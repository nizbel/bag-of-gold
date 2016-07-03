# -*- coding: utf-8 -*-
from bagogold.bagogold.models.cdb_rdb import OperacaoCDB_RDB, \
    HistoricoPorcentagemCDB_RDB
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC, \
    DivisaoOperacaoCDB_RDB
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa
from decimal import Decimal
from django.db.models import Q
import datetime

def calcular_valor_cdb_rdb_ate_dia(investidor, dia):
    """ 
    Calcula o valor dos CDB/RDB no dia determinado
    Parâmetros: Investidor
                Data final
    Retorno: Valor de cada CDB/RDB na data escolhida {id_letra: valor_na_data, }
    """
    operacoes_queryset = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).exclude(data__gte=dia).order_by('-tipo_operacao', 'data') 
    if len(operacoes_queryset) == 0:
        return {}
    operacoes = list(operacoes_queryset)
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.atual = operacao.quantidade
            operacao.taxa = operacao.porcentagem()
    
    # Pegar data inicial
    data_inicial = operacoes_queryset.order_by('data')[0].data
    
    data_final = HistoricoTaxaDI.objects.filter(data__lte=dia).order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    cdb_rdb = {}
    
    while data_iteracao <= data_final:
        # Processar operações
        operacoes_do_dia = operacoes_queryset.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            if operacao.investimento.id not in cdb_rdb.keys():
                cdb_rdb[operacao.investimento.id] = 0
                
            # Vendas
            if operacao.tipo_operacao == 'V':
                # Remover quantidade da operação de compra
                operacao_compra_id = operacao.operacao_compra_relacionada().id
                for operacao_c in operacoes:
                    if (operacao_c.id == operacao_compra_id):
                        operacao.atual = (operacao.quantidade/operacao_c.quantidade) * operacao_c.atual
                        operacao_c.atual -= operacao.atual
                        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                        operacoes.remove(operacao)
                        if operacao_c.atual == 0:
                            operacoes.remove(operacao_c)
                        break
                
        # Calcular o valor atualizado do patrimonio diariamente
        taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
        for operacao in operacoes:
            if (operacao.data <= data_iteracao):
                operacao.atual = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa)
                # Arredondar na última iteração
                if (data_iteracao == data_final):
                    str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                    operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            
        # Proximo dia útil
        proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
        if len(proximas_datas) > 0:
            data_iteracao = proximas_datas[0].data
        else:
            break
    
    # Preencher os valores nas letras de crédito
    for investimento_id in cdb_rdb.keys():
        for operacao in operacoes:
            if operacao.investimento.id == investimento_id:
                cdb_rdb[investimento_id] += operacao.atual
    
    return cdb_rdb

def calcular_valor_cdb_rdb_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula o valor das letras de crédito da divisão no dia determinado
    Parâmetros: Data final, id da divisão
    Retorno: Valor de cada letra de crédito da divisão na data escolhida {id_letra: valor_na_data, }
    """
    operacoes_divisao_id = DivisaoOperacaoCDB_RDB.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes_queryset = OperacaoCDB_RDB.objects.exclude(data__isnull=True).filter(id__in=operacoes_divisao_id).order_by('-tipo_operacao', 'data') 
    operacoes = list(operacoes_queryset)
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.atual = operacao.quantidade
            operacao.taxa = operacao.porcentagem()
    
    # Pegar data inicial
    data_inicial = operacoes_queryset.order_by('data')[0].data
    
    data_final = max(HistoricoTaxaDI.objects.filter(data__lte=dia).order_by('-data')[0].data, datetime.date.today())
    
    data_iteracao = data_inicial
    
    cdb_rdb = {}
    
    while data_iteracao <= data_final:
        # Processar operações
        operacoes_do_dia = operacoes_queryset.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            if operacao.investimento.id not in cdb_rdb.keys():
                cdb_rdb[operacao.investimento.id] = 0
                
            # Vendas
            if operacao.tipo_operacao == 'V':
                # Remover quantidade da operação de compra
                operacao_compra_id = operacao.operacao_compra_relacionada().id
                for operacao_c in operacoes:
                    if (operacao_c.id == operacao_compra_id):
                        operacao.atual = (DivisaoOperacaoLC.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade/DivisaoOperacaoLC.objects.get(divisao__id=divisao_id, operacao=operacao_c).quantidade) * operacao_c.atual
                        operacao_c.atual -= operacao.atual
                        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                        operacoes.remove(operacao)
                        if operacao_c.atual == 0:
                            operacoes.remove(operacao_c)
                        break
                    
        # Calcular o valor atualizado do patrimonio diariamente
        try:
            taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
        except:
            taxa_do_dia = 0
            
        for operacao in operacoes:
            if (operacao.data <= data_iteracao):
                if taxa_do_dia > 0:
                    operacao.atual = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa)
                # Arredondar na última iteração
                if (data_iteracao == data_final):
                    str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                    operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            
        # Proximo dia útil
        proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
        if len(proximas_datas) > 0:
            data_iteracao = proximas_datas[0].data
        elif data_iteracao < datetime.date.today():
            data_iteracao = datetime.date.today()
        else:
            break
        
    # Preencher os valores nas letras de crédito
    for investimento_id in cdb_rdb.keys():
        for operacao in operacoes:
            if operacao.investimento.id == investimento_id:
                cdb_rdb[investimento_id] += operacao.atual
    
    return cdb_rdb