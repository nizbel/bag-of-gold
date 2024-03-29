# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
from bagogold.tesouro_direto.models import OperacaoTitulo, Titulo, \
    HistoricoTitulo, ValorDiarioTitulo
from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, When, F
from django.db.models.fields import DecimalField
import datetime


def calcular_imposto_venda_td(dias, valor_venda, rendimento):
    """
    Calcula a quantidade de imposto (IR + IOF) devida de acordo com a quantidade de dias
    
    Parâmetros: Quantidade de dias corridos
                Valor total da venda
                Rendimento
    Retorno: quantidade de imposto
    """
    if dias < 30:
        valor_iof = calcular_iof_regressivo(dias)
        return min((valor_iof + Decimal(0.225)) * rendimento, rendimento)
    if dias <= 180:
        return Decimal(0.225) * rendimento
    elif dias <= 360:
        return Decimal(0.2) * rendimento
    elif dias <= 720:
        return Decimal(0.175) * rendimento
    else: 
        return Decimal(0.15) * rendimento

def criar_data_inicio_titulos():
    """Percorre todos os títulos disponíveis para configurar sua data de início como a primeira data em que há informação de histórico"""
    for titulo in Titulo.objects.all():
        titulo.data_inicio = HistoricoTitulo.objects.filter(titulo=titulo).order_by('data')[0].data
        titulo.save()

def quantidade_titulos_ate_dia(investidor, dia):
    """ 
    Calcula a quantidade de títulos do investidor até dia determinado
    
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de títulos {titulo_id: qtd}
    """
    qtd_titulos = dict(OperacaoTitulo.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).values('titulo') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('titulo', 'total').exclude(total=0))
            
    return qtd_titulos

def quantidade_titulos_ate_dia_por_titulo(investidor, titulo_id, dia=None):
    """ 
    Calcula a quantidade de títulos do investidor até dia determinado
    
    Parâmetros: ID do título
                Dia final
    Retorno: Quantidade de títulos
    """
    # Preparar data
    if dia == None:
        dia = datetime.date.today()
        
    qtd_titulos = OperacaoTitulo.objects.filter(investidor=investidor, data__lte=dia, titulo__id=titulo_id).exclude(data__isnull=True) \
        .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField())))['total'] or Decimal(0)
    
    return qtd_titulos

def calcular_qtd_titulos_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de títulos até dia determinado para uma divisão
    
    Parâmetros: Dia final
                ID da divisão
    Retorno: Quantidade de títulos {titulo_id: qtd}
    """
    qtd_titulos = dict(DivisaoOperacaoTD.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).annotate(titulo=F('operacao__titulo')) \
        .values('titulo') \
        .annotate(total=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('titulo', 'total').exclude(total=0))
    
    return qtd_titulos

def calcular_qtd_um_titulo_ate_dia_por_divisao(investidor, dia, titulo_id):
    """ 
    Calcula a quantidade de um título específico até dia determinado para cada divisão
    
    Parâmetros: Dia final
                ID da divisão
                ID do título
    Retorno: Quantidade de títulos {divisao_id: qtd}
    """
    qtd_titulos = {}
    operacoes_divisao = list(DivisaoOperacaoTD.objects.filter(operacao__titulo__id=titulo_id, operacao__data__lte=dia, divisao__investidor=investidor) \
        .values('divisao') \
        .annotate(qtd_soma=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))))
        
    for titulo_qtd in operacoes_divisao:
        if titulo_qtd['divisao'] not in qtd_titulos.keys():
            qtd_titulos[titulo_qtd['divisao']] = titulo_qtd['qtd_soma']
        else:
            qtd_titulos[titulo_qtd['divisao']] += titulo_qtd['qtd_soma']
            
    for key in qtd_titulos.keys():
        if qtd_titulos[key] == 0:
            del qtd_titulos[key]
    
    return qtd_titulos

def calcular_valor_td_ate_dia(investidor, dia=None):
    """ 
    Calcula o valor dos títulos do investidor até dia determinado
    
    Parâmetros: Investidor
                Dia final
    Retorno: Valor dos títulos {titulo_id: valor_da_data}
    """
    # Preparar data
    if dia == None:
        dia = datetime.date.today()
    
    qtd_titulos = quantidade_titulos_ate_dia(investidor, dia)
    
    for titulo_id in qtd_titulos.keys():
        qtd_titulos[titulo_id] = HistoricoTitulo.objects.filter(data__lte=dia, titulo__id=titulo_id).order_by('-data')[0].preco_venda * qtd_titulos[titulo_id]
        
    return qtd_titulos

def buscar_data_valor_mais_recente():
    """
    Traz a data para o valor mais recente registrado na base
    
    Retorno: Data ou Data e Hora mais recente
    """
    try:
        atualizacao_mais_recente = ValorDiarioTitulo.objects.latest('data_hora').data_hora
    except:
        atualizacao_mais_recente = HistoricoTitulo.objects.latest('data').data
    return atualizacao_mais_recente