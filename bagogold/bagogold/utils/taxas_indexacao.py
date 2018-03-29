# -*- coding: utf-8 -*-
from decimal import Decimal

def calcular_valor_atualizado_com_taxa_di(taxa_do_dia, valor_atual, operacao_taxa):
    """
    Calcula o valor atualizado de uma operação vinculada ao DI, a partir da taxa DI do dia
    Parâmetros: Taxa DI do dia
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa DI
    """
    return ((pow((Decimal(1) + taxa_do_dia/100), Decimal(1)/Decimal(252)) - Decimal(1)) * operacao_taxa/100 + Decimal(1)) * valor_atual

def calcular_valor_atualizado_com_taxa_prefixado(valor_atual, operacao_taxa, qtd_dias=1):
    """
    Calcula o valor atualizado de uma operação em renda fixa prefixada, a partir da quantidade de dias do período
    Parâmetros: Valor atual da operação
                Taxa da operação
                Quantidade de dias
    Retorno: Valor atualizado com a taxa de um dia prefixado
    """
    return pow((Decimal(1) + operacao_taxa/100), Decimal(qtd_dias)/Decimal(252)) * valor_atual

def calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor_atual, operacao_taxa):
    """
    Calcula o valor atualizado de uma operação vinculada ao DI, a partir das taxa DI dos dias
    Parâmetros: Taxas DI dos dias {taxa(Decimal): quantidade_de_dias}
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa DI
    """
    taxa_acumulada = 1
    for taxa_do_dia in taxas_dos_dias.keys():
        taxa_acumulada *= pow(((pow((Decimal(1) + taxa_do_dia/100), Decimal(1)/Decimal(252)) - Decimal(1)) * operacao_taxa/100 + Decimal(1)), taxas_dos_dias[taxa_do_dia])
    return taxa_acumulada * valor_atual

def calcular_valor_atualizado_com_taxas_di_e_juros(taxas_dos_dias, valor_atual, operacao_taxa, juros):
    """
    Calcula o valor atualizado de uma operação vinculada ao DI, a partir das taxa DI dos dias
    Parâmetros: Taxas DI dos dias {taxa(Decimal): quantidade_de_dias}
                Valor atual da operação
                Taxa da operação
                Juros (percentual ao ano)
    Retorno: Valor atualizado com a taxa DI
    """
    taxa_acumulada = 1
    juros = Decimal(juros)
    for taxa_do_dia in taxas_dos_dias.keys():
        taxa_acumulada *= pow((((pow((Decimal(1) + taxa_do_dia/100), Decimal(1)/Decimal(252)) - Decimal(1)) * operacao_taxa/100 + Decimal(1)) * \
                               pow((Decimal(1) + juros/100), Decimal(1)/Decimal(252))), taxas_dos_dias[taxa_do_dia])
    return taxa_acumulada * valor_atual

def calcular_valor_atualizado_com_taxa_selic(taxa_do_dia, valor_atual):
    """
    Calcula o valor atualizado de uma operação vinculada ao Selic, a partir da taxa Selic do dia
    Parâmetros: Taxa Selic do dia
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa Selic
    """
    return taxa_do_dia * valor_atual

def calcular_valor_atualizado_com_taxas_selic(taxas_dos_dias, valor_atual):
    """
    Calcula o valor atualizado de uma operação vinculada ao Selic, a partir das taxa Selic dos dias
    Parâmetros: Taxas Selic dos dias {taxa(Decimal): quantidade_de_dias}
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa Selic
    """
    taxa_acumulada = 1
    for taxa_do_dia in taxas_dos_dias.keys():
        taxa_acumulada *= pow(taxa_do_dia, taxas_dos_dias[taxa_do_dia])
    return taxa_acumulada * valor_atual
