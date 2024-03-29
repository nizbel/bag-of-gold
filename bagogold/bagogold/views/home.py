# -*- coding: utf-8 -*-
import calendar
import datetime
from decimal import Decimal, ROUND_DOWN
from itertools import chain
import json
import math
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Count
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When
from django.db.models.fields import DecimalField
from django.http.response import HttpResponse
from django.template import loader
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls.base import reverse

from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.misc import ContatoForm
from bagogold.bagogold.models.acoes import OperacaoAcao, HistoricoAcao, Provento, \
    ValorDiarioAcao
from bagogold.bagogold.models.divisoes import TransferenciaEntreDivisoes, \
    Divisao
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.investidores import buscar_ultimas_operacoes, \
    buscar_totais_atuais_investimentos, buscar_proventos_a_receber, \
    buscar_proventos_a_receber_data_ex_futura, buscar_operacoes_no_periodo
from bagogold.bagogold.utils.misc import calcular_rendimentos_ate_data, \
    verificar_feriado_bovespa, formatar_zeros_a_direita_apos_2_casas_decimais, \
    qtd_dias_uteis_no_periodo
from bagogold.bagogold.utils.taxas_indexacao import \
    calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.blog.models import Post
from bagogold.cdb_rdb.models import OperacaoCDB_RDB, CDB_RDB
from bagogold.cdb_rdb.utils import calcular_valor_atualizado_operacao_ate_dia \
    as calcular_valor_atualizado_operacao_ate_dia_cdb_rdb, \
    buscar_operacoes_vigentes_ate_data as buscar_operacoes_vigentes_ate_data_cdb_rdb, \
    calcular_valor_operacao_cdb_rdb_ate_dia, atualizar_operacoes_cdb_rdb_no_periodo
from bagogold.cri_cra.models.cri_cra import OperacaoCRI_CRA, \
    DataRemuneracaoCRI_CRA, DataAmortizacaoCRI_CRA, CRI_CRA
from bagogold.cri_cra.utils.utils import calcular_valor_cri_cra_ate_dia, \
    calcular_rendimentos_cri_cra_ate_data
from bagogold.cri_cra.utils.valorizacao import calcular_valor_um_cri_cra_na_data
from bagogold.criptomoeda.models import OperacaoCriptomoeda, \
    TransferenciaCriptomoeda, ValorDiarioCriptomoeda
from bagogold.debentures.models import OperacaoDebenture, \
    HistoricoValorDebenture
from bagogold.debentures.utils import calcular_valor_debentures_ate_dia,\
    simular_valor_na_data
from bagogold.fii.models import OperacaoFII, HistoricoFII, ProventoFII, \
    ValorDiarioFII
from bagogold.fundo_investimento.models import OperacaoFundoInvestimento, \
    HistoricoValorCotas
from bagogold.lc.models import OperacaoLetraCambio, LetraCambio
from bagogold.lc.utils import calcular_valor_lc_ate_dia, calcular_valor_venda_lc, \
    calcular_valor_atualizado_operacao_ate_dia as calcular_valor_atualizado_operacao_ate_dia_lc, \
    buscar_operacoes_vigentes_ate_data as buscar_operacoes_vigentes_ate_data_lc, \
    calcular_valor_operacao_lc_ate_dia
from bagogold.lci_lca.models import OperacaoLetraCredito, LetraCredito
from bagogold.lci_lca.utils import calcular_valor_operacao_lci_lca_ate_dia, \
    buscar_operacoes_vigentes_ate_data as buscar_operacoes_vigentes_ate_data_lci_lca, \
    atualizar_operacoes_lci_lca_no_periodo
from bagogold.outros_investimentos.models import Rendimento, Amortizacao, \
    Investimento
from bagogold.tesouro_direto.models import OperacaoTitulo, HistoricoTitulo, \
    ValorDiarioTitulo, Titulo
from bagogold.tesouro_direto.utils import calcular_valor_td_ate_dia
from django.shortcuts import resolve_url


@adiciona_titulo_descricao('Cálculos de patrimônio e rendimento futuros', 'Permite calcular o patrimônio acumulado em um período, o rendimento alcançado e o ' \
                                                                          'tempo necessário para obtê-los')
def calcular_renda_futura(request):
    ultima_taxa_di = HistoricoTaxaDI.objects.all().order_by('-data')[0].taxa
    return TemplateResponse(request, 'calcular_renda_futura.html', {'ultima_taxa_di': ultima_taxa_di})

@login_required
@adiciona_titulo_descricao('Calendário de acompanhamento', 'Detalha as operações e recebimentos do investidor mensalmente')
def calendario(request):
    investidor = request.user.investidor
    
    if request.is_ajax():
        # Validar datas
        try:
            data_inicial = datetime.datetime.strptime(request.GET.get('start', ''), '%Y-%m-%d').date()
        except ValueError:
            raise
        try:
            data_final = datetime.datetime.strptime(request.GET.get('end', ''), '%Y-%m-%d').date()
        except ValueError:
            raise
        
        # Buscar eventos
        # Operações do investidor
        operacoes = buscar_operacoes_no_periodo(investidor, data_inicial, data_final)
        for operacao in operacoes:
            operacao.url = operacao.link
#             operacao.url = resolve_url('inicio:painel_geral')
        calendario = [{'title': unicode(operacao), 'start': operacao.data.strftime('%Y-%m-%d'), 'url': operacao.url} for operacao in operacoes]
        
        # Proventos de ações
        # Busca ações que o investidor já tenha negociado
        lista_acoes_negociadas = OperacaoAcao.objects.filter(investidor=investidor).order_by('acao').values_list('acao', flat=True).distinct()
        proventos_acoes = Provento.objects.filter(data_ex__range=[data_inicial, data_final], tipo_provento__in=['D', 'J'], acao__in=lista_acoes_negociadas)
        calendario.extend([{'title': u'Data EX para %s de %s, R$ %s por ação' % (provento.descricao_tipo_provento(), provento.acao.ticker, 
                                                                                 formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario)), 
                            'start': provento.data_ex.strftime('%Y-%m-%d')} for provento in proventos_acoes])
        
        
        proventos_acoes = Provento.objects.filter(data_pagamento__range=[data_inicial, data_final], tipo_provento__in=['D', 'J'], acao__in=lista_acoes_negociadas)
        calendario.extend([{'title': u'Data de pagamento para %s de %s, R$ %s por ação' % (provento.descricao_tipo_provento(), provento.acao.ticker, 
                                                                                           formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario)), 
                            'start': provento.data_pagamento.strftime('%Y-%m-%d')} for provento in proventos_acoes])
        
        # Proventos de FIIs
        # Busca fiis que o investidor já tenha negociado
        lista_fiis_negociadas = OperacaoFII.objects.filter(investidor=investidor).order_by('fii').values_list('fii', flat=True).distinct()
        proventos_fiis = ProventoFII.objects.filter(data_ex__range=[data_inicial, data_final], fii__in=lista_fiis_negociadas)
        calendario.extend([{'title': u'Data EX para %s de %s, R$ %s por cota' % (provento.descricao_tipo_provento(), provento.fii.ticker, 
                                                                                 formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario)), 
                            'start': provento.data_ex.strftime('%Y-%m-%d')} for provento in proventos_fiis])
        
        proventos_fiis = ProventoFII.objects.filter(data_pagamento__range=[data_inicial, data_final], fii__in=lista_fiis_negociadas)
        calendario.extend([{'title': u'Data de pagamento para %s de %s, R$ %s por cota' % (provento.descricao_tipo_provento(), provento.fii.ticker, 
                                                                                           formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario)), 
                            'start': provento.data_pagamento.strftime('%Y-%m-%d')} for provento in proventos_fiis])
        
        # Carência e vencimento de CDB/RDB
        operacoes_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor, data__lt=data_final, tipo_operacao='C')
        # Buscar apenas operações com fim da carência no período especificado
        carencia_cdb_rdb = [operacao for operacao in operacoes_cdb_rdb if operacao.data_carencia() >= data_inicial and operacao.data_carencia() <= data_final]
        calendario.extend([{'title': u'Carência de operação de R$ %s em %s, feita em %s' % (operacao.quantidade, operacao.cdb_rdb.nome, operacao.data.strftime('%d/%m/%Y')), 
                            'start': operacao.data_carencia().strftime('%Y-%m-%d')} for operacao in carencia_cdb_rdb])
        # Buscar apenas operações que vencem no período especificado
        vencimento_cdb_rdb = [operacao for operacao in operacoes_cdb_rdb if operacao.data_vencimento() >= data_inicial and operacao.data_vencimento() <= data_final]
        calendario.extend([{'title': u'Vencimento de operação de R$ %s em %s, feita em %s' % (operacao.quantidade, operacao.cdb_rdb.nome, operacao.data.strftime('%d/%m/%Y')), 
                            'start': operacao.data_vencimento().strftime('%Y-%m-%d')} for operacao in vencimento_cdb_rdb])
        
        # Carência e vencimento de Letras de Câmbio
        operacoes_lc = OperacaoLetraCambio.objects.filter(investidor=investidor, data__lt=data_final, tipo_operacao='C')
        # Buscar apenas operações com fim da carência no período especificado
        carencia_lc = [operacao for operacao in operacoes_lc if operacao.data_carencia() >= data_inicial and operacao.data_carencia() <= data_final]
        calendario.extend([{'title': u'Carência de operação de R$ %s em %s, feita em %s' % (operacao.quantidade, operacao.lc.nome, operacao.data.strftime('%d/%m/%Y')), 
                            'start': operacao.data_carencia().strftime('%Y-%m-%d')} for operacao in carencia_lc])
        # Buscar apenas operações que vencem no período especificado
        vencimento_lc = [operacao for operacao in operacoes_lc if operacao.data_vencimento() >= data_inicial and operacao.data_vencimento() <= data_final]
        calendario.extend([{'title': u'Vencimento de operação de R$ %s em %s, feita em %s' % (operacao.quantidade, operacao.lc.nome, operacao.data.strftime('%d/%m/%Y')), 
                            'start': operacao.data_vencimento().strftime('%Y-%m-%d')} for operacao in vencimento_lc])
        
        # Carência de LCI/LCA
        operacoes_lci_lca = OperacaoLetraCredito.objects.filter(investidor=investidor, data__lt=data_final, tipo_operacao='C')
        # Buscar apenas operações com fim da carência no período especificado
        carencia_lci_lca = [operacao for operacao in operacoes_lci_lca if operacao.data_carencia() >= data_inicial and operacao.data_carencia() <= data_final]
        calendario.extend([{'title': u'Carência de operação de R$ %s em %s, feita em %s' % (operacao.quantidade, operacao.letra_credito.nome, operacao.data.strftime('%d/%m/%Y')), 
                            'start': operacao.data_carencia().strftime('%Y-%m-%d')} for operacao in carencia_lci_lca])
        # Buscar apenas operações que vencem no período especificado
        vencimento_lci_lca = [operacao for operacao in operacoes_lci_lca if operacao.data_vencimento() >= data_inicial and operacao.data_vencimento() <= data_final]
        calendario.extend([{'title': u'Vencimento de operação de R$ %s em %s, feita em %s' % (operacao.quantidade, operacao.letra_credito.nome, operacao.data.strftime('%d/%m/%Y')), 
                            'start': operacao.data_vencimento().strftime('%Y-%m-%d')} for operacao in vencimento_lci_lca])
        
        # Vencimento, amortizações e remunerações de CRI/CRA
        remuneracoes_cri_cra = DataRemuneracaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, data__range=[data_inicial, data_final])
        calendario.extend([{'title': u'Remuneração de R$ %s para %s' % (data_remuneracao.qtd_remuneracao(), data_remuneracao.cri_cra.nome), 
                            'start': data_remuneracao.data.strftime('%Y-%m-%d')} for data_remuneracao in remuneracoes_cri_cra])
        amortizacoes_cri_cra = DataAmortizacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, data__range=[data_inicial, data_final])
        calendario.extend([{'title': u'Amortização para %s' % (data_amortizacao.cri_cra.nome), 
                            'start': data_amortizacao.data.strftime('%Y-%m-%d')} for data_amortizacao in amortizacoes_cri_cra])
        vencimentos_cri_cra = CRI_CRA.objects.filter(investidor=investidor, data_vencimento__range=[data_inicial, data_final])
        calendario.extend([{'title': u'Vencimento de %s' % (cri_cra.nome), 
                            'start': cri_cra.data_vencimento.strftime('%Y-%m-%d')} for cri_cra in vencimentos_cri_cra])
        
        # Vencimento de Tesouro Direto
        vencimento_td = Titulo.objects.filter(operacaotitulo__investidor=investidor, data_vencimento__range=[data_inicial, data_final]).distinct()
        calendario.extend([{'title': u'Vencimento de %s' % (titulo.nome()), 
                            'start': titulo.data_vencimento.strftime('%Y-%m-%d')} for titulo in vencimento_td])
        
        # Transferências em Criptomoedas
        transferencias_cripto = TransferenciaCriptomoeda.objects.filter(data__range=[data_inicial, data_final])
        calendario.extend([{'title': u'Transferência relacionada a Criptomoedas, %s %s' % (formatar_zeros_a_direita_apos_2_casas_decimais(transferencia.quantidade), transferencia.moeda_utilizada()),
                            'start': transferencia.data.strftime('%Y-%m-%d')} for transferencia in transferencias_cripto])
        
        # Rendimentos e amortizações de outros investimentos
        rendimentos_outros_inv = Rendimento.objects.filter(investimento__investidor=investidor, data__range=[data_inicial, data_final])
        calendario.extend([{'title': u'Rendimento de R$ %s para %s' % (data_rendimento.valor, data_rendimento.investimento),
                           'start': data_rendimento.data.strftime('%Y-%m-%d')} for data_rendimento in rendimentos_outros_inv])
        amortizacoes_outros_inv = Amortizacao.objects.filter(investimento__investidor=investidor, data__range=[data_inicial, data_final])
        calendario.extend([{'title': u'Amortização de R$ %s para %s' % (data_amortizacao.valor, data_amortizacao.investimento),
                           'start': data_amortizacao.data.strftime('%Y-%m-%d')} for data_amortizacao in amortizacoes_outros_inv])
        
        return HttpResponse(json.dumps(calendario), content_type = "application/json")   
    
    return TemplateResponse(request, 'calendario.html', {})

@login_required
@adiciona_titulo_descricao('Detalhamento de acumulados mensais', ('Detalha rendimentos recebidos por investimentos em renda fixa e ' \
                           'proventos em dinheiro recebidos por ações e FIIs'))
def detalhar_acumulados_mensais(request):
    investidor = request.user.investidor
    
    filtros = {'mes_inicial': '', 'mes_final': ''}
    if request.method == 'POST':
        try:
            data_inicial = datetime.datetime.strptime('01/%s' % (request.POST.get('mes_inicial')), '%d/%m/%Y')
            filtros['mes_inicial'] = data_inicial.strftime('%m/%Y')
            
            mes, ano = [int(valor) for valor in request.POST.get('mes_final').split('/')]
            data_atual = min(datetime.datetime(ano, mes, calendar.monthrange(ano, mes)[1]), datetime.datetime.now())
            filtros['mes_final'] = data_atual.strftime('%m/%Y')
            
            qtd_meses = (data_atual.year - data_inicial.year) * 12 + (data_atual.month - data_inicial.month + 1)
            
            if qtd_meses > 12 :
                messages.error(request, 'Insira um período de até 12 meses')
                filtros = {'mes_inicial': '', 'mes_final': ''}
        except:
            messages.error(request, 'Filtros de data inválidos')
            filtros = {'mes_inicial': '', 'mes_final': ''}
            
    if filtros['mes_inicial'] == '' or filtros['mes_final'] == '':
        data_atual = datetime.datetime.now()
        qtd_meses = 12
        data_inicial = data_atual.replace(day=1)
        for _ in range(qtd_meses-1):
            data_inicial = (data_inicial - datetime.timedelta(days=1)).replace(day=1)
        filtros = {'mes_inicial': data_inicial.strftime('%m/%Y'), 'mes_final': data_atual.strftime('%m/%Y')}
    
    # Guardar data final do período para o cálculo das taxas
    data_fim_periodo = data_atual.date()
    
    acumulados_mensais = list()
    acumulados_mensais.append([data_atual.date(), calcular_rendimentos_ate_data(investidor, data_atual.date())])
    
    graf_acumulados = list()
    
    for mes in range(qtd_meses):
        # Buscar dados para o acumulado mensal
        ultimo_dia_mes_anterior = data_atual.replace(day=1) - datetime.timedelta(days=1)
        acumulados_mensais.append([ultimo_dia_mes_anterior.date(), calcular_rendimentos_ate_data(investidor, ultimo_dia_mes_anterior.date())])
        # Adiciona o total mensal
        acumulados_mensais[mes].append(sum(acumulados_mensais[mes][1].values()) - sum(acumulados_mensais[mes+1][1].values()))
        # Gerar valor acumulado para cada investimento
        for investimento in acumulados_mensais[mes][1].keys():
            acumulados_mensais[mes][1][investimento] = acumulados_mensais[mes][1][investimento] - acumulados_mensais[mes+1][1][investimento]
        # Trocar data pela string de período
        acumulados_mensais[mes][0] = ['%s' % (data_atual.replace(day=1).strftime('%d/%m/%Y')), '%s' % (data_atual.strftime('%d/%m/%Y'))]
        
        # Adiciona total mensal ao gráfico
        graf_acumulados.append([str(calendar.timegm(data_atual.timetuple()) * 1000), float(acumulados_mensais[mes][2])])
        
        # Coloca data_atual como último dia do mês anterior
        data_atual = ultimo_dia_mes_anterior
    
    # Remover último elemento de acumulados mensais
    acumulados_mensais = acumulados_mensais[:-1]
    
    # Alterar a ordem do gráfico
    graf_acumulados.reverse()
    
    taxas = {}
    taxas['taxa_media_12_meses'] = sum([acumulado for _, _, acumulado in acumulados_mensais]) / (data_fim_periodo - data_atual.date()).days / 24 / 3600
    
    if taxas['taxa_media_12_meses'] != 0:
        # Testar se valor é negativo
        negativo = False
        if (taxas['taxa_media_12_meses'] < 0):
            negativo = True
            taxas['taxa_media_12_meses'] *= -1
        
        indice_primeiro_numero_valido = int(('%e' % taxas['taxa_media_12_meses']).partition('-')[2])
        if str(taxas['taxa_media_12_meses']).index('.') + indice_primeiro_numero_valido + 2 <= len(str(taxas['taxa_media_12_meses'])):
            taxas['taxa_media_12_meses'] = taxas['taxa_media_12_meses'].quantize(Decimal('0.' + '1'.zfill((indice_primeiro_numero_valido)+2)))
        
        if negativo:
            taxas['taxa_media_12_meses'] *= -1

#     velocidades = list()
#     for mes in range(10):
#         velocidades.append(acumulados_mensais[mes+1][2] - acumulados_mensais[mes+2][2])
#     velocidade_media = Decimal(sum(velocidades) / len(velocidades)).quantize(Decimal('0.01'))
#     print velocidades, velocidade_media
#     
#     aceleracoes = list()
#     for mes in range(9):
#         aceleracoes.append(velocidades[mes] - velocidades[mes+1])
#     aceleracao_media = Decimal(sum(aceleracoes) / len(aceleracoes)).quantize(Decimal('0.01'))
#     print aceleracoes, aceleracao_media
#         
#     print '%s + %s*mes + (%s*mes^2)/2' % (acumulados_mensais[11][2], acumulados_mensais[10][2] - acumulados_mensais[11][2], aceleracao_media)
    
    return TemplateResponse(request, 'detalhar_acumulados_mensais.html', {'acumulados_mensais': acumulados_mensais, 'graf_acumulados': graf_acumulados, 'taxas': taxas,
                                                                          'filtros': filtros})
    
@login_required
def detalhar_acumulado_mensal(request):
    class AcumuladoInvestimento(object):
        def __init__(self, investimento, qtd):
            self.investimento = investimento
            self.qtd = qtd
            
    investidor = request.user.investidor
    
    try:
        data_inicio = datetime.datetime.strptime(request.GET.get('data_inicio'), '%d/%m/%Y').date()
        data_fim = datetime.datetime.strptime(request.GET.get('data_fim'), '%d/%m/%Y').date()
    except:
        return HttpResponse(json.dumps({'mensagem': 'Datas inválidas'}), content_type = "application/json")
    
    # Pegar acumulado mensal até o dia anterior da data inicial
    rendimento_anterior = calcular_rendimentos_ate_data(investidor, (data_inicio - datetime.timedelta(days=1)))
    
    # Buscar acumulado até o final do período
    rendimento = calcular_rendimentos_ate_data(investidor, data_fim)
    
    # Subtrair valores para pegar o acumulado no período indicado
#     acumulado = { k: float(rendimento.get(k, 0) - rendimento_anterior.get(k, 0)) for k in set(rendimento) | set(rendimento_anterior)}
    acumulado = [AcumuladoInvestimento(k, float(rendimento.get(k, 0) - rendimento_anterior.get(k, 0))) for k in set(rendimento) | set(rendimento_anterior)]
    
    # Preparar nomes completos para cada investimento
    for acumulado_inv in acumulado:
        if acumulado_inv.investimento == 'A':
            acumulado_inv.investimento = 'Letras de Câmbio'
        if acumulado_inv.investimento == 'B':
            acumulado_inv.investimento = 'Buy and Hold'
        elif acumulado_inv.investimento == 'C':
            acumulado_inv.investimento = 'CDB/RDB'
        elif acumulado_inv.investimento == 'D':
            acumulado_inv.investimento = 'Tesouro Direto'
        elif acumulado_inv.investimento == 'E':
            acumulado_inv.investimento = 'Debêntures'
        elif acumulado_inv.investimento == 'F':
            acumulado_inv.investimento = 'FII'
        elif acumulado_inv.investimento == 'I':
            acumulado_inv.investimento = 'Fundos de investimento'
        elif acumulado_inv.investimento == 'L':
            acumulado_inv.investimento = 'Letras de Crédito'
        elif acumulado_inv.investimento == 'O':
            acumulado_inv.investimento = 'Outros investimentos'
        elif acumulado_inv.investimento == 'R':
            acumulado_inv.investimento = 'CRI/CRA'
        elif acumulado_inv.investimento == 'T':
            acumulado_inv.investimento = 'Trading'
    
    acumulado.sort(key=lambda x: x.investimento)
    
    return HttpResponse(json.dumps(render_to_string('utils/detalhar_acumulado_mensal.html', {'acumulado': acumulado, 'data_inicio': data_inicio,
                                                                                             'data_fim': data_fim})), content_type = "application/json")  


@login_required
@adiciona_titulo_descricao('Histórico detalhado', 'Histórico detalhado das operações feitas pelo investidor')
def detalhamento_investimentos(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass

    investidor = request.user.investidor
    
    # Adicionar FIIs do investidor
    operacoes_fii = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    if operacoes_fii:
        proventos_fii = ProventoFII.objects.exclude(data_ex__isnull=True).filter(fii__in=operacoes_fii.values_list('fii', flat=True), data_ex__range=[operacoes_fii[0].data, datetime.date.today()]) \
            .order_by('data_ex').annotate(data=F('data_ex'))
    else:
        proventos_fii = list()
    
    # Adicionar operações de Tesouro Direto do investidor
    operacoes_td = OperacaoTitulo.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Adicionar operações de Buy and Hold do investidor
    operacoes_bh = OperacaoAcao.objects.filter(investidor=investidor, destinacao='B').exclude(data__isnull=True).order_by('data')
    if operacoes_bh:
        proventos_bh = Provento.objects.exclude(data_ex__isnull=True).filter(acao__in=operacoes_bh.values_list('acao', flat=True), data_ex__range=[operacoes_bh[0].data, datetime.date.today()]) \
            .order_by('data_ex').annotate(data=F('data_ex'))
    else:
        proventos_bh = list()
        
    # Adicionar operações de Trading do investidor
    operacoes_t = OperacaoAcao.objects.filter(investidor=investidor, destinacao='T').exclude(data__isnull=True).order_by('data')
    
    operacoes_lc = OperacaoLetraCambio.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Adicionar operações de LCI/LCA do investidor
    operacoes_lci_lca = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  

    # Adicionar operações de CDB/RDB do investidor    
    operacoes_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data') 
    
    # Adicionar operações de CRI/CRA do investidor    
    operacoes_cri_cra = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor).exclude(data__isnull=True).order_by('data') 
    
    # Adicionar operações de Debêntures do investidor
    operacoes_debentures = OperacaoDebenture.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Adicionar operações de Fundo de Investimento do investidor
    operacoes_fundo_investimento = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Adicionar operações em Criptomoedas do investidor
    operacoes_criptomoedas = OperacaoCriptomoeda.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Adicionar transferências em Criptomoedas do investidor
    transferencias_criptomoedas = TransferenciaCriptomoeda.objects.filter(investidor=investidor, taxa__gt=Decimal(0), moeda__isnull=False).exclude(data__isnull=True).order_by('data')
    
    # Adicionar outros investimentos do investidor
    outros_investimentos = Investimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Adicionar amortizações de outros investimentos
    amort_outros_investimentos = Amortizacao.objects.filter(investimento__investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Juntar todas as operações
    lista_operacoes = sorted(chain(proventos_fii, operacoes_fii, operacoes_td, proventos_bh,  operacoes_bh, operacoes_t, operacoes_lci_lca, operacoes_cdb_rdb, 
                                   operacoes_cri_cra, operacoes_debentures, operacoes_fundo_investimento, operacoes_criptomoedas, operacoes_lc,
                                   transferencias_criptomoedas, outros_investimentos, amort_outros_investimentos),
                            key=attrgetter('data'))

    # Se não houver operações, retornar vazio
    if not lista_operacoes:
        data_anterior = str(calendar.timegm((datetime.date.today() - datetime.timedelta(days=365)).timetuple()) * 1000)
        data_atual = str(calendar.timegm(datetime.date.today().timetuple()) * 1000)
        return TemplateResponse(request, 'detalhamento_investimentos.html', {'graf_patrimonio': [[data_anterior, float(0)], [data_atual, float(0)]], 'patrimonio_anual': list(),
                                                                             'estatisticas': list(), 'graf_patrimonio_cripto': list()})
    
    # Pegar ano da primeira operacao feita
    ano_corrente = lista_operacoes[0].data.year
    
    datas_finais_ano = set()
    # Adicionar datas finais de cada ano
    for ano in range(ano_corrente, datetime.date.today().year):
        ultima_operacao = Object()
        ultima_operacao.data = datetime.date(ano, 12, 31)
        datas_finais_ano.add(ultima_operacao)
        
    # Adicionar data atual
    data_atual = Object()
    data_atual.data = datetime.date.today()
    datas_finais_ano.add(data_atual)
    
    # Adicionar datas para estatísticas
    datas_estatisticas = set()
    # Dia anterior
    data_dia_anterior = Object()
    data_dia_anterior.data = datetime.date.today() + datetime.timedelta(days=-1)
    if data_dia_anterior.data >= lista_operacoes[0].data:
        data_dia_anterior.descricao = "1 dia"
        datas_estatisticas.add(data_dia_anterior)
    # 1 semana
    data_1_semana = Object()
    data_1_semana.data = datetime.date.today() + datetime.timedelta(days=-7)
    if data_1_semana.data >= lista_operacoes[0].data:
        data_1_semana.descricao = "7 dias"
        datas_estatisticas.add(data_1_semana)
    # 30 dias
    data_30_dias = Object()
    data_30_dias.data = datetime.date.today() + datetime.timedelta(days=-30)
    if data_30_dias.data >= lista_operacoes[0].data:
        data_30_dias.descricao = "30 dias"
        datas_estatisticas.add(data_30_dias)
    # 3 meses
    data_3_meses = Object()
    data_3_meses.data = datetime.date.today() + datetime.timedelta(days=-90)
    if data_3_meses.data >= lista_operacoes[0].data:
        data_3_meses.descricao = "3 meses"
        datas_estatisticas.add(data_3_meses)
    # 1 semestre
    data_1_semestre = Object()
    data_1_semestre.data = datetime.date.today() + datetime.timedelta(days=-180)
    if data_1_semestre.data >= lista_operacoes[0].data:
        data_1_semestre.descricao = "1 semestre"
        datas_estatisticas.add(data_1_semestre)
    # 1 ano
    data_1_ano = Object()
    data_1_ano.data = datetime.date.today() + datetime.timedelta(days=-365)
    if data_1_ano.data >= lista_operacoes[0].data:
        data_1_ano.descricao = "1 ano"
        datas_estatisticas.add(data_1_ano)
    
    lista_conjunta = sorted(chain(lista_operacoes, datas_finais_ano, datas_estatisticas),
                            key=attrgetter('data'))
    
    fii = {}
    acoes_bh = {}
    acoes_t = {}
    titulos_td = {}
    letras_credito = {}
    # Caso haja Letra de Crédito, preparar para o cálculo
    if operacoes_lci_lca.exists():
        ultima_data_calculada_lci_lca = operacoes_lci_lca[0].data
    else:
        ultima_data_calculada_lci_lca = datetime.date.today()
    cdb_rdb = {}
    # Caso haja CDB/RDB, preparar para o cálculo
    if operacoes_cdb_rdb.exists():
        ultima_data_calculada_cdb_rdb = operacoes_cdb_rdb[0].data
    else:
        ultima_data_calculada_cdb_rdb = datetime.date.today()
    letras_cambio = {}
    if operacoes_lc.exists():
        ultima_data_calculada_lc = operacoes_lc[0].data
    else:
        ultima_data_calculada_lc = datetime.date.today()
    cri_cra = {}
    fundos_investimento = {}
    debentures = {}
    criptomoedas = {}
    invest = {}
    total_proventos_fii = 0
    total_proventos_bh = 0
    
    patrimonio = {}
    patrimonio_anual = list()
    graf_patrimonio = list()
    # Utilizado para auxiliar o browser a buscar valores históricos de criptomoedas
    graf_patrimonio_cripto = list()
    estatisticas = list()
    
    ############# TESTE
#     total_acoes_bh = datetime.timedelta(hours=0)
#     total_acoes_t = datetime.timedelta(hours=0)
#     total_prov_acoes_bh = datetime.timedelta(hours=0)
#     total_fii = datetime.timedelta(hours=0)
#     total_prov_fii = datetime.timedelta(hours=0)
#     total_td = datetime.timedelta(hours=0)
#     total_lc = datetime.timedelta(hours=0)
#     total_lci_lca = datetime.timedelta(hours=0)
#     total_cdb_rdb = datetime.timedelta(hours=0)
#     total_cri_cra = datetime.timedelta(hours=0)
#     total_debentures = datetime.timedelta(hours=0)
#     total_fundo_investimento = datetime.timedelta(hours=0)
#     total_criptomoeda = datetime.timedelta(hours=0)
#     total_outros_invest = datetime.timedelta(hours=0)
    ############# TESTE
    
    for index, item in enumerate(lista_conjunta):    
        # Atualizar lista de patrimonio atual ao trocar de ano
        if item.data.year != ano_corrente:
            if len(patrimonio_anual) > 0:
                diferenca = patrimonio['patrimonio_total'] - patrimonio_anual[len(patrimonio_anual) - 1][1]['patrimonio_total']
            else:
                diferenca = patrimonio['patrimonio_total']
            patrimonio_anual += [[str(ano_corrente).replace('.', ''), patrimonio, diferenca]]
            ano_corrente = item.data.year
        
        if isinstance(item, OperacaoAcao):
            if item.destinacao == 'B':
                if item.acao.ticker not in acoes_bh.keys():
                    acoes_bh[item.acao.ticker] = 0 
                if item.tipo_operacao == 'C':
                    acoes_bh[item.acao.ticker] += item.quantidade
                    if len(item.usoproventosoperacaoacao_set.all()) > 0:
                        total_proventos_bh -= item.qtd_proventos_utilizada()
                elif item.tipo_operacao == 'V':
                    acoes_bh[item.acao.ticker] -= item.quantidade
            
            elif item.destinacao == 'T':
                if item.acao.ticker not in acoes_t.keys():
                    acoes_t[item.acao.ticker] = 0 
                if item.tipo_operacao == 'C':
                    acoes_t[item.acao.ticker] += item.quantidade
#                     if len(item.usoproventosoperacaoacao_set.all()) > 0:
#                         total_proventos_t -= item.qtd_proventos_utilizada()
                elif item.tipo_operacao == 'V':
                    acoes_t[item.acao.ticker] -= item.quantidade
                
        elif isinstance(item, Provento):
            if item.data_pagamento <= datetime.date.today():
                if item.acao.ticker not in acoes_bh.keys():
                    acoes_bh[item.acao.ticker] = 0 
                if item.tipo_provento in ['D', 'J']:
                    total_recebido = acoes_bh[item.acao.ticker] * item.valor_unitario
                    if item.tipo_provento == 'J':
                        total_recebido = total_recebido * Decimal(0.85)
                    total_proventos_bh += total_recebido
                elif item.tipo_provento == 'A':
                    provento_acao = item.acaoprovento_set.all()[0]
                    if provento_acao.acao_recebida.ticker not in acoes_bh.keys():
                        acoes_bh[provento_acao.acao_recebida.ticker] = 0
                    acoes_recebidas = int((acoes_bh[item.acao.ticker] * item.valor_unitario ) / 100 )
                    acoes_bh[provento_acao.acao_recebida.ticker] += acoes_recebidas
                    if provento_acao.valor_calculo_frac > 0:
                        if provento_acao.data_pagamento_frac <= datetime.date.today():
                            total_proventos_bh += (((acoes_bh[item.acao.ticker] * item.valor_unitario ) / 100 ) % 1 * provento_acao.valor_calculo_frac)
                
        elif isinstance(item, OperacaoTitulo):  
            if item.titulo not in titulos_td.keys():
                titulos_td[item.titulo] = 0
            if item.tipo_operacao == 'C':
                titulos_td[item.titulo] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                titulos_td[item.titulo] -= item.quantidade
                
        elif isinstance(item, OperacaoFII):
            if item.fii.ticker not in fii.keys():
                fii[item.fii.ticker] = 0    
            if item.tipo_operacao == 'C':
                fii[item.fii.ticker] += item.quantidade
                if len(item.usoproventosoperacaofii_set.all()) > 0:
                    total_proventos_fii -= float(item.usoproventosoperacaofii_set.all()[0].qtd_utilizada)
                
            elif item.tipo_operacao == 'V':
                fii[item.fii.ticker] -= item.quantidade
                
        elif isinstance(item, ProventoFII):
            if item.fii.ticker not in fii.keys():
                fii[item.fii.ticker] = 0    
            item.total = math.floor(fii[item.fii.ticker] * item.valor_unitario * 100) / 100
            total_proventos_fii += item.total
                
        elif isinstance(item, OperacaoLetraCambio):
            if item.tipo_operacao == 'C':
                item.taxa = item.porcentagem()
                item.qtd_inicial = item.quantidade
                letras_cambio[item.id] = item
                
            elif item.tipo_operacao == 'V':
                operacao_relacionada_id = item.operacao_compra_relacionada().id
                if item.quantidade == letras_cambio[operacao_relacionada_id].qtd_inicial:
                    del letras_cambio[operacao_relacionada_id]
                else:
                    letras_cambio[operacao_relacionada_id].quantidade -= letras_cambio[operacao_relacionada_id].quantidade \
                        * item.quantidade / letras_cambio[operacao_relacionada_id].qtd_inicial
                    letras_cambio[operacao_relacionada_id].qtd_inicial -= item.quantidade
               
        elif isinstance(item, OperacaoLetraCredito):
            if item.tipo_operacao == 'C':
                item.taxa = item.porcentagem()
                item.qtd_inicial = item.quantidade
                letras_credito[item.id] = item
                
            elif item.tipo_operacao == 'V':
                operacao_relacionada_id = item.operacao_compra_relacionada().id
                if item.quantidade == letras_credito[operacao_relacionada_id].qtd_inicial:
                    del letras_credito[operacao_relacionada_id]
                else:
                    letras_credito[operacao_relacionada_id].quantidade -= letras_credito[operacao_relacionada_id].quantidade \
                        * item.quantidade / letras_credito[operacao_relacionada_id].qtd_inicial
                    letras_credito[operacao_relacionada_id].qtd_inicial -= item.quantidade
                
        elif isinstance(item, OperacaoCDB_RDB):
            if item.tipo_operacao == 'C':
                item.taxa = item.porcentagem()
                item.qtd_inicial = item.quantidade
                cdb_rdb[item.id] = item
                
            elif item.tipo_operacao == 'V':
                operacao_relacionada_id = item.operacao_compra_relacionada().id
                if item.quantidade == cdb_rdb[operacao_relacionada_id].qtd_inicial:
                    del cdb_rdb[operacao_relacionada_id]
                else:
                    cdb_rdb[operacao_relacionada_id].quantidade -= cdb_rdb[operacao_relacionada_id].quantidade \
                        * item.quantidade / cdb_rdb[operacao_relacionada_id].qtd_inicial
                    cdb_rdb[operacao_relacionada_id].qtd_inicial -= item.quantidade
                    
        elif isinstance(item, OperacaoCRI_CRA):
            if item.cri_cra not in cri_cra.keys():
                cri_cra[item.cri_cra] = 0    
            if item.tipo_operacao == 'C':
                cri_cra[item.cri_cra] += item.quantidade 
                
            elif item.tipo_operacao == 'V':
                cri_cra[item.cri_cra] -= item.quantidade 
            
        elif isinstance(item, OperacaoDebenture):
            if item.debenture not in debentures.keys():
                debentures[item.debenture] = 0    
            if item.tipo_operacao == 'C':
                debentures[item.debenture] += item.quantidade 
                
            elif item.tipo_operacao == 'V':
                debentures[item.debenture] -= item.quantidade 
                
        elif isinstance(item, OperacaoFundoInvestimento):
            if item.fundo_investimento not in fundos_investimento.keys():
                fundos_investimento[item.fundo_investimento] = 0    
            if item.tipo_operacao == 'C':
                fundos_investimento[item.fundo_investimento] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                fundos_investimento[item.fundo_investimento] -= item.quantidade
                
        elif isinstance(item, OperacaoCriptomoeda):
            if item.criptomoeda.ticker not in criptomoedas.keys():
                criptomoedas[item.criptomoeda.ticker] = 0
            if hasattr(item, 'operacaocriptomoedamoeda') and item.operacaocriptomoedamoeda.criptomoeda.ticker not in criptomoedas.keys():
                criptomoedas[item.operacaocriptomoedamoeda.criptomoeda.ticker] = 0
            if item.tipo_operacao == 'C':
                criptomoedas[item.criptomoeda.ticker] += item.quantidade
                # Alterar quantidade da criptomoeda utilizada na operação
                if hasattr(item, 'operacaocriptomoedamoeda'):
                    # Verifica a existência de taxas
                    if hasattr(item, 'operacaocriptomoedataxa'):
                        if item.operacaocriptomoedataxa.moeda == item.criptomoeda:
                            item.preco_total = (item.quantidade + item.operacaocriptomoedataxa.valor) * item.preco_unitario
                        elif item.operacaocriptomoedataxa.moeda_utilizada() == item.moeda_utilizada():
                            item.preco_total = item.quantidade * item.preco_unitario + item.operacaocriptomoedataxa.valor
                        else:
                            raise ValueError('Moeda utilizada na taxa é inválida')
                    else:
                        item.preco_total = item.quantidade * item.preco_unitario
                    criptomoedas[item.operacaocriptomoedamoeda.criptomoeda.ticker] -= item.preco_total
            
            elif item.tipo_operacao == 'V':
                criptomoedas[item.criptomoeda.ticker] -= item.quantidade
                # Alterar quantidade da criptomoeda utilizada na operação
                if hasattr(item, 'operacaocriptomoedamoeda'):
                    # Verifica a existência de taxas
                    if hasattr(item, 'operacaocriptomoedataxa'):
                        # Taxas são inclusas na quantidade vendida
                        if item.operacaocriptomoedataxa.moeda == item.criptomoeda:
                            item.preco_total = (item.quantidade - item.operacaocriptomoedataxa.valor) * item.preco_unitario
                        elif item.operacaocriptomoedataxa.moeda_utilizada() == item.moeda_utilizada():
                            item.preco_total = item.quantidade * item.preco_unitario - item.operacaocriptomoedataxa.valor
                        else:
                            raise ValueError('Moeda utilizada na taxa é inválida')
                    else:
                        item.preco_total = item.quantidade * item.preco_unitario
                    criptomoedas[item.operacaocriptomoedamoeda.criptomoeda.ticker] += item.preco_total
                    
        elif isinstance(item, TransferenciaCriptomoeda):
            if item.moeda.ticker not in criptomoedas.keys():
                criptomoedas[item.moeda.ticker] = 0
            criptomoedas[item.moeda.ticker] -= item.taxa
            
        elif isinstance(item, Investimento):
            if item.id not in invest.keys():
                invest[item.id] = 0
            invest[item.id] += item.quantidade
            
        elif isinstance(item, Amortizacao):
            invest[item.investimento.id] -= item.valor

        # Se não cair em nenhum dos anteriores: item vazio
        
        # Se última operação feita no dia, calcular patrimonio
        if index == len(lista_conjunta)-1 or item.data < lista_conjunta[index+1].data:
            patrimonio = {}
            patrimonio['patrimonio_total'] = 0
    
            # Rodar calculo de patrimonio
            # Acoes (B&H)
#             inicio_acoes_bh = datetime.datetime.now()
            patrimonio['Ações (Buy and Hold)'] = 0
            for acao, quantidade in acoes_bh.items():
                if quantidade > 0:
                    # Pegar valor do dia caso seja data atual
                    if item.data == datetime.date.today() and ValorDiarioAcao.objects.filter(acao__ticker=acao, data_hora__date=item.data).exists():
                        valor_acao = ValorDiarioAcao.objects.filter(acao__ticker=acao).order_by('-data_hora')[0].preco_unitario
                    else:
                        # Pegar último dia util com negociação da ação para calculo do patrimonio
                        valor_acao = HistoricoAcao.objects.filter(acao__ticker=acao, data__lte=item.data).order_by('-data')[0].preco_unitario
                    patrimonio['Ações (Buy and Hold)'] += (valor_acao * quantidade)
            patrimonio['patrimonio_total'] += patrimonio['Ações (Buy and Hold)'] 
#             fim_acoes_bh = datetime.datetime.now()
#             total_acoes_bh += fim_acoes - inicio_acoes_bh
            
            # Proventos Acoes
#             inicio_prov_acoes = datetime.datetime.now()
            patrimonio['Proventos Ações'] = Decimal(int(total_proventos_bh * 100) / Decimal(100))
            patrimonio['patrimonio_total'] += patrimonio['Proventos Ações']
#             fim_prov_acoes_bh = datetime.datetime.now()
#             total_prov_acoes_bh += fim_prov_acoes - inicio_prov_acoes_bh
            
            # Acoes (Trading)
#             inicio_acoes_t = datetime.datetime.now()
            patrimonio['Ações (Trading)'] = 0
            for acao, quantidade in acoes_t.items():
                if quantidade > 0:
                    # Pegar valor do dia caso seja data atual
                    if item.data == datetime.date.today() and ValorDiarioAcao.objects.filter(acao__ticker=acao, data_hora__date=item.data).exists():
                        valor_acao = ValorDiarioAcao.objects.filter(acao__ticker=acao).order_by('-data_hora')[0].preco_unitario
                    else:
                        # Pegar último dia util com negociação da ação para calculo do patrimonio
                        valor_acao = HistoricoAcao.objects.filter(acao__ticker=acao, data__lte=item.data).order_by('-data')[0].preco_unitario
                    patrimonio['Ações (Trading)'] += (valor_acao * quantidade)
            patrimonio['patrimonio_total'] += patrimonio['Ações (Trading)'] 
#             fim_acoes_t = datetime.datetime.now()
#             total_acoes_t += fim_acoes - inicio_acoes_t
            
            # TD
#             inicio_td = datetime.datetime.now()
            patrimonio['Tesouro Direto'] = 0
            for titulo in titulos_td.keys():
                if item.data is not datetime.date.today():
                    ultimo_dia_util = item.data
                    while not HistoricoTitulo.objects.filter(data=ultimo_dia_util, titulo=titulo):
                        ultimo_dia_util -= datetime.timedelta(days=1)
                    patrimonio['Tesouro Direto'] += (titulos_td[titulo] * HistoricoTitulo.objects.get(data=ultimo_dia_util, titulo=titulo).preco_venda)
                else:
                    # Buscar valor mais atual de valor diário, se existir
                    if ValorDiarioTitulo.objects.filter(titulo=titulo, data_hora__date=datetime.date.today()).order_by('-data_hora'):
                        valor_diario = ValorDiarioTitulo.objects.filter(titulo=titulo, data_hora__date=datetime.date.today()).order_by('-data_hora')[0]
                        patrimonio['Tesouro Direto'] += (titulos_td[titulo] * valor_diario.preco_venda)
                        break
                    else:
                        # Se não há valor diário, buscar histórico mais atual mesmo
                        patrimonio['Tesouro Direto'] += (titulos_td[titulo] * HistoricoTitulo.objects.filter(titulo=titulo).order_by('-data')[0].preco_venda)
            patrimonio['patrimonio_total'] += patrimonio['Tesouro Direto'] 
#             fim_td = datetime.datetime.now()
#             total_td += fim_td - inicio_td
                
            # FII
#             inicio_fii = datetime.datetime.now()
            patrimonio['FII'] = 0
            for papel, quantidade in fii.items():
                # Pegar valor do dia caso seja data atual
                if item.data == datetime.date.today() and ValorDiarioFII.objects.filter(fii__ticker=papel, data_hora__date=item.data).exists():
                    valor_fii = ValorDiarioFII.objects.filter(fii__ticker=papel).order_by('-data_hora')[0].preco_unitario
                else:
                    # Pegar último dia util com negociação da ação para calculo do patrimonio
                    valor_fii = HistoricoFII.objects.filter(fii__ticker=papel, data__lte=item.data).order_by('-data')[0].preco_unitario
                patrimonio['FII'] += (quantidade * valor_fii)
            patrimonio['patrimonio_total'] += patrimonio['FII']  
#             fim_fii = datetime.datetime.now()
#             total_fii += fim_fii - inicio_fii
                    
            # Proventos FII
#             inicio_prov_fii = datetime.datetime.now()
            patrimonio['Proventos FII'] = Decimal(int(total_proventos_fii * 100) / Decimal(100))
            patrimonio['patrimonio_total'] += patrimonio['Proventos FII'] 
#             fim_prov_fii = datetime.datetime.now()
#             total_prov_fii += fim_prov_fii - inicio_prov_fii
            
            # Letras de Câmbio
#             inicio_lc = datetime.datetime.now()
            patrimonio_lc = 0
            # Rodar calculo com as datas desde o último calculo, com 1 dia de atraso pois a atualização é a do dia anterior
            dia_anterior = item.data - datetime.timedelta(days=1)
            if item.data > ultima_data_calculada_lc:
                # Retira a data limite (item.data) do cálculo
                taxas = HistoricoTaxaDI.objects.filter(data__range=[ultima_data_calculada_lc, dia_anterior]).values('taxa').annotate(qtd_dias=Count('taxa'))
                taxas_dos_dias = {}
                for taxa in taxas:
                    taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
                for operacao in letras_cambio.values():
                    if operacao.data < item.data:
#                         operacao.quantidade = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.taxa)
                        operacao.quantidade = calcular_valor_atualizado_operacao_ate_dia_lc(operacao.quantidade, 
                                                                     ultima_data_calculada_lc, dia_anterior, operacao, 
                                                                     operacao.qtd_inicial)
                # Guardar ultima data de calculo
                ultima_data_calculada_lc = item.data
            for letra_cambio in letras_cambio.values():
                patrimonio_lc += letra_cambio.quantidade.quantize(Decimal('.01'), ROUND_DOWN)
            patrimonio['Letras de Câmbio'] = patrimonio_lc
            patrimonio['patrimonio_total'] += patrimonio['Letras de Câmbio'] 
#             fim_lc = datetime.datetime.now()
#             total_lc += fim_lc - inicio_lc
            
            # LCI/LCA
#             inicio_lci_lca = datetime.datetime.now()
            patrimonio_lci_lca = 0
            # Rodar calculo com as datas desde o último calculo, com 1 dia de atraso pois a atualização é a do dia anterior
            dia_anterior = item.data - datetime.timedelta(days=1)
            if item.data > ultima_data_calculada_lci_lca:
                # Retira a data limite (item.data) do cálculo
                taxas = HistoricoTaxaDI.objects.filter(data__range=[ultima_data_calculada_lci_lca, dia_anterior]).values('taxa').annotate(qtd_dias=Count('taxa'))
                taxas_dos_dias = {}
                for taxa in taxas:
                    taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
                for operacao in letras_credito.values():
                    if operacao.data < item.data:
                        operacao.quantidade = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.taxa)
                # Guardar ultima data de calculo
                ultima_data_calculada_lci_lca = item.data
            for letra_credito in letras_credito.values():
                patrimonio_lci_lca += letra_credito.quantidade.quantize(Decimal('.01'), ROUND_DOWN)
            patrimonio['Letras de Crédito'] = patrimonio_lci_lca
            patrimonio['patrimonio_total'] += patrimonio['Letras de Crédito'] 
#             fim_lci_lca = datetime.datetime.now()
#             total_lci_lca += fim_lci_lca - inicio_lci_lca
            
            # CDB/RDB
#             inicio_cdb_rdb = datetime.datetime.now()
            patrimonio_cdb_rdb = 0
            # Rodar calculo com as datas desde o último calculo, com 1 dia de atraso pois a atualização é a do dia anterior
            dia_anterior = item.data - datetime.timedelta(days=1)
            if item.data > ultima_data_calculada_cdb_rdb:
                # Retira a data limite (item.data) do cálculo
                taxas = HistoricoTaxaDI.objects.filter(data__range=[ultima_data_calculada_cdb_rdb, dia_anterior]).values('taxa').annotate(qtd_dias=Count('taxa'))
                taxas_dos_dias = {}
                for taxa in taxas:
                    taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
                for operacao in cdb_rdb.values():
                    if operacao.data < item.data:
                        operacao.quantidade = calcular_valor_atualizado_operacao_ate_dia_cdb_rdb(operacao.quantidade, 
                                                                     ultima_data_calculada_cdb_rdb, dia_anterior, operacao, 
                                                                     operacao.qtd_inicial)
                # Guardar ultima data de calculo
                ultima_data_calculada_cdb_rdb = item.data
            for investimento in cdb_rdb.values():
                patrimonio_cdb_rdb += investimento.quantidade.quantize(Decimal('.01'), ROUND_DOWN)
            patrimonio['CDB/RDB'] = patrimonio_cdb_rdb
            patrimonio['patrimonio_total'] += patrimonio['CDB/RDB'] 
#             fim_cdb_rdb = datetime.datetime.now()
#             total_cdb_rdb += fim_cdb_rdb - inicio_cdb_rdb

            # CRI/CRA
#             inicio_cri_cra = datetime.datetime.now()
            patrimonio_cri_cra = 0
            for certificado in cri_cra.keys():
                patrimonio_cri_cra += (cri_cra[certificado] * calcular_valor_um_cri_cra_na_data(certificado, item.data)).quantize(Decimal('.01'))
            patrimonio['CRI/CRA'] = patrimonio_cri_cra
            patrimonio['patrimonio_total'] += patrimonio['CRI/CRA'] 
#             fim_cri_cra = datetime.datetime.now()
#             total_cri_cra += fim_cri_cra - inicio_cri_cra

            # Debênture
#             inicio_debentures = datetime.datetime.now()
            patrimonio_debentures = 0
            for debenture in debentures.keys():
                historico_fundo = HistoricoValorDebenture.objects.filter(debenture=debenture, data__lte=item.data).order_by('-data')[0]
                patrimonio_debentures += debentures[debenture] * historico_fundo.valor_total()
            patrimonio['Debêntures'] = patrimonio_debentures
            patrimonio['patrimonio_total'] += patrimonio['Debêntures'] 
#             fim_debentures = datetime.datetime.now()
#             total_debentures += fim_debentures - inicio_debentures

            # Fundo de investimento
#             inicio_fundo_investimento = datetime.datetime.now()
            patrimonio_fundo_investimento = 0
            for fundo in fundos_investimento.keys():
                historico_fundo = HistoricoValorCotas.objects.filter(fundo_investimento=fundo, data__lte=item.data).order_by('-data')
                ultima_operacao_fundo = OperacaoFundoInvestimento.objects.filter(data__lte=item.data, fundo_investimento=fundo).order_by('-data')[0]
                if historico_fundo and historico_fundo[0].data > ultima_operacao_fundo.data:
                    patrimonio_fundo_investimento += fundos_investimento[fundo] * historico_fundo[0].valor_cota
                else:
                    patrimonio_fundo_investimento += fundos_investimento[fundo] * ultima_operacao_fundo.valor_cota()
            patrimonio['Fundo de Inv.'] = patrimonio_fundo_investimento
            patrimonio['patrimonio_total'] += patrimonio['Fundo de Inv.'] 
#             fim_fundo_investimento = datetime.datetime.now()
#             total_fundo_investimento += fim_fundo_investimento - inicio_fundo_investimento
            
            # Criptomoedas
#             inicio_criptomoedas = datetime.datetime.now()
            patrimonio_criptomoedas = 0
            # Verifica se é a data atual
            if item.data == datetime.date.today():
                # Calcular pela função de valores atuais do CryptoCompare
                patrimonio_criptomoedas = sum([criptomoedas[ticker] * valor for ticker, valor in \
                                               {valor_diario.criptomoeda.ticker: valor_diario.valor for \
                                                valor_diario in ValorDiarioCriptomoeda.objects.filter(criptomoeda__ticker__in=criptomoedas.keys(), moeda='BRL')}.items()])
            patrimonio['Criptomoedas'] = patrimonio_criptomoedas
            patrimonio['patrimonio_total'] += patrimonio['Criptomoedas']
            
            # Outros investimentos
#             inicio_outros_invest = datetime.datetime.now()
            patrimonio['Outros inv.'] = sum(invest.values())
            patrimonio['patrimonio_total'] += patrimonio['Outros inv.']
            
#             print 'Ações (B&H)          ', total_acoes_bh
#             print 'Ações (Trading)      ', total_acoes_t
#             print 'Prov. Ações          ', total_prov_acoes_bh
#             print 'TD                   ', total_td
#             print 'FII                  ', total_fii
#             print 'Prov. FII            ', total_prov_fii
#             print 'Letras de Câmbio     ', total_lc
#             print 'LCI/LCA              ', total_lci_lca
#             print 'CDB/RDB              ', total_cdb_rdb
#             print 'CRI/CRA              ', total_cri_cra
#             print 'Debêntures           ', total_debentures
#             print 'Fundo Inv.           ', total_fundo_investimento
#             print 'Cripto.              ', total_criptomoeda
#             print 'Outros inv.          ', total_outros_invest
            
            # Preparar estatísticas
            for data_estatistica in datas_estatisticas:
                if item.data == data_estatistica.data: 
                    if len(estatisticas) > 0 and estatisticas[len(estatisticas)-1][0] == data_estatistica.descricao:
                        estatisticas[len(estatisticas)-1] = [data_estatistica.descricao, float(patrimonio['patrimonio_total'])]
                    else:
                        estatisticas += [[data_estatistica.descricao, float(patrimonio['patrimonio_total'])]]
                 
            # Preparar data
            data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
            # Verifica se altera ultima posicao do grafico ou adiciona novo registro
            if len(graf_patrimonio) > 0 and graf_patrimonio[len(graf_patrimonio)-1][0] == data_formatada:
                graf_patrimonio[len(graf_patrimonio)-1][1] = float(patrimonio['patrimonio_total'])
            else:
                graf_patrimonio += [[data_formatada, float(patrimonio['patrimonio_total'])]]
            
            if criptomoedas and item.data != datetime.date.today():        
                # Jogar valores para o cálculo de histórico no browser do usuário
                data_formatada_utc = calendar.timegm(item.data.timetuple())
                moedas = {ticker: float(qtd) for ticker, qtd in criptomoedas.items()}
                graf_patrimonio_cripto += [[data_formatada, data_formatada_utc, moedas]]
            
    # Adicionar ultimo valor ao dicionario de patrimonio anual
    if len(patrimonio_anual) > 0:
        diferenca = patrimonio['patrimonio_total'] - patrimonio_anual[len(patrimonio_anual) - 1][1]['patrimonio_total']
    else:
        diferenca = patrimonio['patrimonio_total']
    patrimonio_anual += [[str(ano_corrente).replace('.', ''), patrimonio, diferenca]]
    
    # Terminar estatísticas
    for index, estatistica in enumerate(estatisticas):
        estatisticas[index] = [estatistica[0], float(patrimonio['patrimonio_total']) - estatistica[1]]
    
#     print 'Ações (B&H):      ', total_acoes_bh
#     print 'Ações (Trading):  ', total_acoes_t
#     print 'Prov. ações:      ', total_prov_acoes_bh
#     print 'FII:              ', total_fii 
#     print 'Prov. FII:        ', total_prov_fii 
#     print 'TD:               ', total_td 
#     print 'Letras de Câmbio: ', total_lc
#     print 'LCI/LCA:          ', total_lci_lca 
#     print 'CDB/RDB:          ', total_cdb_rdb
#     print 'CRI/CRA:          ', total_cri_cra
#     print 'Debêntures:       ', total_debentures
#     print 'Fundo Inv.:       ', total_fundo_investimento
#     print 'Cripto.           ', total_criptomoeda
#     print 'Outros inv.       ', total_outros_invest
    
    return TemplateResponse(request, 'detalhamento_investimentos.html', {'graf_patrimonio': graf_patrimonio, 'patrimonio_anual': patrimonio_anual,
                                            'estatisticas': estatisticas, 'graf_patrimonio_cripto': json.dumps(graf_patrimonio_cripto)})

@adiciona_titulo_descricao('', 'O Bag of Gold permite que o usuário acompanhe seus investimentos em um único lugar')
def inicio(request):
    posts = Post.objects.all().order_by('-data').prefetch_related('tagpost_set__tag')[:6]
    
    return TemplateResponse(request, 'inicio.html', {'posts': posts})

@login_required
@adiciona_titulo_descricao('Listar operações', 'Lista todas as operações do investidor')
def listar_operacoes(request):
    investidor = request.user.investidor
    
    operacoes = buscar_operacoes_no_periodo(investidor, investidor.buscar_data_primeira_operacao(), datetime.date.today())
    
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.tipo_operacao = 'Compra'
        elif operacao.tipo_operacao == 'V':
            operacao.tipo_operacao = 'Venda'
        if isinstance(operacao, OperacaoFII):
            operacao.tipo_investimento = 'FII'
            operacao.valor_total = operacao.quantidade * operacao.preco_unitario
        if isinstance(operacao, OperacaoTitulo):
            operacao.tipo_investimento = 'Tesouro Direto'
            operacao.valor_total = operacao.quantidade * operacao.preco_unitario
        if isinstance(operacao, OperacaoAcao):
            operacao.tipo_investimento = u'Ações'
            operacao.valor_total = operacao.quantidade * operacao.preco_unitario
        if isinstance(operacao, OperacaoLetraCambio):
            operacao.tipo_investimento = 'Letra de Câmbio'
            operacao.valor_total = operacao.quantidade 
        if isinstance(operacao, OperacaoLetraCredito):
            operacao.tipo_investimento = 'LCI/LCA'
            operacao.valor_total = operacao.quantidade
        if isinstance(operacao, OperacaoCDB_RDB):
            operacao.tipo_investimento = 'CDB/RDB'
            operacao.valor_total = operacao.quantidade 
        if isinstance(operacao, OperacaoCRI_CRA):
            operacao.tipo_investimento = 'CRI/CRA'
            operacao.valor_total = operacao.quantidade * operacao.preco_unitario
        if isinstance(operacao, OperacaoCriptomoeda):
            operacao.tipo_investimento = 'Criptomoeda'
            operacao.valor_total = operacao.quantidade * operacao.preco_unitario
        if isinstance(operacao, OperacaoDebenture):
            operacao.tipo_investimento = u'Debênture'
            operacao.valor_total = operacao.quantidade * operacao.preco_unitario
        if isinstance(operacao, OperacaoFundoInvestimento):
            operacao.tipo_investimento = 'Fundo de investimento'
            operacao.valor_total = operacao.valor
        if isinstance(operacao, Investimento):
            operacao.tipo_investimento = 'Outros investimentos'
            operacao.valor_total = operacao.quantidade
    
    return TemplateResponse(request, 'listar_operacoes.html', {'operacoes': operacoes})

@adiciona_titulo_descricao('Painel geral', 'Traz informações gerais sobre a posição atual em cada tipo de investimento')
def painel_geral(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'painel_geral.html', {'ultimas_operacoes': list(), 'investimentos_atuais': {}, 
                                                               'proventos_acoes_recebidos_hoje': list(),
                                                               'proventos_fiis_recebidos_hoje': list(), 'proventos_acoes_a_receber': list(),
                                                               'proventos_fiis_a_receber': list(), 'proventos_acoes_futuros': list(),
                                                               'proventos_fiis_futuros': list(),'graf_rendimentos_mensal_lci_lca': list(),
                                                               'total_atual_investimentos': 0, 'graf_rendimentos_mensal_cdb_rdb': list(),
                                                               'graf_rendimentos_mensal_td': list(), 'graf_rendimentos_mensal_debentures': list(),
                                                               'graf_rendimentos_mensal_cri_cra': list()})
    # Guardar data atual
    data_atual = datetime.datetime.now()
    
    ultimas_operacoes = buscar_ultimas_operacoes(investidor, 5) 
    
    investimentos_atuais = list()
    investimentos = buscar_totais_atuais_investimentos(investidor) 
    for chave, valor in investimentos.items():
        investimento = Object()
        investimento.valor = valor
        investimento.descricao = chave
        if chave == 'Ações':
            investimento.link = 'acoes:bh:painel_bh'
        elif chave == 'CDB/RDB':
            investimento.link = 'cdb_rdb:painel_cdb_rdb'
        elif chave == 'CRI/CRA':
            investimento.link = 'cri_cra:painel_cri_cra'
        elif chave == 'Criptomoedas':
            investimento.link = 'criptomoeda:painel_criptomoeda'
        elif chave == 'Debêntures':
            investimento.link = 'debentures:painel_debenture'
        elif chave == 'FII':
            investimento.link = 'fii:painel_fii'
        elif chave == 'Fundos de Inv.':
            investimento.link = 'fundo_investimento:painel_fundo_investimento'
        elif chave == 'Letras de Câmbio':
            investimento.link = 'lcambio:painel_lc'
        elif chave == 'LCI/LCA':
            investimento.link = 'lci_lca:painel_lci_lca'
        elif chave == 'Outros inv.':
            investimento.link = 'outros_investimentos:painel_outros_invest'
        elif chave == 'Tesouro Direto':
            investimento.link = 'tesouro_direto:painel_td'
            
        investimentos_atuais.append(investimento)
#         print chave, investimento.link
    # Pegar total atual de todos os investimentos
    total_atual_investimentos = sum([valor for valor in investimentos.values()])
    
    # Ordenar proventos a receber e separar por grupos
    # Proventos a receber com data EX já passada
    proventos_a_receber = buscar_proventos_a_receber(investidor)
    
    # Recebidos hoje
    proventos_acoes_recebidos_hoje = [provento for provento in proventos_a_receber if isinstance(provento, Provento) and provento.data_pagamento == data_atual.date()]
    proventos_acoes_recebidos_hoje.sort(key=lambda provento: provento.acao)
    
    proventos_fiis_recebidos_hoje = [provento for provento in proventos_a_receber if isinstance(provento, ProventoFII) and provento.data_pagamento == data_atual.date()]
    proventos_fiis_recebidos_hoje.sort(key=lambda provento: provento.fii)
    
    # A receber futuramente
    proventos_acoes_a_receber = [provento for provento in proventos_a_receber if isinstance(provento, Provento) and provento.data_pagamento > data_atual.date()]
    proventos_acoes_a_receber.sort(key=lambda provento: provento.data_pagamento)
    
    proventos_fiis_a_receber = [provento for provento in proventos_a_receber if isinstance(provento, ProventoFII) and provento.data_pagamento > data_atual.date()]
    proventos_fiis_a_receber.sort(key=lambda provento: provento.data_pagamento)
    
    # Proventos a receber com data EX ainda não passada
    proventos_futuros = buscar_proventos_a_receber_data_ex_futura(request.user.investidor)
    proventos_acoes_futuros = [provento for provento in proventos_futuros if isinstance(provento, Provento)]
    proventos_acoes_futuros.sort(key=lambda provento: provento.data_ex)
    
    proventos_fiis_futuros = [provento for provento in proventos_futuros if isinstance(provento, ProventoFII)]
    proventos_fiis_futuros.sort(key=lambda provento: provento.data_ex)
    
    return TemplateResponse(request, 'painel_geral.html', {'ultimas_operacoes': ultimas_operacoes, 'investimentos_atuais': investimentos_atuais, 
                                                           'proventos_acoes_recebidos_hoje': proventos_acoes_recebidos_hoje,
                                                           'proventos_fiis_recebidos_hoje': proventos_fiis_recebidos_hoje, 'proventos_acoes_a_receber': proventos_acoes_a_receber,
                                                           'proventos_fiis_a_receber': proventos_fiis_a_receber, 'proventos_acoes_futuros': proventos_acoes_futuros,
                                                           'proventos_fiis_futuros': proventos_fiis_futuros, 'total_atual_investimentos': total_atual_investimentos})

@login_required
def acumulado_mensal_painel_geral(request):
    if request.is_ajax():
        investidor = request.user.investidor
        data_atual = datetime.date.today()
        
        # Buscar dados para o acumulado mensal
        ultimo_dia_mes_anterior = data_atual.replace(day=1) - datetime.timedelta(days=1)
        acumulado_mensal_atual = sum(calcular_rendimentos_ate_data(investidor, data_atual).values()) - sum(calcular_rendimentos_ate_data(investidor, ultimo_dia_mes_anterior).values())
                                                                                              
        ultimo_dia_mes_antes_do_anterior = ultimo_dia_mes_anterior.replace(day=1) - datetime.timedelta(days=1)         
        acumulado_mensal_anterior = sum(calcular_rendimentos_ate_data(investidor, ultimo_dia_mes_anterior).values()) - sum(calcular_rendimentos_ate_data(investidor, ultimo_dia_mes_antes_do_anterior).values())
        
        return HttpResponse(json.dumps(render_to_string('utils/acumulado_mensal_painel_geral.html', {'acumulado_mensal_atual': acumulado_mensal_atual,
                                                     'acumulado_mensal_anterior': acumulado_mensal_anterior})), content_type = "application/json")   

    return HttpResponse(json.dumps({}), content_type = "application/json")   

@login_required
def grafico_renda_fixa_painel_geral(request):
    if request.is_ajax():
        investidor = request.user.investidor
        data_atual = datetime.datetime.now()
        
        qtd_ultimos_dias = 15
        # Guardar valores totais
        diario_cdb_rdb = {}
        diario_cri_cra = {}
        diario_debentures = {}
        diario_lc = {}
        diario_lci_lca = {}
        diario_td = {}
        
        total_lc_dia_anterior = float(sum(calcular_valor_lc_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
#         total_lci_lca_dia_anterior = float(sum(calcular_valor_lci_lca_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
        operacoes_vigentes_lci_lca = list(buscar_operacoes_vigentes_ate_data_lci_lca(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()))
        for operacao in operacoes_vigentes_lci_lca:
            operacao.atual = calcular_valor_operacao_lci_lca_ate_dia(operacao, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date(), False, False)
        total_lci_lca_dia_anterior = float(sum([operacao.atual.quantize(Decimal('0.01'), ROUND_DOWN) for operacao in operacoes_vigentes_lci_lca]))
#         total_cdb_rdb_dia_anterior = float(sum(calcular_valor_cdb_rdb_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
        operacoes_vigentes_cdb_rdb = list(buscar_operacoes_vigentes_ate_data_cdb_rdb(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()))
        for operacao in operacoes_vigentes_cdb_rdb:
            operacao.atual = calcular_valor_operacao_cdb_rdb_ate_dia(operacao, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date(), False, False)
        total_cdb_rdb_dia_anterior = float(sum([operacao.atual.quantize(Decimal('0.01'), ROUND_DOWN) for operacao in operacoes_vigentes_cdb_rdb]))
        total_td_dia_anterior = float(sum(calcular_valor_td_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
        total_debentures_dia_anterior = float(sum(calcular_valor_debentures_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
        total_cri_cra_dia_anterior = float(sum(calcular_valor_cri_cra_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values())) \
            + float(calcular_rendimentos_cri_cra_ate_data(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()))
        
        operacoes_lc_no_periodo = OperacaoLetraCambio.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
        operacoes_lci_lca_no_periodo = OperacaoLetraCredito.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
        operacoes_cdb_rdb_no_periodo = OperacaoCDB_RDB.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
        operacoes_td_no_periodo = OperacaoTitulo.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
        operacoes_debenture_no_periodo = OperacaoDebenture.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
        operacoes_cri_cra_no_periodo = OperacaoCRI_CRA.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], cri_cra__investidor=investidor)
        
        for dia in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))]:
            dia = dia.date()
            diario_cdb_rdb[dia] = 0
            diario_lc[dia] = 0
            diario_lci_lca[dia] = 0
            diario_td[dia] = 0
            diario_debentures[dia] = 0
            diario_cri_cra[dia] = 0
            
            if dia.weekday() < 5 and not verificar_feriado_bovespa(dia):
                # Letra de Câmbio
                total_lc = float(sum(calcular_valor_lc_ate_dia(investidor, dia).values()))
    #                     print '(%s) %s - %s =' % (dia, total_lc, total_lc_dia_anterior), total_lc - total_lc_dia_anterior
                # Removendo operações do dia
                diario_lc[dia] += total_lc - total_lc_dia_anterior - float(operacoes_lc_no_periodo.filter(data=dia, tipo_operacao='C').aggregate(soma_compras=Sum('quantidade'))['soma_compras'] or Decimal(0)) + \
                    float(sum([calcular_valor_venda_lc(operacao_venda) for operacao_venda in operacoes_lc_no_periodo.filter(data=dia, tipo_operacao='V')]))
                total_lc_dia_anterior = total_lc
                
                # Letra de Crédito
#                 total_lci_lca = float(sum(calcular_valor_lci_lca_ate_dia(investidor, dia).values()))
                valor_compra_no_dia = 0
                valor_venda_no_dia = 0
                if operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='C').exists():
                    operacoes_no_periodo = operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='C')
                    for operacao_no_periodo in operacoes_no_periodo:
                        operacao_no_periodo.atual = calcular_valor_operacao_lci_lca_ate_dia(operacao_no_periodo, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date(), False, False)
                    # Adicionar operações de compra e calcular o valor total das compras
                    operacoes_vigentes_lci_lca.extend(list(operacoes_no_periodo))
                    valor_compra_no_dia += float(operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='C').aggregate(soma_compras=Sum('quantidade'))['soma_compras'] or Decimal(0))
                if operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='V').exists():
                    for operacao in operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='V'):
                        for operacao_compra in operacoes_vigentes_lci_lca:
                            if operacao_compra.id == operacao.operacao_compra_relacionada().id:
                                # Calcular valor da venda arredondado no dia
                                valor_venda = operacao_compra.atual * (operacao.quantidade / operacao_compra.quantidade)
                                valor_venda_no_dia += float(valor_venda.quantize(Decimal('0.01'), ROUND_DOWN))
                                # Subtrair valores da operação de compra
                                operacao_compra.quantidade -= operacao.quantidade
                                operacao_compra.atual -= valor_venda
                                if operacao_compra.quantidade == 0:
                                    operacoes_vigentes_lci_lca.remove(operacao_compra)
                                break
                        
                operacoes_vigentes_lci_lca = atualizar_operacoes_lci_lca_no_periodo(operacoes_vigentes_lci_lca, dia, dia)
                total_lci_lca = float(sum([operacao.atual.quantize(Decimal('0.01'), ROUND_DOWN) for operacao in operacoes_vigentes_lci_lca]))
    #                     print '(%s) %s - %s =' % (dia, total_lci_lca, total_lci_lca_dia_anterior), total_lci_lca - total_lci_lca_dia_anterior
                # Removendo operações do dia
#                 diario_lci_lca[dia] += total_lci_lca - total_lci_lca_dia_anterior - float(operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='C').aggregate(soma_compras=Sum('quantidade'))['soma_compras'] or Decimal(0)) + \
#                     float(sum([calcular_valor_venda_lci_lca(operacao_venda) for operacao_venda in operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='V')]))
                diario_lci_lca[dia] += total_lci_lca - total_lci_lca_dia_anterior - valor_compra_no_dia + valor_venda_no_dia
                total_lci_lca_dia_anterior = total_lci_lca
                
                # CDB / RDB
#                 total_cdb_rdb = float(sum(calcular_valor_cdb_rdb_ate_dia(investidor, dia).values()))
                valor_compra_no_dia = 0
                valor_venda_no_dia = 0
                if operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='C').exists():
                    operacoes_no_periodo = operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='C')
                    for operacao_no_periodo in operacoes_no_periodo:
                        operacao_no_periodo.atual = calcular_valor_operacao_cdb_rdb_ate_dia(operacao_no_periodo, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date(), False, False)
                    # Adicionar operações de compra e calcular o valor total das compras
                    operacoes_vigentes_cdb_rdb.extend(list(operacoes_no_periodo))
                    valor_compra_no_dia += float(operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='C').aggregate(soma_compras=Sum('quantidade'))['soma_compras'] or Decimal(0))
                if operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='V').exists():
                    for operacao in operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='V'):
                        for operacao_compra in operacoes_vigentes_cdb_rdb:
                            if operacao_compra.id == operacao.operacao_compra_relacionada().id:
                                # Calcular valor da venda arredondado no dia
                                valor_venda = operacao_compra.atual * (operacao.quantidade / operacao_compra.quantidade)
                                valor_venda_no_dia += float(valor_venda.quantize(Decimal('0.01'), ROUND_DOWN))
                                # Subtrair valores da operação de compra
                                operacao_compra.quantidade -= operacao.quantidade
                                operacao_compra.atual -= valor_venda
                                if operacao_compra.quantidade == 0:
                                    operacoes_vigentes_cdb_rdb.remove(operacao_compra)
                                break
                        
                operacoes_vigentes_cdb_rdb = atualizar_operacoes_cdb_rdb_no_periodo(operacoes_vigentes_cdb_rdb, dia, dia)
                total_cdb_rdb = float(sum([operacao.atual.quantize(Decimal('0.01'), ROUND_DOWN) for operacao in operacoes_vigentes_cdb_rdb]))
    #                     print '(%s) %s - %s =' % (dia, total_cdb_rdb, total_cdb_rdb_dia_anterior), total_cdb_rdb - total_cdb_rdb_dia_anterior
                # Removendo operações do dia
#                 diario_cdb_rdb[dia] += total_cdb_rdb - total_cdb_rdb_dia_anterior - float(operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='C').aggregate(soma_compras=Sum('quantidade'))['soma_compras'] or Decimal(0)) + \
#                     float(sum([calcular_valor_venda_cdb_rdb(operacao_venda) for operacao_venda in operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='V')]))
                diario_cdb_rdb[dia] += total_cdb_rdb - total_cdb_rdb_dia_anterior - valor_compra_no_dia + valor_venda_no_dia
                total_cdb_rdb_dia_anterior = total_cdb_rdb
                
                # Tesouro Direto
                total_td = float(sum(calcular_valor_td_ate_dia(investidor, dia).values()))
                # Removendo operações do dia
                operacoes_do_dia = operacoes_td_no_periodo.filter(data=dia).aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('preco_unitario')*F('quantidade')),
                                When(tipo_operacao='V', then=F('preco_unitario')*F('quantidade')*-1),
                                output_field=DecimalField())))['total'] or Decimal(0)
                diario_td[dia] += total_td - total_td_dia_anterior - float(operacoes_do_dia)
                total_td_dia_anterior = total_td
                
                # Debêntures
                total_debentures = float(sum(calcular_valor_debentures_ate_dia(investidor, dia).values()))
                # Removendo operações do dia
                operacoes_do_dia = operacoes_debenture_no_periodo.filter(data=dia).aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('preco_unitario')*F('quantidade') + F('taxa')),
                                When(tipo_operacao='V', then=F('preco_unitario')*F('quantidade')*-1 - F('taxa')),
                                output_field=DecimalField())))['total'] or Decimal(0)
                diario_debentures[dia] += total_debentures - total_debentures_dia_anterior - float(operacoes_do_dia)
                total_debentures_dia_anterior = total_debentures
                
                # CRI / CRA
                total_cri_cra = float(sum(calcular_valor_cri_cra_ate_dia(investidor, dia).values())) + float(calcular_rendimentos_cri_cra_ate_data(investidor, dia))
                # Removendo operações do dia
                operacoes_do_dia = operacoes_cri_cra_no_periodo.filter(data=dia).aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('preco_unitario')*F('quantidade') + F('taxa')),
                                When(tipo_operacao='V', then=F('preco_unitario')*F('quantidade')*-1 - F('taxa')),
                                output_field=DecimalField())))['total'] or Decimal(0)
                diario_cri_cra[dia] += total_cri_cra - total_cri_cra_dia_anterior - float(operacoes_do_dia)
                total_cri_cra_dia_anterior = total_cri_cra
                    
        graf_rendimentos_mensal_cdb_rdb = [[str(calendar.timegm(data.replace(hour=3).timetuple()) * 1000), diario_cdb_rdb[data.date()] ] \
                                   for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ] 
        graf_rendimentos_mensal_lci_lca = [[str(calendar.timegm(data.replace(hour=6).timetuple()) * 1000), diario_lci_lca[data.date()] ] \
                                   for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ] 
        graf_rendimentos_mensal_td = [[str(calendar.timegm(data.replace(hour=9).timetuple()) * 1000), diario_td[data.date()] ] \
                                   for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ] 
        graf_rendimentos_mensal_debentures = [[str(calendar.timegm(data.replace(hour=12).timetuple()) * 1000), diario_debentures[data.date()] ] \
                                   for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ] 
        graf_rendimentos_mensal_cri_cra = [[str(calendar.timegm(data.replace(hour=15).timetuple()) * 1000), diario_cri_cra[data.date()] ] \
                                   for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ]
        graf_rendimentos_mensal_lc = [[str(calendar.timegm(data.replace(hour=18).timetuple()) * 1000), diario_lc[data.date()] ] \
                                   for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ]

        return HttpResponse(json.dumps({'sucesso': True, 'graf_rendimentos_mensal_cdb_rdb': graf_rendimentos_mensal_cdb_rdb,
                                        'graf_rendimentos_mensal_lci_lca': graf_rendimentos_mensal_lci_lca, 'graf_rendimentos_mensal_td': graf_rendimentos_mensal_td,
                                        'graf_rendimentos_mensal_debentures': graf_rendimentos_mensal_debentures,
                                        'graf_rendimentos_mensal_cri_cra': graf_rendimentos_mensal_cri_cra,
                                        'graf_rendimentos_mensal_lc': graf_rendimentos_mensal_lc}), content_type = "application/json")   

    return HttpResponse(json.dumps({'sucesso': False}), content_type = "application/json")   

@login_required
def prox_vencimentos_painel_geral(request):
    if request.is_ajax():
        investidor = request.user.investidor
        data_atual = datetime.date.today()
#         data_30_dias = data_atual + datetime.timedelta(days=3000)
        
        # Verificar próximos vencimentos de renda fixa
        prox_vencimentos = list()
        
        limite_vencimentos = 10
        
        # Taxa DI final
        data_final, taxa_final = HistoricoTaxaDI.objects.all().values_list('data', 'taxa').order_by('-data')[0]
        
        # CDB/RDB
        # Buscar cdbs vigentes
        operacoes_atuais = buscar_operacoes_vigentes_ate_data_cdb_rdb(investidor)
        for operacao in operacoes_atuais[:limite_vencimentos]:
#             if operacao.data_vencimento() >= data_atual and operacao.data_vencimento() <= data_30_dias:
            if operacao.data_vencimento() >= data_atual:
                operacao.tipo_investimento = u'CDB/RDB'
                operacao.nome = operacao.cdb_rdb.nome
                
                # Valor inicial
                operacao.valor_inicial = operacao.qtd_disponivel_venda 
                 
                # Valor vencimento
                operacao.quantidade = operacao.valor_inicial
                operacao.taxa = operacao.porcentagem()
                operacao.atual = calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data_atual)
                qtd_dias_uteis_ate_vencimento = qtd_dias_uteis_no_periodo(data_final + datetime.timedelta(days=1), operacao.data_vencimento())
                # Se prefixado apenas pegar rendimento de 1 dia
                if operacao.cdb_rdb.eh_prefixado():
                    operacao.valor_vencimento = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa, qtd_dias_uteis_ate_vencimento)
                elif operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
                    # Considerar rendimento do dia anterior
                    operacao.valor_vencimento = calcular_valor_atualizado_com_taxas_di({taxa_final: qtd_dias_uteis_ate_vencimento},
                                                         operacao.atual, operacao.taxa)
                str_auxiliar = str(operacao.valor_vencimento.quantize(Decimal('.0001')))
                operacao.valor_vencimento = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                 
                prox_vencimentos.append(operacao)
                
        # CRI/CRA
#         for operacao in OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, cri_cra__data_vencimento__range=[data_atual, data_30_dias]) \
        for operacao in OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, cri_cra__data_vencimento__gte=data_atual, tipo_operacao='C') \
        .select_related('cri_cra').order_by('data')[:limite_vencimentos]:
            operacao.tipo_investimento = u'CRI/CRA'
            operacao.nome = operacao.cri_cra.nome
            
            # Valor inicial
            operacao.valor_inicial = operacao.quantidade * operacao.preco_unitario
            
            # Valor vencimento
            operacao.valor_vencimento = operacao.quantidade * calcular_valor_um_cri_cra_na_data(operacao.cri_cra, operacao.cri_cra.data_vencimento, True)
            
            prox_vencimentos.append(operacao)
                
        # Debênture
#         for operacao in OperacaoDebenture.objects.filter(investidor=investidor, debenture__data_vencimento__range=[data_atual, data_30_dias]) \
        for operacao in OperacaoDebenture.objects.filter(investidor=investidor, debenture__data_vencimento__gte=data_atual, tipo_operacao='C') \
        .select_related('debenture').order_by('data')[:limite_vencimentos]:
            operacao.tipo_investimento = u'Debênture'
            operacao.nome = operacao.debenture.codigo
            
            # Valor inicial
            operacao.valor_inicial = operacao.quantidade * operacao.preco_unitario
            
            # TODO Valor vencimento
            operacao.valor_vencimento = simular_valor_na_data(operacao.debenture_id, operacao.debenture.data_vencimento)
            
            prox_vencimentos.append(operacao)
                
        # LC
        # Buscar lcs vigentes
        operacoes_atuais = buscar_operacoes_vigentes_ate_data_lc(investidor)
        # Verificar datas de vencimento, pegar nos próximos 30 dias
        for operacao in operacoes_atuais[:limite_vencimentos]:
#             if operacao.data_vencimento() >= data_atual and operacao.data_vencimento() <= data_30_dias:
            if operacao.data_vencimento() >= data_atual:
                operacao.tipo_investimento = u'Letra de Câmbio'
                operacao.nome = operacao.lc.nome
                
                # Valor inicial
                operacao.valor_inicial = operacao.qtd_disponivel_venda 
                
                # Calcular valor vencimento
                operacao.quantidade = operacao.valor_inicial
                operacao.taxa = operacao.porcentagem()
                operacao.atual = calcular_valor_operacao_lc_ate_dia(operacao, data_atual)
                qtd_dias_uteis_ate_vencimento = qtd_dias_uteis_no_periodo(data_final + datetime.timedelta(days=1), operacao.data_vencimento())
                # Se prefixado apenas pegar rendimento de 1 dia
                if operacao.lc.eh_prefixado():
                    operacao.valor_vencimento = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa, qtd_dias_uteis_ate_vencimento)
                elif operacao.lc.tipo_rendimento == LetraCambio.LC_DI:
                    # Considerar rendimento do dia anterior
                    operacao.valor_vencimento = calcular_valor_atualizado_com_taxas_di({taxa_final: qtd_dias_uteis_ate_vencimento},
                                                         operacao.atual, operacao.taxa)
                str_auxiliar = str(operacao.valor_vencimento.quantize(Decimal('.0001')))
                operacao.valor_vencimento = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                
                prox_vencimentos.append(operacao)
                
        # LCI/LCA
        # Buscar lcis vigentes
        operacoes_atuais = buscar_operacoes_vigentes_ate_data_lci_lca(investidor)
        # Verificar datas de vencimento, pegar nos próximos 30 dias
        for operacao in operacoes_atuais[:limite_vencimentos]:
#             if operacao.data_vencimento() >= data_atual and operacao.data_vencimento() <= data_30_dias:
            if operacao.data_vencimento() >= data_atual:
                operacao.tipo_investimento = u'LCI/LCA'
                operacao.nome = operacao.letra_credito.nome
                
                # Valor inicial
                operacao.valor_inicial = operacao.qtd_disponivel_venda 
                
                # Calcular valor vencimento
                operacao.quantidade = operacao.valor_inicial
                operacao.taxa = operacao.porcentagem()
                operacao.atual = calcular_valor_operacao_lci_lca_ate_dia(operacao, data_atual)
                qtd_dias_uteis_ate_vencimento = qtd_dias_uteis_no_periodo(data_final + datetime.timedelta(days=1), operacao.data_vencimento())
                # Se prefixado apenas pegar rendimento de 1 dia
                if operacao.letra_credito.tipo_rendimento == LetraCredito.LCI_LCA_PREFIXADO:
                    operacao.valor_vencimento = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa, qtd_dias_uteis_ate_vencimento)
                elif operacao.letra_credito.tipo_rendimento == LetraCredito.LCI_LCA_DI:
                    # Considerar rendimento do dia anterior
                    operacao.valor_vencimento = calcular_valor_atualizado_com_taxas_di({taxa_final: qtd_dias_uteis_ate_vencimento},
                                                         operacao.atual, operacao.taxa)
                str_auxiliar = str(operacao.valor_vencimento.quantize(Decimal('.0001')))
                operacao.valor_vencimento = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                
                prox_vencimentos.append(operacao)
                
        # Título
#         for operacao in OperacaoTitulo.objects.filter(investidor=investidor, titulo__data_vencimento__range=[data_atual, data_30_dias]) \
        for operacao in OperacaoTitulo.objects.filter(investidor=investidor, titulo__data_vencimento__gte=data_atual, tipo_operacao='C') \
        .select_related('titulo').order_by('data')[:limite_vencimentos]:
            operacao.tipo_investimento = u'Tesouro Direto'
            operacao.nome = operacao.titulo.nome()
            
            # Valor inicial
            operacao.valor_inicial = operacao.quantidade * operacao.preco_unitario
            
            # Valor vencimento
            operacao.valor_vencimento = operacao.titulo.valor_vencimento()
            
            prox_vencimentos.append(operacao)
                
        # Ordenar pela data de vencimento
        prox_vencimentos.sort(key=lambda x: x.data_vencimento())
        
        # Filtrar apenas os 10 próximos
        prox_vencimentos = prox_vencimentos[:limite_vencimentos]

        # Preencher dados gerais para operações a serem mostradas        
        for operacao in prox_vencimentos:
            operacao.decorrido_percentual = (float((data_atual - operacao.data).days) / (operacao.data_vencimento() - operacao.data).days) * 100
        
        return HttpResponse(json.dumps(render_to_string('utils/prox_vencimentos_rf_painel_geral.html', {'prox_vencimentos': prox_vencimentos})), 
                            content_type = "application/json")   
    else:
        return HttpResponse(json.dumps({}), content_type = "application/json")  
        

@login_required
def rendimento_medio_painel_geral(request):
    if request.is_ajax():
        investidor = request.user.investidor
        data_atual = datetime.date.today()
        
        # Verificar rendimento médio do investidor
        data_primeira_operacao = investidor.buscar_data_primeira_operacao()
        if data_primeira_operacao and data_primeira_operacao < data_atual:
            data_inicial = max(data_primeira_operacao, data_atual - datetime.timedelta(days=365))
            
            # Buscar totais
            total_atual_investimentos = Decimal(request.GET.get('total_atual'))
            total_inicial_investimentos = sum([valor for valor in buscar_totais_atuais_investimentos(request.user.investidor, data_inicial).values()])
            
            # Rendimento é a variação do valor total dos investimentos, menos o que foi investido 
            #(saldo inicial - saldo final + transferencias entrando - transferencias saindo)
            rendimento = total_atual_investimentos - total_inicial_investimentos
            rendimento += sum([(divisao.saldo() - divisao.saldo(data_inicial)) for divisao in Divisao.objects.filter(investidor=investidor)])
            rendimento += (TransferenciaEntreDivisoes.objects.filter(data__range=[data_inicial, data_atual], divisao_cedente__investidor=investidor, divisao_recebedora__isnull=True).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
                - (TransferenciaEntreDivisoes.objects.filter(data__range=[data_inicial, data_atual], divisao_recebedora__investidor=request.user.investidor, divisao_cedente__isnull=True).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
            # Calcular rendimento percentual
            rendimento_percentual = (rendimento / (total_inicial_investimentos or 1))
            # Calcular média mensal e anual
            rendimento_medio_mensal = 100 * (pow((1 + rendimento_percentual), Decimal(30) / (data_atual - data_inicial).days) - 1)
            rendimento_medio_anual = 100 * (pow((1 + rendimento_medio_mensal/100), 12) - 1)
            
        else:
            rendimento = 0
            rendimento_medio_mensal = 0
            rendimento_medio_anual = 0
            data_inicial = data_atual
        return HttpResponse(json.dumps(render_to_string('utils/rendimento_medio_painel_geral.html', {'rendimento': rendimento, 'data_inicial': data_inicial, 
                                                     'rendimento_medio_mensal': rendimento_medio_mensal, 'rendimento_medio_anual': rendimento_medio_anual})), 
                            content_type = "application/json")   
    else:
        return HttpResponse(json.dumps({}), content_type = "application/json")  

@adiciona_titulo_descricao('Sobre o site', 'O que é? Para quê?')
def sobre(request):
    form = ContatoForm()
    if request.method == 'POST':
        form = ContatoForm(data=request.POST)

        if form.is_valid():
            form_nome = request.POST.get(
                'nome'
            , '')
            form_email = request.POST.get(
                'email'
            , '')
            form_conteudo = request.POST.get('conteudo', '')
            
            texto = u'E-mail enviado por %s <%s>\n%s' % (form_nome, form_email, form_conteudo)
            html_message = loader.render_to_string(
                        'email_contato.html',
                        {
                            'nome': form_nome,
                            'email': form_email,
                            'conteudo':  form_conteudo,
                        }
                    )
            send_mail('Contato de %s' % (form_nome), texto, form_email, ['suporte@bagofgold.com.br'], html_message=html_message)
            messages.success(request, u'E-mail enviado com sucesso')
            # Limpar form
            form = ContatoForm()
    return TemplateResponse(request, 'sobre.html', {'form_contato': form})