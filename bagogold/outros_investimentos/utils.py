# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoInvestimento
from bagogold.outros_investimentos.models import Investimento, Amortizacao
from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
import datetime

def calcular_valor_outros_investimentos_ate_data(investidor, data=datetime.date.today()):
    """
    Calcula o valor investido em outros investimentos até determinada data
    Parâmetros: Investidor
                Data
    Retorno: Valores por investimento {investimento_id: valor}
    """
    investimentos = dict(Investimento.objects.filter(investidor=investidor, data__lte=data, data_encerramento__isnull=True).values_list('id', 'quantidade'))

    amortizacoes = dict(Amortizacao.objects.filter(investimento__investidor=investidor, data__lte=data, investimento__data_encerramento__isnull=True) \
                        .values('investimento__id').annotate(total_amortizado=Sum('valor')).values_list('investimento__id', 'total_amortizado'))
    
    qtd_investimentos = { k: investimentos.get(k, 0) - amortizacoes.get(k, 0) for k in set(investimentos) | set(amortizacoes) \
                         if investimentos.get(k, 0) - amortizacoes.get(k, 0) > 0 }
    return qtd_investimentos

def calcular_valor_outros_investimentos_ate_data_por_investimento(investimento, data=datetime.date.today()):
    """
    Calcula o valor investido em um investimento até determinada data
    Parâmetros: Investimento
                Data
    Retorno: Quantidade investida
    """
    total_investido = investimento.quantidade - (Amortizacao.objects.filter(investimento=investimento, data__lte=data) \
        .aggregate(total_amortizado=Sum('valor'))['total_amortizado'] or 0)
        
    return total_investido

def calcular_valor_outros_investimentos_ate_data_por_divisao(divisao, data=datetime.date.today()):
    """
    Calcula o valor dos invesimentos de uma divisão até determinada data
    Parâmetros: Divisão
                Data
    Retorno: Valores por investimento {investimento_id: valor}
    """
    investimentos = DivisaoInvestimento.objects.filter(divisao=divisao, investimento__data__lte=data, 
                                                            investimento__data_encerramento__isnull=True) \
                    .annotate(qtd_total=F('investimento__quantidade')).values_list('investimento__id', 'quantidade', 'qtd_total')
    
    dict_divisao = {investimento[0]: investimento[1] for investimento in investimentos}
    dict_investimentos = {investimento[0]: investimento[2] for investimento in investimentos}

    amortizacoes = dict(Amortizacao.objects.filter(data__lte=data, investimento__in=dict_investimentos.keys()) \
                        .values('investimento__id').annotate(total_amortizado=Sum('valor')).values_list('investimento__id', 'total_amortizado'))
    
    qtd_investimentos = { k: (dict_divisao.get(k, 0) - (amortizacoes.get(k, 0) * dict_divisao.get(k, 0) / dict_investimentos.get(k, 0))).quantize(Decimal('0.01')) \
                         for k in set(dict_investimentos) | set(amortizacoes) | set(dict_divisao) \
                         if (dict_divisao.get(k, 0) - (amortizacoes.get(k, 0) * dict_divisao.get(k, 0) / dict_investimentos.get(k, 0))).quantize(Decimal('0.01')) > 0 }
    return qtd_investimentos