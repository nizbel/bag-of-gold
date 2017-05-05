# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoAcaoFormSet
from bagogold.bagogold.forms.operacao_acao import OperacaoAcaoForm, \
    UsoProventosOperacaoAcaoForm
from bagogold.bagogold.forms.provento_acao import ProventoAcaoForm
from bagogold.bagogold.forms.taxa_custodia_acao import TaxaCustodiaAcaoForm
from bagogold.bagogold.models.acoes import OperacaoAcao, HistoricoAcao, \
    ValorDiarioAcao, Provento, UsoProventosOperacaoAcao, TaxaCustodiaAcao, Acao, \
    AcaoProvento
from bagogold.bagogold.models.divisoes import DivisaoOperacaoAcao, Divisao
from bagogold.bagogold.utils.acoes import calcular_provento_por_mes, \
    calcular_media_proventos_6_meses, calcular_operacoes_sem_proventos_por_mes, \
    calcular_uso_proventos_por_mes, quantidade_acoes_ate_dia, \
    calcular_poupanca_prov_acao_ate_dia
from bagogold.bagogold.utils.divisoes import calcular_saldo_geral_acoes_bh
from bagogold.bagogold.utils.investidores import is_superuser, \
    buscar_acoes_investidor_na_data
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from itertools import chain
from operator import attrgetter
import calendar
import datetime
import json

@login_required
def calcular_poupanca_proventos_na_data(request):
    investidor = request.user.investidor
    data = datetime.datetime.strptime(request.GET['dataEscolhida'], '%d/%m/%Y').date()
    poupanca_proventos = str(calcular_poupanca_prov_acao_ate_dia(investidor, data))
    return HttpResponse(json.dumps(poupanca_proventos), content_type = "application/json") 

@login_required
@adiciona_titulo_descricao('Editar operação em Ações (Buy and Hold)', 'Altera valores de operação de compra/venda em Ações para Buy and Hold')
def editar_operacao_acao(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_acao = get_object_or_404(OperacaoAcao, pk=operacao_id, destinacao='B')
    
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if operacao_acao.investidor != investidor:
        raise PermissionDenied
    
    # Valor da poupança de proventos na data apontada
    poupanca_proventos = calcular_poupanca_prov_acao_ate_dia(investidor, operacao_acao.data)
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoAcao, DivisaoOperacaoAcao, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoAcaoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1

    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_acao = OperacaoAcaoForm(request.POST, instance=operacao_acao)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_acao, investidor=investidor) if varias_divisoes else None
            
            if not varias_divisoes:
                try:
                    form_uso_proventos = UsoProventosOperacaoAcaoForm(request.POST, instance=UsoProventosOperacaoAcao.objects.get(divisao_operacao__operacao=operacao_acao))
                except UsoProventosOperacaoAcao.DoesNotExist:
                    form_uso_proventos = UsoProventosOperacaoAcaoForm(request.POST)
            else:
                form_uso_proventos = UsoProventosOperacaoAcaoForm()    
                
            if form_operacao_acao.is_valid():
                # Validar de acordo com a quantidade de divisões
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_acao.save()
                        formset_divisao.save()
                        for form_divisao_operacao in [form for form in formset_divisao if form.cleaned_data]:
                            # Ignorar caso seja apagado
                            if 'DELETE' in form_divisao_operacao.cleaned_data and form_divisao_operacao.cleaned_data['DELETE']:
                                pass
                            else:
                                divisao_operacao = form_divisao_operacao.save(commit=False)
                                if hasattr(divisao_operacao, 'usoproventosoperacaoacao'):
                                    if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] == None or form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] == 0:
                                        divisao_operacao.usoproventosoperacaoacao.delete()
                                    else:
                                        divisao_operacao.usoproventosoperacaoacao.qtd_utilizada = form_divisao_operacao.cleaned_data['qtd_proventos_utilizada']
                                        divisao_operacao.usoproventosoperacaoacao.save()
                                else:
                                    if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] != None and form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] > 0:
                                        # TODO remover operação de uso proventos
                                        divisao_operacao.usoproventosoperacaoacao = UsoProventosOperacaoAcao(qtd_utilizada=form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'], operacao=operacao_acao)
                                        divisao_operacao.usoproventosoperacaoacao.save()
                        
                        messages.success(request, 'Operação alterada com sucesso')
                        return HttpResponseRedirect(reverse('acoes:historico_bh'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                        
                else:
                    if form_uso_proventos.is_valid():
                        operacao_acao.save()
                        divisao_operacao = DivisaoOperacaoAcao.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_acao, quantidade=operacao_acao.quantidade)
                        divisao_operacao.save()
                        uso_proventos = form_uso_proventos.save(commit=False)
#                         print uso_proventos.qtd_utilizada 
                        if uso_proventos.qtd_utilizada > 0:
                            uso_proventos.operacao = operacao_acao
                            uso_proventos.divisao_operacao = DivisaoOperacaoAcao.objects.get(operacao=operacao_acao)
                            uso_proventos.save()
                        # Se uso proventos for 0 e existir uso proventos atualmente, apagá-lo
                        elif uso_proventos.qtd_utilizada == 0 and UsoProventosOperacaoAcao.objects.filter(divisao_operacao__operacao=operacao_acao):
                            uso_proventos.delete()
                        messages.success(request, 'Operação alterada com sucesso')
                        return HttpResponseRedirect(reverse('acoes:historico_bh'))
            
            for erro in [erro for erro in form_operacao_acao.non_field_errors()]:
                messages.error(request, erro)

        elif request.POST.get("delete"):
            divisao_acao = DivisaoOperacaoAcao.objects.filter(operacao=operacao_acao)
            for divisao in divisao_acao:
                if hasattr(divisao, 'usoproventosoperacaoacao'):
                    divisao.usoproventosoperacaoacao.delete()
                divisao.delete()
            operacao_acao.delete()
            messages.success(request, 'Operação apagada com sucesso')
            return HttpResponseRedirect(reverse('acoes:historico_bh'))

    else:
        form_operacao_acao = OperacaoAcaoForm(instance=operacao_acao)
        if not varias_divisoes:
            if UsoProventosOperacaoAcao.objects.filter(divisao_operacao__operacao=operacao_acao).exists():
                form_uso_proventos = UsoProventosOperacaoAcaoForm(instance=UsoProventosOperacaoAcao.objects.get(divisao_operacao__operacao=operacao_acao))
            else:
                form_uso_proventos = UsoProventosOperacaoAcaoForm()
        else:
            form_uso_proventos = UsoProventosOperacaoAcaoForm()
        formset_divisao = DivisaoFormSet(instance=operacao_acao, investidor=investidor)
            
    return TemplateResponse(request, 'acoes/buyandhold/editar_operacao_acao.html', {'form_operacao_acao': form_operacao_acao, 'form_uso_proventos': form_uso_proventos,
                                                                       'formset_divisao': formset_divisao, 'poupanca_proventos': poupanca_proventos, 'varias_divisoes': varias_divisoes})

@login_required
@user_passes_test(is_superuser)
def editar_provento_acao(request, id):
    provento = Provento.objects.get(pk=id)
    if request.method == 'POST':
        if request.POST.get("save"):
            form = ProventoAcaoForm(request.POST, instance=provento)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('acoes:historico_bh'))
        elif request.POST.get("delete"):
            provento.delete()
            return HttpResponseRedirect(reverse('acoes:historico_bh'))

    else:
        form = ProventoAcaoForm(instance=provento)
            
    return TemplateResponse(request, 'acoes/buyandhold/editar_provento_acao.html', {'form': form})  

@login_required
@adiciona_titulo_descricao('Estatísticas da ação', 'Mostra estatísticas e valores históricos de uma ação')
def estatisticas_acao(request, ticker=None):
    investidor = request.user.investidor
    if (ticker):
        acao = get_object_or_404(Acao, ticker=ticker)
    else:
        acao = Acao.objects.all()[0]
    
    # Buscar historicos
    historico = HistoricoAcao.objects.filter(acao__ticker=ticker).order_by('data')
    if not historico:
        return TemplateResponse(request, 'acoes/buyandhold/estatisticas_acao.html', {'graf_preco_medio': list(), 'graf_preco_medio_valor_acao': list(),
                               'graf_historico_proventos': list(), 'graf_historico': list()})
        
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
    
    graf_historico = list()
    graf_historico_proventos = list()
    graf_preco_medio = list()
    graf_preco_medio_valor_acao = list()
    
    preco_medio = 0
    total_gasto = 0
    total_proventos = 0
    proventos_acumulado = 0
    qtd_acoes = 0
    
    # Preparar gráfico com os valores históricos da acao
    for item in historico:
        data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
        graf_historico += [[data_formatada, float(item.preco_unitario)]]
    
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
        ultimo_dia_util = item.data
        while not HistoricoAcao.objects.filter(data=ultimo_dia_util, acao=acao):
            ultimo_dia_util -= datetime.timedelta(days=1)
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
    try:
        preco_unitario = ValorDiarioAcao.objects.filter(acao__ticker=acao, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).order_by('-data_hora')[0].preco_unitario
    except:
        preco_unitario = HistoricoAcao.objects.filter(acao__ticker=acao).order_by('-data')[0].preco_unitario
        
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_historico) > 0 and graf_historico[len(graf_historico)-1][0] == data_atual_formatada:
        graf_historico[len(graf_historico)-1][1] = float(preco_unitario)
    else:
        graf_historico += [[data_atual_formatada, float(preco_unitario)]]
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_historico_proventos) > 0 and graf_historico_proventos[len(graf_historico_proventos)-1][0] == data_atual_formatada:
        graf_historico_proventos[len(graf_historico_proventos)-1][1] = float(proventos_acumulado)
    else:
        graf_historico_proventos += [[data_atual_formatada, float(proventos_acumulado)]]
    # Preço médio corrente
    try:
        preco_medio_corrente = float(-float(total_gasto)/qtd_acoes)
    except ZeroDivisionError:
        preco_medio_corrente = float(0)
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_preco_medio) > 0 and graf_preco_medio[len(graf_preco_medio)-1][0] == data_atual_formatada:
        graf_preco_medio[len(graf_preco_medio)-1][1] = preco_medio_corrente
        graf_preco_medio_valor_acao[len(graf_preco_medio_valor_acao)-1][1] = float(preco_unitario)
    else:
        graf_preco_medio += [[data_atual_formatada, preco_medio_corrente]]
        graf_preco_medio_valor_acao += [[data_atual_formatada, float(preco_unitario)]]
    
    return TemplateResponse(request, 'acoes/buyandhold/estatisticas_acao.html', {'graf_preco_medio': graf_preco_medio, 'graf_preco_medio_valor_acao': graf_preco_medio_valor_acao,
                               'graf_historico_proventos': graf_historico_proventos, 'graf_historico': graf_historico})

@login_required
@adiciona_titulo_descricao('Histórico de Ações (Buy and Hold)', 'Histórico de operações de compra/venda em ações para Buy and Hold e proventos recebidos')
def historico(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    investidor = request.user.investidor
    
    operacoes = OperacaoAcao.objects.filter(destinacao='B', investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    if not operacoes:
        return TemplateResponse(request, 'acoes/buyandhold/historico.html', {'operacoes': list(), 'graf_total_gasto': list(), 'graf_patrimonio': list(),
                               'graf_proventos_mes': list(), 'graf_media_proventos_6_meses': list(), 'graf_poupanca_proventos': list(),
                               'graf_gasto_op_sem_prov_mes': list(), 'graf_uso_proventos_mes': list(),
                                'graf_dividendos_mensal': list(), 'graf_jscp_mensal': list(), 'dados': {}})
    
    acoes = list(set(operacoes.values_list('acao', flat=True)))

    proventos = Provento.objects.filter(acao__in=acoes).exclude(data_ex__isnull=True).exclude(data_ex__gt=datetime.date.today()).order_by('data_ex')
    for acao_id in operacoes.values_list('acao', flat=True):
        proventos = proventos.filter((Q(acao__id=acao_id) & Q(data_ex__gt=operacoes.filter(acao__id=acao_id)[0].data)) | ~Q(acao__id=acao_id))
    for provento in proventos:
        provento.data = provento.data_ex
        provento.emolumentos = 0
        provento.corretagem = 0
     
    taxas_custodia = TaxaCustodiaAcao.objects.filter(investidor=investidor).order_by('ano_vigencia', 'mes_vigencia')
#     for taxa in taxas_custodia:
#         taxa.data = datetime.date(taxa.ano_vigencia, taxa.mes_vigencia, 1)
    
    # Na lista conjunta proventos devem vir antes (data EX antes de operações do dia)
    lista_conjunta = sorted(chain(proventos, operacoes),
                            key=attrgetter('data'))
    
    # Adicionar dias de pagamento de taxa de custodia
    datas_custodia = set()
    
    ano_inicial = lista_conjunta[0].data.year
    mes_inicial = lista_conjunta[0].data.month
    
    # Se houver registro de taxas de custódia, adicionar ao histórico
    if taxas_custodia:
        # Adicionar datas finais de cada ano
        for ano in range(ano_inicial, datetime.date.today().year+1):
            for mes_inicial in range(mes_inicial, 13):
                # Verificar se há nova taxa de custodia vigente
                taxa_custodia_atual = taxas_custodia.filter(Q(ano_vigencia__lt=ano) | Q(ano_vigencia=ano, mes_vigencia__lte=mes_inicial) ).order_by('-ano_vigencia', '-mes_vigencia')[0]
                
                data_custodia = Object()
                data_custodia.data = datetime.date(ano, mes_inicial, 1)
                data_custodia.valor = taxa_custodia_atual.valor_mensal
                data_custodia.acao = operacoes[0].acao
                datas_custodia.add(data_custodia)
                
                # Parar caso esteja no ano atual
                if ano == datetime.date.today().year:
                    if mes_inicial == datetime.date.today().month:
                        break
            mes_inicial = 1
        
    lista_conjunta = sorted(chain(lista_conjunta, datas_custodia),
                            key=attrgetter('data'))
    
    # Dados para os gráficos
    graf_proventos_mes = list()
    graf_media_proventos_6_meses = list()
    graf_uso_proventos_mes = list()
    graf_gasto_op_sem_prov_mes = list()
    graf_total_gasto = list()
    graf_patrimonio = list()
    graf_poupanca_proventos = list()
    graf_dividendos_mensal = list()
    graf_jscp_mensal = list()
    
    # Totais
    total_custodia = 0
    total_gasto = 0
    total_proventos = 0
    proventos_gastos = 0
    patrimonio = 0
    
    # Guarda as ações correntes para o calculo do patrimonio
    acoes = {}
    # Preparar gráfico de proventos em dinheiro por mês
#     graf_proventos_mes = calcular_provento_por_mes(proventos.exclude(data_ex__gt=datetime.date.today()).exclude(tipo_provento='A'), operacoes)
    proventos_mes = calcular_provento_por_mes(investidor, proventos.exclude(data_ex__gt=datetime.date.today()).exclude(tipo_provento='A'), operacoes)
    for x in proventos_mes:
        graf_proventos_mes += [[x[0], x[1] + x[2]]]
        graf_dividendos_mensal += [[x[0], x[1]]]
        graf_jscp_mensal += [[x[0], x[2]]]
    
    graf_media_proventos_6_meses = calcular_media_proventos_6_meses(investidor, proventos.exclude(data_ex__gt=datetime.date.today()).exclude(tipo_provento='A'), operacoes)
    
    # Preparar gráfico de utilização de proventos por mês
    graf_gasto_op_sem_prov_mes = calcular_operacoes_sem_proventos_por_mes(investidor, operacoes.filter(tipo_operacao='C'))
    graf_uso_proventos_mes = calcular_uso_proventos_por_mes(investidor)
    
    # Calculos de patrimonio e gasto total
    for item_lista in lista_conjunta:      
        if item_lista.acao.ticker not in acoes.keys():
            acoes[item_lista.acao.ticker] = 0
        # Verifica se é uma compra/venda
        if isinstance(item_lista, OperacaoAcao):   
            # Verificar se se trata de compra ou venda
            if item_lista.tipo_operacao == 'C':
                item_lista.tipo = 'Compra'
                item_lista.total_gasto = -1 * (item_lista.quantidade * item_lista.preco_unitario + \
                item_lista.emolumentos + item_lista.corretagem)
                if item_lista.utilizou_proventos():
                    qtd_utilizada = item_lista.qtd_proventos_utilizada()
                    proventos_gastos += qtd_utilizada
                    # Remover proventos gastos do total gasto
                    item_lista.total_gasto += qtd_utilizada
                total_gasto += item_lista.total_gasto
                acoes[item_lista.acao.ticker] += item_lista.quantidade
                
            elif item_lista.tipo_operacao == 'V':
                item_lista.tipo = 'Venda'
                item_lista.total_gasto = (item_lista.quantidade * item_lista.preco_unitario - \
                item_lista.emolumentos - item_lista.corretagem)
#                     total_proventos += item_lista.total_gasto
                total_gasto += item_lista.total_gasto
                acoes[item_lista.acao.ticker] -= item_lista.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item_lista, Provento):
            if item_lista.data_pagamento <= datetime.date.today():
                if item_lista.tipo_provento in ['D', 'J']:
                    total_recebido = acoes[item_lista.acao.ticker] * item_lista.valor_unitario
                    if item_lista.tipo_provento == 'J':
                        item_lista.tipo = 'JSCP'
                        total_recebido = total_recebido * Decimal(0.85)
                    else:
                        item_lista.tipo = 'Dividendos'
#                         total_gasto += total_recebido
                    total_proventos += total_recebido
                    item_lista.total_gasto = total_recebido
                    item_lista.quantidade = acoes[item_lista.acao.ticker]
                    item_lista.preco_unitario = item_lista.valor_unitario
                    
                elif item_lista.tipo_provento == 'A':
#                         print '%s %s' % (type(item_lista.tipo_provento), type(u'A'))
                    item_lista.tipo = 'Ações'
#                         print item_lista.acaoprovento_set.all()[0]
                    provento_acao = item_lista.acaoprovento_set.all()[0]
                    if provento_acao.acao_recebida.ticker not in acoes.keys():
                        acoes[provento_acao.acao_recebida.ticker] = 0
                    acoes_recebidas = int((acoes[item_lista.acao.ticker] * item_lista.valor_unitario ) / 100 )
                    item_lista.total_gasto = acoes_recebidas
                    acoes[provento_acao.acao_recebida.ticker] += acoes_recebidas
                    if provento_acao.valor_calculo_frac > 0:
                        if provento_acao.data_pagamento_frac <= datetime.date.today():
#                                 print u'recebido fracionado %s, %s ações de %s a %s' % (total_recebido, acoes[item_lista.acao.ticker], item_lista.acao.ticker, item_lista.valor_unitario)
#                                 total_gasto += (((acoes[item_lista.acao.ticker] * item_lista.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
                            total_proventos += (((acoes[item_lista.acao.ticker] * item_lista.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
                            
        # Verifica se é pagamento de custódia
        elif isinstance(item_lista, Object):
            if taxas_custodia:
                total_gasto -= item_lista.valor
                total_custodia += item_lista.valor
                
        patrimonio = 0
        
        # Rodar calculo de patrimonio
        for acao in acoes.keys():
            # Pegar último dia util com negociação da ação para calculo do patrimonio
            ultimo_dia_util = item_lista.data
            while not HistoricoAcao.objects.filter(data=ultimo_dia_util, acao__ticker=acao):
                ultimo_dia_util -= datetime.timedelta(days=1)
        
            valor_acao = HistoricoAcao.objects.get(acao__ticker=acao, data=ultimo_dia_util).preco_unitario
            patrimonio += (valor_acao * acoes[acao])
        
        data_formatada = str(calendar.timegm(item_lista.data.timetuple()) * 1000)
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_total_gasto) > 0 and graf_total_gasto[-1][0] == data_formatada:
            graf_total_gasto[len(graf_total_gasto)-1][1] = float(-total_gasto)
        else:
            graf_total_gasto += [[data_formatada, float(-total_gasto)]]
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
            graf_patrimonio[len(graf_patrimonio)-1][1] = float(patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(patrimonio)]]
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_poupanca_proventos) > 0 and graf_poupanca_proventos[-1][0] == data_formatada:
            graf_poupanca_proventos[len(graf_poupanca_proventos)-1][1] = float(total_proventos - proventos_gastos)
        else:
            graf_poupanca_proventos += [[data_formatada, float(total_proventos - proventos_gastos)]]
                
    # Adicionar dia mais atual
    patrimonio = 0
    for acao in acoes.keys():
        if acoes[acao] > 0:
#             print '%s %s' % (acao, acoes[acao])
            valor_diario_mais_recente = ValorDiarioAcao.objects.filter(acao__ticker=acao).order_by('-data_hora')
            historico_mais_recente = HistoricoAcao.objects.filter(acao__ticker=acao).order_by('-data')
            data_formatada = ''
            if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() >= historico_mais_recente[0].data:
                patrimonio += (valor_diario_mais_recente[0].preco_unitario * acoes[acao])
            else:
                patrimonio += (historico_mais_recente[0].preco_unitario * acoes[acao])
    data_formatada = str(calendar.timegm(datetime.date.today().timetuple()) * 1000)
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if not(len(graf_total_gasto) > 0 and graf_total_gasto[-1][0] == data_formatada):
        graf_total_gasto += [[data_formatada, float(-total_gasto)]]
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if not(len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada):
        graf_patrimonio += [[data_formatada, float(patrimonio)]]
            
#     print proventos_gastos
    # Popular dados
    dados = {}
    dados['acoes'] = acoes
    dados['total_proventos'] = total_proventos
    dados['poupanca_proventos'] = total_proventos - proventos_gastos
    dados['total_gasto'] = -total_gasto
    dados['total_custodia'] = total_custodia
    dados['patrimonio'] = patrimonio
    dados['lucro'] = patrimonio + total_gasto
    dados['lucro_percentual'] = (patrimonio + total_gasto) / -total_gasto * 100
    dados['dividendos_mensal'] = graf_dividendos_mensal[-1][1]
    dados['jscp_mensal'] = graf_jscp_mensal[-1][1]
    dados['saldo_geral'] = calcular_saldo_geral_acoes_bh()
    
    # Remover taxas de custódia da lista conjunta de operações e proventos
    lista_conjunta = [value for value in lista_conjunta if not isinstance(value, Object)]

    return TemplateResponse(request, 'acoes/buyandhold/historico.html', {'operacoes': lista_conjunta, 'graf_total_gasto': graf_total_gasto, 'graf_patrimonio': graf_patrimonio,
                               'graf_proventos_mes': graf_proventos_mes, 'graf_media_proventos_6_meses': graf_media_proventos_6_meses, 'graf_poupanca_proventos': graf_poupanca_proventos,
                               'graf_gasto_op_sem_prov_mes': graf_gasto_op_sem_prov_mes, 'graf_uso_proventos_mes': graf_uso_proventos_mes,
                                'graf_dividendos_mensal': graf_dividendos_mensal, 'graf_jscp_mensal': graf_jscp_mensal, 'dados': dados})
    
@login_required
@adiciona_titulo_descricao('Inserir operação em Ações (Buy and Hold)', 'Insere um registro de operação de compra/venda em Ações para Buy and Hold')
def inserir_operacao_acao(request):
    investidor = request.user.investidor
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoAcao, DivisaoOperacaoAcao, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoAcaoFormSet)
    
    if request.method == 'POST':
        form_operacao_acao = OperacaoAcaoForm(request.POST)
        form_uso_proventos = UsoProventosOperacaoAcaoForm(request.POST) if not varias_divisoes else None
        formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        if form_operacao_acao.is_valid():
            operacao_acao = form_operacao_acao.save(commit=False)
            operacao_acao.investidor = investidor
            operacao_acao.destinacao = 'B'
            try:
                with transaction.atomic():
                    # Validar de acordo com a quantidade de divisões
                    if varias_divisoes:
                        formset_divisao = DivisaoFormSet(request.POST, instance=operacao_acao, investidor=investidor)
                        if formset_divisao.is_valid():
                            operacao_acao.save()
                            formset_divisao.save()
                            for form_divisao_operacao in [form for form in formset_divisao if form.cleaned_data]:
                                divisao_operacao = form_divisao_operacao.save(commit=False)
                                if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] != None and form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] > 0:
                                    # TODO remover operação de uso proventos
                                    divisao_operacao.usoproventosoperacaoacao = UsoProventosOperacaoAcao(qtd_utilizada=form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'], operacao=operacao_acao)
                                    divisao_operacao.usoproventosoperacaoacao.save()
                                
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('acoes:historico_bh'))
                        for erro in formset_divisao.non_form_errors():
                            messages.error(request, erro)
                        
                    else:
                        if form_uso_proventos.is_valid():
                            operacao_acao.save()
                            divisao_operacao = DivisaoOperacaoAcao(operacao=operacao_acao, quantidade=operacao_acao.quantidade, divisao=investidor.divisaoprincipal.divisao)
                            divisao_operacao.save()
                            uso_proventos = form_uso_proventos.save(commit=False)
                            if uso_proventos.qtd_utilizada > 0:
                                uso_proventos.operacao = operacao_acao
                                uso_proventos.divisao_operacao = divisao_operacao
                                uso_proventos.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('acoes:historico_bh'))
            except:
                pass
        
        for erro in [erro for erro in form_operacao_acao.non_field_errors()]:
            messages.error(request, erro)
    else:
        valores_iniciais = {}
        if investidor.tipo_corretagem == 'F':
            valores_iniciais['corretagem'] = investidor.corretagem_padrao
        form_operacao_acao = OperacaoAcaoForm(initial=valores_iniciais)
        form_uso_proventos = UsoProventosOperacaoAcaoForm(initial={'qtd_utilizada': Decimal('0.00')})
        formset_divisao = DivisaoFormSet(investidor=investidor)
        
    return TemplateResponse(request, 'acoes/buyandhold/inserir_operacao_acao.html', {'form_operacao_acao': form_operacao_acao, 'form_uso_proventos': form_uso_proventos,
                                                                       'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})
    
@login_required
@user_passes_test(is_superuser)
def inserir_provento_acao(request):
    if request.method == 'POST':
        form = ProventoAcaoForm(request.POST)
        if form.is_valid():
            operacao_acao = form.save()
            return HttpResponseRedirect(reverse('acoes:historico_bh'))
    else:
        form = ProventoAcaoForm()
            
    return TemplateResponse(request, 'acoes/buyandhold/inserir_provento_acao.html', {'form': form, })
    
@login_required
@adiciona_titulo_descricao('Inserir taxa de custódia para Ações', 'Insere um registro no histórico de valores de taxa de custódia para o investidor')
def inserir_taxa_custodia_acao(request):
    investidor = request.user.investidor
    
    if request.method == 'POST':
        form = TaxaCustodiaAcaoForm(request.POST)
        if form.is_valid():
            taxa_custodia = form.save(commit=False)
            taxa_custodia.investidor = investidor
            taxa_custodia.save()
            return HttpResponseRedirect(reverse('acoes:ver_taxas_custodia_acao'))
    else:
        form = TaxaCustodiaAcaoForm()
            
    return TemplateResponse(request, 'acoes/buyandhold/inserir_taxa_custodia_acao.html', {'form': form, })
    
@login_required
@adiciona_titulo_descricao('Painel de Ações (Buy and Hold)', 'Posição atual do investidor em Ações para Buy and Hold')
def painel(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    investidor = request.user.investidor
    
    acoes_investidor = buscar_acoes_investidor_na_data(investidor, destinacao='B')
    
    # Guarda as ações correntes para o calculo do patrimonio
    acoes = {}
    # Cálculo de quantidade
    for acao in Acao.objects.filter(id__in=acoes_investidor):
        acoes[acao.ticker] = Object()
        acoes[acao.ticker].quantidade = quantidade_acoes_ate_dia(investidor, acao.ticker, datetime.date.today())
        if acoes[acao.ticker].quantidade == 0:
            del acoes[acao.ticker]
        else:
            ultimo_dia_util = (datetime.date.today() + datetime.timedelta(days=-1))
            while not HistoricoAcao.objects.filter(data=ultimo_dia_util, acao=acao):
                ultimo_dia_util -= datetime.timedelta(days=1)
            acoes[acao.ticker].valor_dia_anterior = HistoricoAcao.objects.get(acao=acao, data=ultimo_dia_util).preco_unitario
                     
    # Pegar totais de ações  
    total_acoes = 0      
    total_valor = 0
    total_variacao = 0
    total_variacao_percentual = 0
    
    # Preencher totais   
    for acao in acoes.keys():
        total_acoes += acoes[acao].quantidade
        try:
            acoes[acao].valor = ValorDiarioAcao.objects.filter(acao__ticker=acao, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).order_by('-data_hora')[0].preco_unitario
        except:
            acoes[acao].valor = HistoricoAcao.objects.filter(acao__ticker=acao).order_by('-data')[0].preco_unitario
        acoes[acao].variacao = acoes[acao].valor - acoes[acao].valor_dia_anterior
        acoes[acao].variacao_total = acoes[acao].variacao * acoes[acao].quantidade
        acoes[acao].valor_total = acoes[acao].valor * acoes[acao].quantidade
        total_valor += acoes[acao].valor_total
        total_variacao += acoes[acao].variacao * acoes[acao].quantidade
    
    # Calcular percentagens
    for acao in acoes.keys():
        acoes[acao].quantidade_percentual = float(acoes[acao].quantidade) / total_acoes * 100
        acoes[acao].valor_total_percentual = acoes[acao].valor_total / total_valor * 100
        acoes[acao].variacao_percentual = float(acoes[acao].variacao) / float(acoes[acao].valor_dia_anterior) * 100
        total_variacao_percentual += acoes[acao].valor_dia_anterior * acoes[acao].quantidade
    
    # Calcular percentual do total de variação
    if total_variacao_percentual > 0:
        total_variacao_percentual = total_variacao / total_variacao_percentual * Decimal(100)
    
    # Adicionar dados sobre última atualização
    # Histórico
    historico_mais_recente = HistoricoAcao.objects.latest('data').data
    # Valor diário
    try:
        valor_diario_mais_recente = ValorDiarioAcao.objects.latest('data_hora').data_hora
    except:
        valor_diario_mais_recente = 'N/A'
    
    # Popular dados
    dados = {}
    dados['total_acoes'] = total_acoes
    dados['total_valor'] = total_valor
    dados['total_variacao'] = total_variacao
    dados['total_variacao_percentual'] = total_variacao_percentual
    dados['historico_mais_recente'] = historico_mais_recente
    dados['valor_diario_mais_recente'] = valor_diario_mais_recente

    return TemplateResponse(request, 'acoes/buyandhold/painel.html', {'acoes': acoes, 'dados': dados})
    
@login_required
def remover_taxa_custodia_acao(request, taxa_id):
    investidor = request.user.investidor
    taxa = get_object_or_404(TaxaCustodiaAcao, pk=taxa_id)
    
    # Verifica se a taxa é do investidor, senão, jogar erro de permissão
    if taxa.investidor != investidor:
        raise PermissionDenied
    
    try:
        taxa.delete()
        messages.success(request, 'Taxa de custódia excluída com sucesso')
    except Exception as e:
        messages.error(request, e)
    
    return HttpResponseRedirect(reverse('acoes:ver_taxas_custodia_acao'))

@login_required
@adiciona_titulo_descricao('Listar taxas de custódia de ações', 'Lista o histórico de valores de taxas de custódia cadastrados pelo investidor')
def ver_taxas_custodia_acao(request):
    investidor = request.user.investidor
    taxas_custodia = TaxaCustodiaAcao.objects.filter(investidor=investidor).order_by('ano_vigencia', 'mes_vigencia')
    for taxa in taxas_custodia:
        taxa.ano_vigencia = str(taxa.ano_vigencia).replace('.', '')
    return TemplateResponse(request, 'acoes/buyandhold/ver_taxas_custodia_acao.html', {'taxas_custodia': taxas_custodia})