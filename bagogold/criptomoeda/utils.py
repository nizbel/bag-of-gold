# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda
from bagogold.criptomoeda.models import OperacaoCriptomoeda, \
    TransferenciaCriptomoeda
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When
from django.db.models.fields import DecimalField
import datetime

def calcular_qtd_moedas_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de moedas até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de moedas por fundo {moeda_id: qtd}
    """
    # Pega primeiro moedas operadas
    qtd_moedas1 = dict(OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia).values('criptomoeda') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('criptomoeda', 'total').exclude(total=0))
    
    # Moedas utilizadas, sem taxas
    qtd_moedas2 = dict(OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, operacaocriptomoedamoeda__isnull=False,
                                                          operacaocriptomoedataxa__isnull=True) \
                       .annotate(moeda_utilizada=F('operacaocriptomoedamoeda__criptomoeda')).values('moeda_utilizada') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade') * F('preco_unitario') *-1),
                            When(tipo_operacao='V', then=F('quantidade') * F('preco_unitario')),
                            output_field=DecimalField()))).values_list('moeda_utilizada', 'total').exclude(total=0))
    
    # Moedas utilizadas, com taxas
    qtd_moedas3 = dict(OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, operacaocriptomoedamoeda__isnull=False,
                                                          operacaocriptomoedataxa__isnull=False) \
                       .annotate(moeda_utilizada=F('operacaocriptomoedamoeda__criptomoeda')).values('moeda_utilizada') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', \
                  # Para compras, verificar se taxa está na moeda comprada ou na utilizada
                  then=Case(When(operacaocriptomoedataxa__moeda=F('criptomoeda'), 
                                 then=(F('quantidade') + F('operacaocriptomoedataxa__valor')) * F('preco_unitario') *-1),
                            When(operacaocriptomoedataxa__moeda=F('operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('quantidade') * F('preco_unitario') *-1 - F('operacaocriptomoedataxa__valor')))),
                                 When(tipo_operacao='V', \
                  # Para vendas, verificar se a taxa está na moeda vendida ou na utilizada
                  then=Case(When(operacaocriptomoedataxa__moeda=F('criptomoeda'), 
                                 then=(F('quantidade') - F('operacaocriptomoedataxa__valor')) * F('preco_unitario')),
                            When(operacaocriptomoedataxa__moeda=F('operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('quantidade') * F('preco_unitario') - F('operacaocriptomoedataxa__valor')))),
                        output_field=DecimalField()))).values_list('moeda_utilizada', 'total').exclude(total=0))
    
    # Transferências, remover taxas
    qtd_moedas4 = dict(TransferenciaCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, moeda__isnull=False).values('moeda') \
        .annotate(total=Sum(F('taxa')*-1)).values_list('moeda', 'total').exclude(total=0))
    
    qtd_moedas = { k: qtd_moedas1.get(k, 0) + qtd_moedas2.get(k, 0) + qtd_moedas3.get(k, 0) + qtd_moedas4.get(k, 0) \
                   for k in set(qtd_moedas1) | set(qtd_moedas2) | set(qtd_moedas3) | set(qtd_moedas4) }
    
    return qtd_moedas

def calcular_qtd_moedas_ate_dia_por_criptomoeda(investidor, moeda_id, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de moedas até dia determinado para uma criptomoeda
    Parâmetros: Investidor
                ID da Criptomoeda
                Dia final
    Retorno: Quantidade de moedas para a criptomoeda determinada
    """
    # Pega primeiro moedas operadas
    qtd_moedas = OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, criptomoeda__id=moeda_id) \
        .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField())))['total'] or 0
    
    # Moedas utilizadas, sem taxas
    qtd_moedas += OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, operacaocriptomoedamoeda__criptomoeda__id=moeda_id,
                                                          operacaocriptomoedataxa__isnull=True) \
        .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade') * F('preco_unitario') *-1),
                            When(tipo_operacao='V', then=F('quantidade') * F('preco_unitario')),
                            output_field=DecimalField())))['total'] or 0
    
    # Moedas utilizadas, com taxas
    qtd_moedas += OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, operacaocriptomoedamoeda__criptomoeda__id=moeda_id,
                                                          operacaocriptomoedataxa__isnull=False) \
        .aggregate(total=Sum(Case(When(tipo_operacao='C', \
                  # Para compras, verificar se taxa está na moeda comprada ou na utilizada
                  then=Case(When(operacaocriptomoedataxa__moeda=F('criptomoeda'), 
                                 then=(F('quantidade') + F('operacaocriptomoedataxa__valor')) * F('preco_unitario') *-1),
                            When(operacaocriptomoedataxa__moeda=F('operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('quantidade') * F('preco_unitario') *-1 - F('operacaocriptomoedataxa__valor')))),
                                 When(tipo_operacao='V', \
                  # Para vendas, verificar se a taxa está na moeda vendida ou na utilizada
                  then=Case(When(operacaocriptomoedataxa__moeda=F('criptomoeda'), 
                                 then=(F('quantidade') - F('operacaocriptomoedataxa__valor')) * F('preco_unitario')),
                            When(operacaocriptomoedataxa__moeda=F('operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('quantidade') * F('preco_unitario') - F('operacaocriptomoedataxa__valor')))),
                        output_field=DecimalField())))['total'] or 0
    
    # Transferências, remover taxas
    qtd_moedas += TransferenciaCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, moeda__id=moeda_id) \
        .aggregate(total=Sum(F('taxa')*-1))['total'] or 0
        
    return qtd_moedas

def calcular_qtd_moedas_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de moedas até dia determinado para uma divisão
    Parâmetros: Dia final
                Id da divisão
    Retorno: Quantidade de moedas {moeda: qtd}
    """
    operacoes_divisao_id = DivisaoOperacaoCriptomoeda.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes = OperacaoCriptomoeda.objects.filter(id__in=operacoes_divisao_id).exclude(data__isnull=True).order_by('data')
    
    qtd_moedas = {}
    
    for operacao in operacoes:
        # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
        operacao.quantidade = DivisaoOperacaoCriptomoeda.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
        
        if operacao.fundo_investimento.id not in qtd_moedas:
            qtd_moedas[operacao.fundo_investimento.id] = 0
            
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            qtd_moedas[operacao.fundo_investimento.id] += operacao.quantidade
            
        elif operacao.tipo_operacao == 'V':
            qtd_moedas[operacao.fundo_investimento.id] -= operacao.quantidade
        
    for key, item in qtd_moedas.items():
        if qtd_moedas[key] == 0:
            del qtd_moedas[key]
            
    return qtd_moedas

def calcular_valor_criptomoeda_atual(criptomoeda):
    pass

def calcular_valor_criptomoedas_atual(lista_criptomoedas):
    pass