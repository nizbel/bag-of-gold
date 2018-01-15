# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.models.acoes import Acao, ValorDiarioAcao, HistoricoAcao, \
    Provento, OperacaoAcao, AcaoProvento
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorValidacaoDocumento, ProventoAcaoDocumento
from bagogold.bagogold.utils.acoes import quantidade_acoes_ate_dia, \
    calcular_poupanca_prov_acao_ate_dia
from bagogold.bagogold.utils.investidores import buscar_acoes_investidor_na_data, \
    buscar_proventos_a_receber
from decimal import Decimal, ROUND_FLOOR
from django.db.models.expressions import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from itertools import chain
from operator import attrgetter
import calendar
import datetime
import json
import math
import re

@adiciona_titulo_descricao('Detalhar provento', 'Detalhamento de proventos em ações')
def detalhar_provento(request, provento_id):
    provento = get_object_or_404(Provento, pk=provento_id)
    
    documentos = ProventoAcaoDocumento.objects.filter(provento=provento).order_by('-versao')
    
    # Se usuário autenticado, mostrar dados do recebimento do provento
    if request.user.is_authenticated():
        provento.pago = datetime.date.today() > provento.data_pagamento
        provento.qtd_na_data_ex = quantidade_acoes_ate_dia(request.user.investidor, provento.acao.ticker, provento.data_ex, False)
        if provento.tipo_provento != 'A':
            provento.valor_recebido = (provento.qtd_na_data_ex * provento.valor_unitario).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
        else:
            provento.valor_recebido = int(math.floor(provento.qtd_na_data_ex * provento.valor_unitario / 100))
    
    # Preencher última versão
    provento.ultima_versao = documentos[0].versao
    
    return TemplateResponse(request, 'acoes/detalhar_provento.html', {'provento': provento, 'documentos': documentos})

@adiciona_titulo_descricao('Estatísticas da ação', 'Mostra estatísticas e valores históricos de uma ação')
def estatisticas_acao(request, ticker=None):
    if request.user.is_authenticated():
        investidor = request.user.investidor
        
    if ticker:
        acao = get_object_or_404(Acao, ticker=ticker)
    else:
        acao = Acao.objects.all()[0]
    
    # Buscar historicos
    historico = HistoricoAcao.objects.filter(acao__ticker=ticker, oficial_bovespa=True).order_by('data')
    if not historico:
        return TemplateResponse(request, 'acoes/estatisticas_acao.html', {'graf_preco_medio': list(), 'graf_preco_medio_valor_acao': list(),
                               'graf_historico_proventos': list(), 'graf_historico': list(), 'dados': {}})
        
    graf_historico = list()
    # Preparar gráfico com os valores históricos da acao
    for item in historico:
        data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
        graf_historico += [[data_formatada, float(item.preco_unitario)]]
    
    if not request.user.is_authenticated():
        return TemplateResponse(request, 'acoes/estatisticas_acao.html', {'graf_preco_medio': list(), 'graf_preco_medio_valor_acao': list(),
                               'graf_historico_proventos': list(), 'graf_historico': graf_historico, 'dados': {}})
        
    operacoes = OperacaoAcao.objects.filter(destinacao='B', acao__ticker=ticker, investidor=investidor).exclude(data__isnull=True).order_by('data')
    # Pega os proventos em ações recebidos por outras ações
    proventos_em_acoes = AcaoProvento.objects.filter(acao_recebida__ticker=ticker).exclude(provento__acao__ticker=ticker).order_by('provento__data_ex')
    
    # Verifica se houve operação
    # TODO testar data mais antiga para ver se é operação ou provento em ação de outra ação
    data_mais_antiga = datetime.date.today()
    if operacoes:
        data_mais_antiga = min(data_mais_antiga, operacoes[0].data)
    if proventos_em_acoes:
        data_mais_antiga = min(data_mais_antiga, proventos_em_acoes[0].data)
    proventos = Provento.objects.filter(acao__ticker=ticker).exclude(data_ex__isnull=True).filter(data_ex__range=[data_mais_antiga, datetime.date.today()]).order_by('data_ex')
    for provento in proventos:
        provento.data = provento.data_ex
    
    proventos = list(proventos)
    # Adicionar os proventos em ações provenientes de outras ações
    for provento_em_acoes in proventos_em_acoes:
        provento = provento_em_acoes.provento
        provento.data = provento.data_ex
        proventos.append(provento)
        
    # Proventos devem vir antes
    lista_conjunta = sorted(chain(proventos, operacoes), key=attrgetter('data'))
    
    # Dados da tela
    dados = {}
    
    graf_historico_proventos = list()
    graf_preco_medio = list()
    graf_preco_medio_valor_acao = list()
    
    preco_medio = 0
    total_gasto = 0
    total_proventos = 0
    proventos_acumulado = 0
    qtd_acoes = 0
    
    for item in lista_conjunta:
#         print item
        if isinstance(item, OperacaoAcao):   
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                item.total_gasto = -1 * (item.quantidade * item.preco_unitario + \
                item.emolumentos + item.corretagem)
                total_gasto += item.total_gasto
                qtd_acoes += item.quantidade
                
            elif item.tipo_operacao == 'V':
                item.total_gasto = (item.quantidade * item.preco_unitario - \
                item.emolumentos - item.corretagem)
                total_proventos += item.total_gasto
                total_gasto += item.total_gasto
                qtd_acoes -= item.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item, Provento):
            if item.data_pagamento <= datetime.date.today():
                if item.tipo_provento in ['D', 'J']:
                    total_recebido = qtd_acoes * item.valor_unitario
                    if item.tipo_provento == 'J':
                        total_recebido = total_recebido * Decimal(0.85)
                    total_gasto += total_recebido
                    total_proventos += total_recebido
                    proventos_acumulado += item.valor_unitario
                elif item.tipo_provento == 'A':
                    provento_acao = item.acaoprovento_set.all()[0]
                    if provento_acao.acao_recebida.ticker == ticker:
                        acoes_recebidas = int((quantidade_acoes_ate_dia(investidor, item.acao.ticker, item.data) * item.valor_unitario ) / 100 )
                        qtd_acoes += acoes_recebidas
                    if item.acao.ticker == ticker:
                        if provento_acao.valor_calculo_frac > 0:
                            if provento_acao.data_pagamento_frac <= datetime.date.today():
    #                                 print u'recebido fracionado %s, %s ações de %s a %s' % (total_recebido, acoes[item.acao.ticker], item.acao.ticker, item.valor_unitario)
                                total_gasto += (((qtd_acoes * item.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
                                total_proventos += (((qtd_acoes * item.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
                
                # Preencher gráfico do histórico
                data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
                # Verifica se altera ultima posicao do grafico ou adiciona novo registro
                if len(graf_historico_proventos) > 0 and graf_historico_proventos[len(graf_historico_proventos)-1][0] == data_formatada:
                    graf_historico_proventos[len(graf_historico_proventos)-1][1] = float(proventos_acumulado)
                else:
                    graf_historico_proventos += [[data_formatada, float(proventos_acumulado)]]
                    
                                
        data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
        ultimo_dia_util = historico.filter(data__lte=item.data).order_by('-data')[0].data
        # Preço médio corrente
        try:
            preco_medio_corrente = float(-float(total_gasto)/qtd_acoes)
        except ZeroDivisionError:
            preco_medio_corrente = float(0)
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_preco_medio) > 0 and graf_preco_medio[len(graf_preco_medio)-1][0] == data_formatada:
            graf_preco_medio[len(graf_preco_medio)-1][1] = preco_medio_corrente
            graf_preco_medio_valor_acao[len(graf_preco_medio_valor_acao)-1][1] = float(historico.filter(data=ultimo_dia_util)[0].preco_unitario)
        else:
            graf_preco_medio += [[data_formatada, preco_medio_corrente]]
            graf_preco_medio_valor_acao += [[data_formatada, float(historico.filter(data=ultimo_dia_util)[0].preco_unitario)]]
                
    
    # Adicionar data atual
    data_atual_formatada = str(calendar.timegm(datetime.date.today().timetuple()) * 1000)
#     ultimo_dia_util = datetime.date.today()
#     while not HistoricoAcao.objects.filter(data=ultimo_dia_util, acao=acao):
#         ultimo_dia_util -= datetime.timedelta(days=1)
    if ValorDiarioAcao.objects.filter(acao__ticker=acao, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).exists():
        preco_unitario = ValorDiarioAcao.objects.filter(acao__ticker=acao, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).order_by('-data_hora')[0].preco_unitario
        # Preparar data a ser usada nos grafs de histórico/proventos
        data_valida_graf_historico = data_atual_formatada
    else:
        preco_unitario = historico.filter(acao__ticker=acao).order_by('-data')[0].preco_unitario
        # Preparar data a ser usada nos grafs de histórico/proventos
        data_valida_graf_historico = str(calendar.timegm(historico.filter(acao__ticker=acao).order_by('-data')[0].data.timetuple()) * 1000)
        
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_historico) > 0 and graf_historico[len(graf_historico)-1][0] == data_valida_graf_historico:
        graf_historico[len(graf_historico)-1][1] = float(preco_unitario)
    else:
        graf_historico += [[data_valida_graf_historico, float(preco_unitario)]]
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_historico_proventos) > 0 and graf_historico_proventos[len(graf_historico_proventos)-1][0] == data_valida_graf_historico:
        graf_historico_proventos[len(graf_historico_proventos)-1][1] = float(proventos_acumulado)
    else:
        graf_historico_proventos += [[data_valida_graf_historico, float(proventos_acumulado)]]
    # Preço médio corrente
    try:
        preco_medio_corrente = float(-float(total_gasto)/qtd_acoes)
    except ZeroDivisionError:
        preco_medio_corrente = float(0)
    
    # Guarda se gráfico de preço médio será mostrado
    dados['mostrar_grafico_preco_medio'] = len(graf_preco_medio) > 0
    if dados['mostrar_grafico_preco_medio']:
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if graf_preco_medio[len(graf_preco_medio)-1][0] == data_atual_formatada:
            graf_preco_medio[len(graf_preco_medio)-1][1] = preco_medio_corrente
            graf_preco_medio_valor_acao[len(graf_preco_medio_valor_acao)-1][1] = float(preco_unitario)
        else:
            graf_preco_medio += [[data_atual_formatada, preco_medio_corrente]]
            graf_preco_medio_valor_acao += [[data_atual_formatada, float(preco_unitario)]]
        
    
    return TemplateResponse(request, 'acoes/estatisticas_acao.html', {'graf_preco_medio': graf_preco_medio, 'graf_preco_medio_valor_acao': graf_preco_medio_valor_acao,
                               'graf_historico_proventos': graf_historico_proventos, 'graf_historico': graf_historico, 'dados': dados})

@adiciona_titulo_descricao('Lista de ações', 'Lista as ações da Bovespa')
def listar_acoes(request):
    acoes = Acao.objects.all()
    
    return TemplateResponse(request, 'acoes/listar_acoes.html', {'acoes': acoes})

def listar_tickers_acoes(request):
    return HttpResponse(json.dumps(render_to_string('acoes/utils/listar_tickers.html', {'acoes': Acao.objects.all().order_by('ticker')})), content_type = "application/json")  

@adiciona_titulo_descricao('Lista de proventos', 'Lista os proventos de ações cadastrados')
def listar_proventos(request):
    # Montar filtros
    if request.is_ajax():
        filtros = {}
        # Preparar filtro por tipo de investimento
        filtros['tipo_provento'] = request.GET.get('tipo', 'T')
        if filtros['tipo_provento'] == 'T':
            query_proventos = Provento.objects.all()
        else:
            query_proventos = Provento.objects.filter(tipo_provento=filtros['tipo_provento'])
            
        filtros['acoes'] = re.sub('[^,\d]', '', request.GET.get('acoes', ''))
        if filtros['acoes'] != '':
            query_proventos = query_proventos.filter(acao__id__in=filtros['acoes'].split(','))
            
        # Preparar filtros para datas
        # Início data EX
        filtros['inicio_data_ex'] = request.GET.get('inicio_data_ex', '')
        if filtros['inicio_data_ex'] != '':
            try:
                query_proventos = query_proventos.filter(data_ex__gte=datetime.datetime.strptime(filtros['inicio_data_ex'], '%d/%m/%Y'))
            except:
                filtros['inicio_data_ex'] = ''
        # Fim data EX
        filtros['fim_data_ex'] = request.GET.get('fim_data_ex', '')
        if filtros['fim_data_ex'] != '':
            try:
                query_proventos = query_proventos.filter(data_ex__lte=datetime.datetime.strptime(filtros['fim_data_ex'], '%d/%m/%Y'))
            except:
                filtros['fim_data_ex'] = ''
        # Início data pagamento
        filtros['inicio_data_pagamento'] = request.GET.get('inicio_data_pagamento', '')
        if filtros['inicio_data_pagamento'] != '':
            try:
                query_proventos = query_proventos.filter(data_pagamento__gte=datetime.datetime.strptime(filtros['inicio_data_pagamento'], '%d/%m/%Y'))
            except:
                filtros['inicio_data_pagamento'] = ''
        # Fim data pagamento
        filtros['fim_data_pagamento'] = request.GET.get('fim_data_pagamento', '')
        if filtros['fim_data_pagamento'] != '':
            try:
                query_proventos = query_proventos.filter(data_pagamento__lte=datetime.datetime.strptime(filtros['fim_data_pagamento'], '%d/%m/%Y'))
            except:
                filtros['fim_data_pagamento'] = ''
                
        proventos = list(query_proventos)
        return HttpResponse(json.dumps(render_to_string('acoes/utils/lista_proventos.html', {'proventos': proventos})), content_type = "application/json")  
    else:
        filtros = {'tipo_provento': 'T', 'inicio_data_ex': '', 'fim_data_ex': '', 'inicio_data_pagamento': '', 'fim_data_pagamento': '', 'acoes': ''}
        
    # Buscar últimas atualizações
    ultimas_validacoes = InvestidorValidacaoDocumento.objects.filter(documento__tipo='A').order_by('-data_validacao')[:10] \
        .annotate(provento=F('documento__proventoacaodocumento__provento')).values('provento', 'data_validacao')
    ultimas_atualizacoes = Provento.objects.filter(id__in=[validacao['provento'] for validacao in ultimas_validacoes])
    for atualizacao in ultimas_atualizacoes:
        atualizacao.data_insercao = next(validacao['data_validacao'].date() for validacao in ultimas_validacoes if validacao['provento'] == atualizacao.id)
    
    if request.user.is_authenticated():
        proximos_proventos = buscar_proventos_a_receber(request.user.investidor, 'A')
    else:
        proximos_proventos = list()
    
    return TemplateResponse(request, 'acoes/listar_proventos.html', {'filtros': filtros, 'ultimas_atualizacoes': ultimas_atualizacoes, 'proximos_proventos': proximos_proventos})

@adiciona_titulo_descricao('Sobre Ações', 'Detalha o que são Ações')
def sobre(request):
    if request.user.is_authenticated():
        total_atual = 0
        data_atual = datetime.date.today()
        acoes_investidor = buscar_acoes_investidor_na_data(request.user.investidor)
        # Cálculo de quantidade
        for acao in Acao.objects.filter(id__in=acoes_investidor):
            acao_qtd = quantidade_acoes_ate_dia(request.user.investidor, acao.ticker, data_atual, considerar_trade=True)
            if acao_qtd > 0:
                if ValorDiarioAcao.objects.filter(acao__ticker=acao.ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
                    acao_valor = ValorDiarioAcao.objects.filter(acao__ticker=acao.ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_unitario
                else:
                    acao_valor = HistoricoAcao.objects.filter(acao__ticker=acao.ticker).order_by('-data')[0].preco_unitario
                total_atual += (acao_qtd * acao_valor)
        total_atual += calcular_poupanca_prov_acao_ate_dia(request.user.investidor, data_atual)
    else:
        total_atual = 0
    
    return TemplateResponse(request, 'acoes/sobre.html', {'total_atual': total_atual})