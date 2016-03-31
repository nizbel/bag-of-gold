# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD
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

def quantidade_titulos_ate_dia_por_titulo(titulo_id, dia):
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

def calcular_qtd_titulos_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de títulos até dia determinado por divisão
    Parâmetros: Dia final
                ID da divisão
    Retorno: Quantidade de títulos {titulo_id: qtd}
    """
    operacoes_divisao_id = DivisaoOperacaoTD.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes = OperacaoTitulo.objects.filter(id__in=operacoes_divisao_id).exclude(data__isnull=True).order_by('data')
    
    qtd_titulos = {}
    
    for operacao in operacoes:
        # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
        operacao.quantidade = DivisaoOperacaoTD.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
        
        if operacao.titulo.id not in qtd_titulos:
            qtd_titulos[operacao.titulo.id] = 0
            
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            qtd_titulos[operacao.titulo.id] += operacao.quantidade
            
        elif operacao.tipo_operacao == 'V':
            qtd_titulos[operacao.titulo.id] -= operacao.quantidade
        
    return qtd_titulos