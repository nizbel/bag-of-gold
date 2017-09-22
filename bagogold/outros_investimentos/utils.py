# -*- coding: utf-8 -*-
from bagogold.outros_investimentos.models import Investimento, Amortizacao
from django.db.models.aggregates import Sum
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