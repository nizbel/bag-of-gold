# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII, \
    ValorDiarioFII, HistoricoFII
import datetime


def calcular_qtd_fiis_ate_dia(dia):
    """ 
    Calcula a quantidade de FIIs até dia determinado
    Parâmetros: Dia final
    Retorno: Quantidade de FIIs {ticker: qtd}
    """
    
    operacoes = OperacaoFII.objects.filter(data__lte=dia).exclude(data__isnull=True).order_by('data')
    
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

def calcular_qtd_fiis_ate_dia_por_ticker(dia, ticker):
    """ 
    Calcula a quantidade de FIIs até dia determinado para um ticker determinado
    Parâmetros: Ticker do FII
                Dia final
    Retorno: Quantidade de FIIs para o ticker determinado
    """
    
    operacoes = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia).exclude(data__isnull=True).order_by('data')
    qtd_fii = 0
    
    for item in operacoes:
        if isinstance(item, OperacaoFII): 
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
    operacoes_divisao_id = DivisaoOperacaoFII.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes = OperacaoFII.objects.filter(id__in=operacoes_divisao_id).exclude(data__isnull=True).order_by('data')
    
    qtd_fii = {}
    
    for operacao in operacoes:
        # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
        operacao.quantidade = DivisaoOperacaoFII.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
        
        if operacao.fii.ticker not in qtd_fii:
            qtd_fii[operacao.fii.ticker] = 0
            
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            qtd_fii[operacao.fii.ticker] += operacao.quantidade
            
        elif operacao.tipo_operacao == 'V':
            qtd_fii[operacao.fii.ticker] -= operacao.quantidade
        
    return qtd_fii

def calcular_rendimento_proventos_fii_12_meses(fii):
    """ 
    Calcula o rendimento percentual dos proventos nos últimos 12 meses para um FII
    Parâmetros: FII
    Retorno: Rendimento percentual
    """
    total_proventos = 0
    data_1_ano_atras = datetime.date.today() - datetime.timedelta(days=365)
    # Calcular media de proventos dos ultimos 6 recebimentos
    proventos = ProventoFII.objects.filter(fii=fii, data_ex__gt=data_1_ano_atras).order_by('data_ex')
    if len(proventos) == 0:
        return 0
    for provento in proventos:
        total_proventos += provento.valor_unitario
        
    # Pegar valor atual dos FIIs
    preenchido = False
    try:
        valor_diario_mais_recente = ValorDiarioFII.objects.filter(fii=fii).order_by('-data_hora')
        if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
            valor_atual = valor_diario_mais_recente[0].preco_unitario
            percentual_retorno = (total_proventos/valor_atual) * 100
            preenchido = True
    except:
        preenchido = False
    if (not preenchido):
        # Pegar último dia util com negociação da ação para calculo do patrimonio
        try:
            valor_atual = HistoricoFII.objects.filter(fii=fii).order_by('-data')[0].preco_unitario
            # Percentual do retorno sobre o valor do fundo
            percentual_retorno = (total_proventos/valor_atual) * 100
        except:
            valor_atual = 0
            # Percentual do retorno sobre o valor do fundo
            percentual_retorno = 0
    
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