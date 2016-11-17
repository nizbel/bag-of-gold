# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD
from bagogold.bagogold.models.td import OperacaoTitulo, Titulo, HistoricoTitulo, \
    ValorDiarioTitulo, HistoricoIPCA
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
from decimal import Decimal
from django.db.models import Q
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
    Parâmetros: Dia final
    Retorno: Quantidade de títulos {titulo_id: qtd}
    """
    
    operacoes = OperacaoTitulo.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).order_by('data')
    
    qtd_titulos = {}
    
    for item in operacoes:
        print qtd_titulos
        # Verificar se se trata de compra ou venda
        if item.tipo_operacao == 'C':
            if item.titulo.id not in qtd_titulos:
                qtd_titulos[item.titulo.id] = item.quantidade
            else:
                qtd_titulos[item.titulo.id] += item.quantidade
            
        elif item.tipo_operacao == 'V':
            qtd_titulos[item.titulo.id] -= item.quantidade
    
    # Remover títulos com quantidade 0
    for titulo_id in qtd_titulos.keys():
        if qtd_titulos[titulo_id] == 0:
            del qtd_titulos[titulo_id]
    
    return qtd_titulos

def quantidade_titulos_ate_dia_por_titulo(investidor, titulo_id, dia):
    """ 
    Calcula a quantidade de títulos do investidor até dia determinado
    Parâmetros: ID do título
                Dia final
    Retorno: Quantidade de títulos
    """
    
    operacoes = OperacaoTitulo.objects.filter(investidor=investidor, titulo__id=titulo_id, data__lte=dia).exclude(data__isnull=True).order_by('data')
    
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
            
    for key, item in qtd_titulos.items():
        if qtd_titulos[key] == 0:
            del qtd_titulos[key]
        
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