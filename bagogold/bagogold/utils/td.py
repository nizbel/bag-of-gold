# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo, Titulo, HistoricoTitulo
from decimal import Decimal
from django.db.models import Sum, Case, When, IntegerField, F
from itertools import chain
from operator import attrgetter
import calendar
import datetime


def calcular_imposto_venda_td(dias, valor_venda, rendimento):
    """
    Calcula a quantidade de imposto (IR + IOF) devida de acordo com a quantidade de dias
    Parâmetros: quantidade de dias corridos, valor total da venda, rendimento
    Retorno: quantidade de imposto
    """
    if dias < 30:
        return min(0.01 * valor_venda + 0.225 * rendimento, rendimento)
    if dias <= 180:
        return 0.225 * rendimento
    elif dias <= 360:
        return 0.2 * rendimento
    elif dias <= 720:
        return 0.175 * rendimento
    else: 
        return 0.15 * rendimento

def criar_data_inicio_titulos():
    """
    Percorre todos os títulos disponíveis para configurar sua data de início como a primeira data em que
    há informação de histórico
    """
    for titulo in Titulo.objects.all():
        titulo.data_inicio = HistoricoTitulo.objects.filter(titulo=titulo).order_by('data')[0].data
        titulo.save()

def quantidade_titulos_ate_dia(titulo_id, dia):
    """ 
    Calcula a quantidade de títulos até dia determinado
    Parâmetros: ID do título
                Dia final
    Retorno: Quantidade de títulos
    """
    
    operacoes = OperacaoTitulo.objects.filter(titulo__id=titulo_id, data__lte=dia).exclude(data__isnull=True).order_by('data')
    
    qtd_titulos = 0
    
    for item in operacoes:
        # Verificar se se trata de compra ou venda
        if item.tipo_operacao == 'C':
            qtd_titulos += item.quantidade
            
        elif item.tipo_operacao == 'V':
            qtd_titulos -= item.quantidade
        
    return qtd_titulos