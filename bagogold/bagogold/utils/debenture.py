# -*- coding: utf-8 -*-
from bagogold.bagogold.models.debentures import OperacaoDebenture, \
    HistoricoValorDebenture
from bagogold.bagogold.models.divisoes import DivisaoOperacaoDebenture
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, When, F
from django.db.models.fields import DecimalField


def calcular_qtd_debentures_ate_dia(investidor, dia):
    """ 
    Calcula a quantidade de Debêntures até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de Debentures {id_debenture: qtd}
    """
    
#     operacoes = OperacaoDebenture.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).order_by('data')
#     
#     qtd_debenture = {}
#     
#     for operacao in operacoes:
#         if operacao.debenture.codigo not in qtd_debenture:
#             qtd_debenture[operacao.debenture.codigo] = 0
#             
#         # Verificar se se trata de compra ou venda
#         if operacao.tipo_operacao == 'C':
#             qtd_debenture[operacao.debenture.codigo] += operacao.quantidade
#             
#         elif operacao.tipo_operacao == 'V':
#             qtd_debenture[operacao.debenture.codigo] -= operacao.quantidade
#         
#     return qtd_debenture
    qtd_debenture = dict(OperacaoDebenture.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).values('debenture') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('debenture', 'total').exclude(total=0))
            
    return qtd_debenture

def calcular_qtd_debentures_ate_dia_por_codigo(investidor, dia, codigo):
    """ 
    Calcula a quantidade de Debêntures até dia determinado para um codigo determinado
    Parâmetros: Investidor
                Código da Debênture
                Dia final
    Retorno: Quantidade de Debêntures para o codigo determinado
    """
    operacoes = OperacaoDebenture.objects.filter(debenture__codigo=codigo, data__lte=dia, investidor=investidor).exclude(data__isnull=True).order_by('data')
    qtd_debenture = 0
    
    for item in operacoes:
        # Verificar se se trata de compra ou venda
        if item.tipo_operacao == 'C':
            qtd_debenture += item.quantidade
            
        elif item.tipo_operacao == 'V':
            qtd_debenture -= item.quantidade
        
    return qtd_debenture

def calcular_qtd_debentures_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de Debentures até dia determinado
    Parâmetros: Id da divisão
                Dia final
    Retorno: Quantidade de Debentures {codigo: qtd}
    """
    operacoes_divisao_id = DivisaoOperacaoDebenture.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes = OperacaoDebenture.objects.filter(id__in=operacoes_divisao_id).exclude(data__isnull=True).order_by('data')
    
    qtd_debenture = {}
    
    for operacao in operacoes:
        # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
        operacao.quantidade = DivisaoOperacaoDebenture.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
        
        if operacao.debenture.codigo not in qtd_debenture:
            qtd_debenture[operacao.debenture.codigo] = 0
            
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            qtd_debenture[operacao.debenture.codigo] += operacao.quantidade
            
        elif operacao.tipo_operacao == 'V':
            qtd_debenture[operacao.debenture.codigo] -= operacao.quantidade
        
    for key, item in qtd_debenture.items():
        if qtd_debenture[key] == 0:
            del qtd_debenture[key]
            
    return qtd_debenture

def calcular_valor_debentures_ate_dia(investidor, dia):
    """ 
    Calcula o valor das debêntures do investidor até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Valor das debêntures {debenture_id: valor_da_data}
    """
    
    qtd_debentures = calcular_qtd_debentures_ate_dia(investidor, dia)
    
    for debenture_id in qtd_debentures.keys():
        print dia, HistoricoValorDebenture.objects.filter(data__lte=dia, debenture__id=debenture_id).order_by('-data')[0].valor_total()
        qtd_debentures[debenture_id] = HistoricoValorDebenture.objects.filter(data__lte=dia, debenture__id=debenture_id).order_by('-data')[0].valor_total() * qtd_debentures[debenture_id]
        
    return qtd_debentures