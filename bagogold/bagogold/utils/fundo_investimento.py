# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII,\
    DivisaoOperacaoFundoInvestimento
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII, \
    ValorDiarioFII, HistoricoFII
from decimal import Decimal
from itertools import chain
from operator import attrgetter
import datetime
from bagogold.bagogold.models.fundo_investimento import OperacaoFundoInvestimento

def calcular_qtd_cotas_ate_dia(investidor, dia):
    """ 
    Calcula a quantidade de cotas até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de cotas por fundo {fundo: qtd}
    """
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).order_by('data')
    
    qtd_cotas = {}
    
    for operacao in operacoes:
        if operacao.fundo_investimento.id not in qtd_cotas:
            qtd_cotas[operacao.fundo_investimento.id] = 0
            
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            qtd_cotas[operacao.fundo_investimento.id] += operacao.quantidade
            
        elif operacao.tipo_operacao == 'V':
            qtd_cotas[operacao.fundo_investimento.id] -= operacao.quantidade
        
    return qtd_cotas

def calcular_qtd_cotas_ate_dia_por_fundo(investidor, dia, fundo_id):
    """ 
    Calcula a quantidade de cotas até dia determinado para um fundo determinado
    Parâmetros: Investidor
                ID do Fundo de investimento
                Dia final
    Retorno: Quantidade de cotas para o fundo determinado
    """
    
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor, fii__ticker=ticker, data__lte=dia).exclude(data__isnull=True).order_by('data')
    qtd_cotas = 0
    
    for item in operacoes:
        # Verificar se se trata de compra ou venda
        if item.tipo_operacao == 'C':
            qtd_cotas += item.quantidade
            
        elif item.tipo_operacao == 'V':
            qtd_cotas -= item.quantidade
        
    return qtd_cotas

def calcular_qtd_cotas_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de cotas até dia determinado
    Parâmetros: Id da divisão
                Dia final
    Retorno: Quantidade de cotas {fundo: qtd}
    """
    operacoes_divisao_id = DivisaoOperacaoFundoInvestimento.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes = OperacaoFundoInvestimento.objects.filter(id__in=operacoes_divisao_id).exclude(data__isnull=True).order_by('data')
    
    qtd_cotas = {}
    
    for operacao in operacoes:
        # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
        operacao.quantidade = DivisaoOperacaoFundoInvestimento.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
        
        if operacao.fundo_investimento.id not in qtd_cotas:
            qtd_cotas[operacao.fundo_investimento.id] = 0
            
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            qtd_cotas[operacao.fundo_investimento.id] += operacao.quantidade
            
        elif operacao.tipo_operacao == 'V':
            qtd_cotas[operacao.fundo_investimento.id] -= operacao.quantidade
        
    for key, item in qtd_cotas.items():
        if qtd_cotas[key] == 0:
            del qtd_cotas[key]
            
    return qtd_cotas

