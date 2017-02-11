# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD
from bagogold.bagogold.models.td import OperacaoTitulo, Titulo, HistoricoTitulo, \
    ValorDiarioTitulo, HistoricoIPCA
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
from decimal import Decimal
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, When, F
from django.db.models.fields import DecimalField
import calendar
import datetime


def calcular_valor_acumulado_ipca(data_base, data_final=datetime.date.today()):
    """
    Calcula o valor acumulado do IPCA desde a data base, até uma data final
    Parâmetros: Data base
                Data final
    Retorno: Taxa total acumulada
    """
    ipca_inicial = HistoricoIPCA.objects.get(mes=data_base.month, ano=data_base.year)
    # Calcular quantidade de dias em que a taxa inicial foi aplicada
    ultimo_dia_mes_inicial = datetime.date(data_base.year, data_base.month, calendar.monthrange(data_base.year, data_base.month)[1])
    qtd_dias = (min(data_final, ultimo_dia_mes_inicial) - data_base).days
    # Transformar taxa mensal em diaria
    ipca_inicial_diario = pow(1 + ipca_inicial.valor/Decimal(100), Decimal(1)/30) - 1
    # Iniciar IPCA do periodo com o acumulado nos dias
    ipca_periodo = pow(1 + ipca_inicial_diario, qtd_dias) - 1
#     print 'IPCA inicial:', ipca_periodo
    # TODO melhorar isso
    for mes_historico in HistoricoIPCA.objects.filter((Q(mes__gt=ipca_inicial.mes) & Q(ano=ipca_inicial.ano)) | \
                                                      Q(ano__gt=ipca_inicial.ano)).filter(ano__lte=data_final.year).order_by('ano', 'mes'):
        if datetime.date(mes_historico.ano, mes_historico.mes, calendar.monthrange(mes_historico.ano, mes_historico.mes)[1]) <= data_final:
#             print mes_historico.ano, '/', mes_historico.mes, '->', ipca_periodo, (1 + mes_historico.valor/Decimal(100))
            ipca_periodo = (1 + ipca_periodo) * (1 + mes_historico.valor/Decimal(100)) - 1
    return ipca_periodo

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
    """
    Percorre todos os títulos disponíveis para configurar sua data de início como a primeira data em que
    há informação de histórico
    """
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
    compras = list(OperacaoTitulo.objects.filter(investidor=investidor, data__lte=dia, tipo_operacao='C').exclude(data__isnull=True).values('titulo') \
        .annotate(total=Sum('quantidade')))
    vendas = list(OperacaoTitulo.objects.filter(investidor=investidor, data__lte=dia, tipo_operacao='V').exclude(data__isnull=True).values('titulo') \
        .annotate(total=Sum('quantidade')*-1))
    
    qtd_titulos = {}
    for titulo_qtd in (compras + vendas):
        if titulo_qtd['titulo'] not in qtd_titulos.keys():
            qtd_titulos[titulo_qtd['titulo']] = titulo_qtd['total']
        else:
            qtd_titulos[titulo_qtd['titulo']] += titulo_qtd['total']

    for key in qtd_titulos.keys():
        if qtd_titulos[key] == 0:
            del qtd_titulos[key]
            
    return qtd_titulos

def quantidade_titulos_ate_dia_por_titulo(investidor, titulo_id, dia):
    """ 
    Calcula a quantidade de títulos do investidor até dia determinado
    Parâmetros: ID do título
                Dia final
    Retorno: Quantidade de títulos
    """
    compras = OperacaoTitulo.objects.filter(investidor=investidor, titulo__id=titulo_id, data__lte=dia, tipo_operacao='C').exclude(data__isnull=True) \
        .aggregate(total_compras=Sum('quantidade'))['total_compras'] or Decimal(0)
    vendas = OperacaoTitulo.objects.filter(investidor=investidor, titulo__id=titulo_id, data__lte=dia, tipo_operacao='V').exclude(data__isnull=True) \
        .aggregate(total_vendas=Sum('quantidade'))['total_vendas'] or Decimal(0)
    
    qtd_titulos = compras - vendas
    
    return qtd_titulos

def calcular_qtd_titulos_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de títulos até dia determinado por divisão
    Parâmetros: Dia final
                ID da divisão
    Retorno: Quantidade de títulos {titulo_id: qtd}
    """
    qtd_titulos = {}
    operacoes_divisao = list(DivisaoOperacaoTD.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).annotate(titulo=F('operacao__titulo')) \
        .values('titulo') \
        .annotate(qtd_soma=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))))
        
    for titulo_qtd in operacoes_divisao:
        if titulo_qtd['titulo'] not in qtd_titulos.keys():
            qtd_titulos[titulo_qtd['titulo']] = titulo_qtd['qtd_soma']
        else:
            qtd_titulos[titulo_qtd['titulo']] += titulo_qtd['qtd_soma']
            
    for key in qtd_titulos.keys():
        if qtd_titulos[key] == 0:
            del qtd_titulos[key]
    
    return qtd_titulos

def calcular_valor_td_ate_dia(investidor, dia):
    """ 
    Calcula o valor dos títulos do investidor até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Valor dos títulos {titulo_id: valor_da_data}
    """
    
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