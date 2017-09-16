# -*- coding: utf-8 -*-
import datetime
from bagogold.outros_investimentos.models import Investimento

def calcular_valor_outros_investimentos_ate_data(investidor, data=datetime.date.today()):
    """
    Calcula o valor investido em outros investimentos até determinada data
    Parâmetros: Investidor
                Data
    Retorno: Valores por investimento {investimento_id: valor}
    """
    investimentos = dict(Investimento.objects.filter(investidor=investidor, data__lte=data, data_encerramento__isnull=True).values_list('id', 'quantidade'))
    
    # TODO remover amortizações
    
    return investimentos