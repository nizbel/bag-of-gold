# -*- coding: utf-8 -*-

def calcular_valor_outros_investimentos_ate_data(investidor, data=datetime.date.today()):
    """
    Calcula o valor investido em outros investimentos até determinada data
    Parâmetros: Investidor
                Data
    Retorno: Valores por investimento {investimento_id: valor}
    """
    return