# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII, \
    ValorDiarioFII, HistoricoFII
from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When
from django.db.models.fields import DecimalField
from itertools import chain
from operator import attrgetter
import datetime

def calcular_poupanca_prov_fii_ate_dia(investidor, dia):
    """
    Calcula a quantidade de proventos provisionada até dia determinado para FII
    Parâmetros: Investidor
                Dia da posição de proventos
    Retorno: Quantidade provisionada no dia
    """
    operacoes = OperacaoFII.objects.filter(investidor=investidor,data__lte=dia).order_by('data')
    
    # Remover valores repetidos
    fiis = list(set(operacoes.values_list('fii', flat=True)))

    proventos = ProventoFII.objects.filter(data_ex__lte=dia, fii__in=fiis).order_by('data_ex')
    for provento in proventos:
        provento.data = provento.data_ex
     
    lista_conjunta = sorted(chain(proventos, operacoes),
                            key=attrgetter('data'))
    
    total_proventos = Decimal(0)
    
    # Guarda as cotas correntes para o calculo do patrimonio
    fiis = {}
    # Calculos de patrimonio e gasto total
    for item_lista in lista_conjunta:      
        if item_lista.fii.ticker not in fiis.keys():
            fiis[item_lista.fii.ticker] = 0
            
        # Verifica se é uma compra/venda
        if isinstance(item_lista, OperacaoFII):   
            # Verificar se se trata de compra ou venda
            if item_lista.tipo_operacao == 'C':
                if item_lista.utilizou_proventos():
                    total_proventos -= item_lista.qtd_proventos_utilizada()
                fiis[item_lista.fii.ticker] += item_lista.quantidade
                
            elif item_lista.tipo_operacao == 'V':
                fiis[item_lista.fii.ticker] -= item_lista.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item_lista, ProventoFII):
            if item_lista.data_pagamento <= datetime.date.today() and fiis[item_lista.fii.ticker] > 0:
                total_recebido = fiis[item_lista.fii.ticker] * item_lista.valor_unitario
                total_proventos += total_recebido
                    
    return total_proventos.quantize(Decimal('0.01'))

def calcular_poupanca_prov_fii_ate_dia_por_divisao(dia, divisao):
    """
    Calcula a quantidade de proventos provisionada até dia determinado para uma divisão para FII
    Parâmetros: Dia da posição de proventos
                Divisão escolhida
    Retorno: Quantidade provisionada no dia
    """
    operacoes_divisao = DivisaoOperacaoFII.objects.filter(divisao=divisao, operacao__data__lte=dia).values_list('operacao__id', flat=True)
    
    operacoes = OperacaoFII.objects.filter(id__in=operacoes_divisao).order_by('data')

    proventos = ProventoFII.objects.filter(data_ex__lte=dia).order_by('data_ex')
    for provento in proventos:
        provento.data = provento.data_ex
     
    lista_conjunta = sorted(chain(operacoes, proventos),
                            key=attrgetter('data'))
    
    total_proventos = Decimal(0)
    
    # Guarda as ações correntes para o calculo do patrimonio
    fiis = {}
    # Calculos de patrimonio e gasto total
    for item_lista in lista_conjunta:      
        if item_lista.fii.ticker not in fiis.keys():
            fiis[item_lista.fii.ticker] = 0
            
        # Verifica se é uma compra/venda
        if isinstance(item_lista, OperacaoFII):   
            # Verificar se se trata de compra ou venda
            if item_lista.tipo_operacao == 'C':
                if item_lista.utilizou_proventos():
                    total_proventos -= item_lista.qtd_proventos_utilizada()
                fiis[item_lista.fii.ticker] += item_lista.quantidade
                
            elif item_lista.tipo_operacao == 'V':
                fiis[item_lista.fii.ticker] -= item_lista.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item_lista, ProventoFII):
            if item_lista.data_pagamento <= datetime.date.today() and fiis[item_lista.fii.ticker] > 0:
                total_recebido = fiis[item_lista.fii.ticker] * item_lista.valor_unitario
                total_proventos += total_recebido
                    
    return total_proventos.quantize(Decimal('0.01'))

def calcular_qtd_fiis_ate_dia(investidor, dia):
    """ 
    Calcula a quantidade de FIIs até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de FIIs {ticker: qtd}
    """
    
    operacoes = OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).order_by('data')
    
    qtd_fii = {}
    
    for operacao in operacoes:
        if operacao.fii.ticker not in qtd_fii:
            qtd_fii[operacao.fii.ticker] = 0
            
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            qtd_fii[operacao.fii.ticker] += operacao.quantidade
            
        elif operacao.tipo_operacao == 'V':
            qtd_fii[operacao.fii.ticker] -= operacao.quantidade
        
    return qtd_fii

def calcular_qtd_fiis_ate_dia_por_ticker(investidor, dia, ticker):
    """ 
    Calcula a quantidade de FIIs até dia determinado para um ticker determinado
    Parâmetros: Investidor
                Ticker do FII
                Dia final
    Retorno: Quantidade de FIIs para o ticker determinado
    """
    operacoes = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True).order_by('data')
    qtd_fii = 0
    
    for item in operacoes:
        # Verificar se se trata de compra ou venda
        if item.tipo_operacao == 'C':
            qtd_fii += item.quantidade
            
        elif item.tipo_operacao == 'V':
            qtd_fii -= item.quantidade
        
    return qtd_fii

def calcular_qtd_fiis_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de FIIs até dia determinado
    Parâmetros: Id da divisão
                Dia final
    Retorno: Quantidade de FIIs {ticker: qtd}
    """
    qtd_fii = dict(DivisaoOperacaoFII.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).annotate(ticker=F('operacao__fii__ticker')) \
        .values('ticker').annotate(qtd=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('ticker', 'qtd').exclude(qtd=0))
    
    return qtd_fii

def calcular_rendimento_proventos_fii_12_meses(fii):
    """ 
    Calcula o rendimento percentual dos proventos nos últimos 12 meses para um FII
    Parâmetros: FII
    Retorno: Rendimento percentual
    """
    total_proventos = Decimal(0)
    data_1_ano_atras = datetime.date.today() - datetime.timedelta(days=365)
    # Calcular media de proventos dos ultimos 6 recebimentos
    proventos = ProventoFII.objects.filter(fii=fii, data_ex__gt=data_1_ano_atras).order_by('data_ex')
    if len(proventos) == 0:
        return Decimal(0)
    for provento in proventos:
        total_proventos += provento.valor_unitario
        
    # Pegar valor atual dos FIIs
    preenchido = False
    try:
        valor_diario_mais_recente = ValorDiarioFII.objects.filter(fii=fii).order_by('-data_hora')
        if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
            valor_atual = valor_diario_mais_recente[0].preco_unitario
            percentual_retorno = (total_proventos/valor_atual) * Decimal(100)
            preenchido = True
    except:
        preenchido = False
    if (not preenchido):
        # Pegar último dia util com negociação da ação para calculo do patrimonio
        try:
            valor_atual = HistoricoFII.objects.filter(fii=fii).order_by('-data')[0].preco_unitario
            # Percentual do retorno sobre o valor do fundo
            percentual_retorno = (total_proventos/valor_atual) * Decimal(100)
        except:
            valor_atual = Decimal(0)
            # Percentual do retorno sobre o valor do fundo
            percentual_retorno = Decimal(0)
    
    return percentual_retorno

def calcular_variacao_percentual_fii_por_periodo(fii, periodo_inicio, periodo_fim):
    """
    Calcula a variação percentual de um FII em determinado período
    Parâmetros: FII
                Data inicial do período
                Data final do período
    Retorno: Variação percentual
    """
    try:
        valor_inicial = HistoricoFII.objects.filter(fii=fii, data__lte=periodo_inicio).order_by('-data')[0].preco_unitario
        valor_final = HistoricoFII.objects.filter(fii=fii, data__lte=periodo_fim).order_by('-data')[0].preco_unitario
    except:
        return 0
    
    return (valor_final - valor_inicial) / valor_final * 100