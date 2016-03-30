# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import OperacaoFII



def quantidade_fiis_ate_dia(ticker, dia):
    """ 
    Calcula a quantidade de FIIs até dia determinado
    Parâmetros: Ticker do FII
                Dia final
    Retorno: Quantidade de ações
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

def quantidade_fiis_por_divisao_ate_dia(divisao, ticker, dia):
    """ 
    Calcula a quantidade de FIIs até dia determinado
    Parâmetros: Id da divisão
                Ticker do FII
                Dia final
    Retorno: Quantidade de ações
    """
#     operacoes_divisao_id
    operacoes = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia).exclude(data__isnull=True).order_by('data')
    for operacao in operacoes:
        print 'colocar quantidade da operacao da div'
    
    qtd_fii = 0
    
    for item in operacoes:
        if isinstance(item, OperacaoFII): 
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                qtd_fii += item.quantidade
                
            elif item.tipo_operacao == 'V':
                qtd_fii -= item.quantidade
        
    return qtd_fii