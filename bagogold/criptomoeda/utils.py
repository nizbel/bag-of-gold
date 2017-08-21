# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda
from bagogold.criptomoeda.models import OperacaoCriptomoeda
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
    qtd_moedas = dict(OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).values('criptomoeda') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('criptomoeda', 'total').exclude(total=0))
    
    return qtd_moedas

def calcular_qtd_moedas_ate_dia_por_criptomoeda(investidor, moeda_id, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de moedas até dia determinado para uma criptomoeda determinada
    Parâmetros: Investidor
                ID da Criptomoeda
                Dia final
    Retorno: Quantidade de moedas para a criptomoeda determinada
    """
    qtd_moedas = OperacaoCriptomoeda.objects.filter(investidor=investidor, criptomoeda__id=moeda_id, data__lte=dia).exclude(data__isnull=True) \
        .aggregate(qtd_moedas=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField())))['qtd_moedas'] or 0
        
    return qtd_moedas

def calcular_qtd_moedas_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de moedas até dia determinado
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

#                                                                 data__range=[historico_fundo.data + datetime.timedelta(days=1), dia]).order_by('-data')[0].valor_cota()
#                 Dia final
#                 valor_cota = OperacaoCriptomoeda.objects.filter(fundo_investimento__id=fundo_id, investidor=investidor, 
#                 valor_cota = historico_fundo.valor_cota
#             else:
#             historico_fundo = HistoricoValorCotas.objects.filter(fundo_investimento__id=fundo_id).order_by('-data')[0]
#             if investidor and OperacaoCriptomoeda.objects.filter(fundo_investimento__id=fundo_id, investidor=investidor, data__range=[historico_fundo.data + datetime.timedelta(days=1), dia]).exists():
#             valor_cota = OperacaoCriptomoeda.objects.filter(fundo_investimento__id=fundo_id, investidor=investidor, data__lte=dia).order_by('-data')[0].valor_cota()
#         else:
#         if HistoricoValorCotas.objects.filter(fundo_investimento__id=fundo_id, data__lte=dia).exists():
#         valor_fundos[fundo_id] = valor_cota * fundos[fundo_id]
#     """
#     """ 
#     Calcula a o valor das moedas do investidor até dia determinado
#     Parâmetros: Investidor
#     Retorno: Valor por fundo {fundo_id: valor (em reais)}
#     for fundo_id in fundos.keys():
#     fundos = calcular_qtd_moedas_ate_dia(investidor, dia)
#     return valor_fundos
#     valor_fundos = {}
# def calcular_valor_fundos_investimento_ate_dia(investidor, dia=datetime.date.today()):