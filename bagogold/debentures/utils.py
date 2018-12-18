# -*- coding: utf-8 -*-
from bagogold.debentures.models import OperacaoDebenture, \
    HistoricoValorDebenture
from bagogold.bagogold.models.divisoes import DivisaoOperacaoDebenture
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, When, F
from django.db.models.fields import DecimalField
import datetime


def calcular_qtd_debentures_ate_dia(investidor, dia):
    """ 
    Calcula a quantidade de Debêntures até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de Debentures {id_debenture: qtd}
    """
    qtd_debenture = dict(OperacaoDebenture.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).values('debenture') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('debenture', 'total').exclude(total=0))
            
    return qtd_debenture

def calcular_qtd_debentures_ate_dia_por_codigo(investidor, dia, codigo):
    """ 
    Calcula a quantidade de Debêntures até dia determinado para um codigo determinado
    Parâmetros: Investidor
                Código da Debênture
                Dia final
    Retorno: Quantidade de Debêntures para o codigo determinado
    """
    operacoes = OperacaoDebenture.objects.filter(debenture__codigo=codigo, data__lte=dia, investidor=investidor).exclude(data__isnull=True).order_by('data')
    qtd_debenture = 0
    
    for item in operacoes:
        # Verificar se se trata de compra ou venda
        if item.tipo_operacao == 'C':
            qtd_debenture += item.quantidade
            
        elif item.tipo_operacao == 'V':
            qtd_debenture -= item.quantidade
        
    return qtd_debenture

def calcular_qtd_debentures_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de Debentures até dia determinado
    Parâmetros: Id da divisão
                Dia final
    Retorno: Quantidade de Debentures {codigo: qtd}
    """
    operacoes_divisao_id = DivisaoOperacaoDebenture.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes = OperacaoDebenture.objects.filter(id__in=operacoes_divisao_id).exclude(data__isnull=True).order_by('data')
    
    qtd_debenture = {}
    
    for operacao in operacoes:
        # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
        operacao.quantidade = DivisaoOperacaoDebenture.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
        
        if operacao.debenture.codigo not in qtd_debenture:
            qtd_debenture[operacao.debenture.codigo] = 0
            
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            qtd_debenture[operacao.debenture.codigo] += operacao.quantidade
            
        elif operacao.tipo_operacao == 'V':
            qtd_debenture[operacao.debenture.codigo] -= operacao.quantidade
        
    for key, item in qtd_debenture.items():
        if qtd_debenture[key] == 0:
            del qtd_debenture[key]
            
    return qtd_debenture

def calcular_valor_debentures_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula o valor das debêntures do investidor até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Valor das debêntures {debenture_id: valor_da_data}
    """
    
    qtd_debentures = calcular_qtd_debentures_ate_dia(investidor, dia)
    
    for debenture_id in qtd_debentures.keys():
        qtd_debentures[debenture_id] = HistoricoValorDebenture.objects.filter(data__lte=dia, debenture__id=debenture_id).order_by('-data')[0].valor_total() * qtd_debentures[debenture_id]
        
    return qtd_debentures

def calcular_valor_debentures_ate_dia_por_divisao(divisao_id, dia=datetime.date.today()):
    """ 
    Calcula o valor das debêntures do investidor até dia determinado para uma divisão
    Parâmetros: ID da divisão
                Dia final
    Retorno: Valor das debêntures {debenture_id: valor_da_data}
    """
    
    qtd_debentures = calcular_qtd_debentures_ate_dia_por_divisao(dia, divisao_id)
    
    for debenture_codigo in qtd_debentures.keys():
        qtd_debentures[debenture_codigo] = HistoricoValorDebenture.objects.filter(data__lte=dia, debenture__codigo=debenture_codigo).order_by('-data')[0].valor_total() * qtd_debentures[debenture_codigo]
        
    return qtd_debentures
    
def simular_valor_na_data(debenture_id, data=None):
    """
    Calcula o valor previsto para debênture em uma data específica
    
    Parâmetros: ID da debênture
                Data
    Retorno: Valor previsto para a debênture
    """
    ultimo_historico = HistoricoValorDebenture.objects.filter(debenture=debenture_id, data__lte=data).order_by('-data')[0]
    ultima_data = ultimo_historico.data
    
    qtd_dias_uteis_ate_data = calcular_qtd_dias_uteis(ultima_data + datetime.timedelta(days=1), data)
    
    if qtd_dias_uteis_ate_data == 0:
        return ultimo_historico.juros + ultimo_historico.valor_nominal
    
    # Verificar com a valorização de datas anteriores
    historicos_anteriores = {}
    if HistoricoValorDebenture.objects.filter(debenture=debenture_id, data__lte=(ultima_data - datetime.timedelta(days=1))).exists():
        historicos_anteriores[1] = HistoricoValorDebenture.objects.filter(debenture=debenture_id, data__lte=(ultima_data - datetime.timedelta(days=1))).order_by('-data')[0]
    if HistoricoValorDebenture.objects.filter(debenture=debenture_id, data__lte=(ultima_data - datetime.timedelta(days=7))).exists():
        historicos_anteriores[7] = HistoricoValorDebenture.objects.filter(debenture=debenture_id, data__lte=(ultima_data - datetime.timedelta(days=7))).order_by('-data')[0]
    if HistoricoValorDebenture.objects.filter(debenture=debenture_id, data__lte=(ultima_data - datetime.timedelta(days=30))).exists():
        historicos_anteriores[30] = HistoricoValorDebenture.objects.filter(debenture=debenture_id, data__lte=(ultima_data - datetime.timedelta(days=30))).order_by('-data')[0]
    
    
    # Calcular de acordo com o índice
    valorizacoes = {'divisor': 0}
    valorizacao_final = 0

    # Verificar valorização nos históricos anteriores
    if 1 in historicos_anteriores and ultimo_historico.juros > historicos_anteriores[1].juros:
        valorizacoes[1] = ultimo_historico.juros / historicos_anteriores[1].juros
        valorizacao_final += valorizacoes[1] * 3
        valorizacoes['divisor'] += 3
        
    if 7 in historicos_anteriores and ultimo_historico.juros > historicos_anteriores[7].juros:
        qtd_dias_uteis_periodo = calcular_qtd_dias_uteis(historicos_anteriores[7].data, ultima_data)
        valorizacoes[7] = ultimo_historico.juros / historicos_anteriores[7].juros
        valorizacoes[7] = (1 + valorizacoes[7]/100) ** (Decimal(1)/qtd_duas_uteis_periodo)
        valorizacao_final += valorizacoes[7] * 2
        valorizacoes['divisor'] += 2
        
    if 30 in historicos_anteriores and ultimo_historico.juros > historicos_anteriores[30].juros:
        qtd_dias_uteis_periodo = calcular_qtd_dias_uteis(historicos_anteriores[30].data, ultima_data)
        valorizacoes[30] = ultimo_historico.juros / historicos_anteriores[30].juros
        valorizacoes[30] = (1 + valorizacoes[30]/100) ** (Decimal(1)/qtd_duas_uteis_periodo)
        valorizacao_final += valorizacoes[30] * 1
        valorizacoes['divisor'] += 1
        
    valorizacao_final = valorizacao_final / valorizacoes['divisor']
    
    return (ultimo_historico.valor_nominal + ultimo_historico.juros) * ((1 + valorizacao_final) ** (qtd_dias_uteis_ate_data))
            