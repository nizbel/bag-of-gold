# -*- coding: utf-8 -*-
from decimal import Decimal
from django.db.models import Q
import datetime

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
