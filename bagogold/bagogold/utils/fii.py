# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII
from bagogold.bagogold.models.fii import OperacaoFII


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