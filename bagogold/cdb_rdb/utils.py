# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCDB_RDB
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo
from bagogold.cdb_rdb.models import OperacaoCDB_RDB, CDB_RDB
from decimal import Decimal, ROUND_DOWN
from django.db.models.aggregates import Sum, Count
from django.db.models.expressions import F
from django.db.models.functions import Coalesce
import datetime

def calcular_valor_venda_cdb_rdb(operacao_venda):
    if operacao_venda.operacao_compra_relacionada().investimento.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
        # Definir período do histórico relevante para a operação
        historico_utilizado = HistoricoTaxaDI.objects.filter(data__range=[operacao_venda.operacao_compra_relacionada().data, operacao_venda.data - datetime.timedelta(days=1)]).values('taxa').annotate(qtd_dias=Count('taxa'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_utilizado:
            taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
        
        # Calcular
        return calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao_venda.quantidade, operacao_venda.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
    elif operacao_venda.operacao_compra_relacionada().investimento.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
        # Prefixado
        return calcular_valor_atualizado_com_taxa_prefixado(operacao_venda.quantidade, operacao_venda.porcentagem(), qtd_dias_uteis_no_periodo(operacao_venda.operacao_compra_relacionada().data, 
                                                                                                                                               operacao_venda.data - datetime.timedelta(days=1)))
    

def calcular_valor_cdb_rdb_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula o valor dos CDB/RDB no dia determinado
    Parâmetros: Investidor
                Data final
    Retorno: Valor de cada CDB/RDB na data escolhida {id_letra: valor_na_data, }
    """
    operacoes = buscar_operacoes_vigentes_ate_data(investidor, dia)
    
    cdb_rdb = {}
    # Buscar taxas dos dias
    historico = HistoricoTaxaDI.objects.all()
    for operacao in operacoes:
        # TODO consertar verificação de todas vendidas
        operacao.quantidade = operacao.qtd_disponivel_venda

        if operacao.investimento.id not in cdb_rdb.keys():
            cdb_rdb[operacao.investimento.id] = 0
        
        if operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
            # DI
            # Definir período do histórico relevante para a operação
            historico_utilizado = historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa'))
            taxas_dos_dias = {}
            for taxa_quantidade in historico_utilizado:
                taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
            
            # Calcular
            cdb_rdb[operacao.investimento.id] += calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
        elif operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
            # Prefixado
            cdb_rdb[operacao.investimento.id] += calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), qtd_dias_uteis_no_periodo(operacao.data, datetime.date.today())).quantize(Decimal('.01'), ROUND_DOWN)
    
    return cdb_rdb

def calcular_valor_cdb_rdb_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula o valor dos CDB/RDB da divisão no dia determinado
    Parâmetros: Data final
                ID da divisão
    Retorno: Valor de cada CDB/RDB da divisão na data escolhida {id_investimento: valor_na_data, }
    """
    if not DivisaoOperacaoCDB_RDB.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).exists():
        return {}
    
    operacoes_divisao_id = DivisaoOperacaoCDB_RDB.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    
    operacoes = list(OperacaoCDB_RDB.objects.exclude(data__isnull=True).filter(id__in=operacoes_divisao_id).order_by('-tipo_operacao', 'data'))
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.atual = DivisaoOperacaoCDB_RDB.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
    
    cdb_rdb = {}
    for operacao in operacoes:
        # Processar operações
        if operacao.investimento.id not in cdb_rdb.keys():
            cdb_rdb[operacao.investimento.id] = 0
                
        # Vendas
        if operacao.tipo_operacao == 'V':
            # Remover quantidade da operação de compra
            operacao_compra_id = operacao.operacao_compra_relacionada().id
            for operacao_c in operacoes:
                if (operacao_c.id == operacao_compra_id):
                    operacao.atual = DivisaoOperacaoCDB_RDB.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
                    operacao_c.atual -= operacao.atual
                    break
                
    # Remover operações de venda e operações de compra totalmente vendidas
    operacoes = [operacao for operacao in operacoes if operacao.tipo_operacao == 'C' and operacao.atual > 0]
    # Pegar data inicial
    data_inicial = operacoes[0].data
    
    # Calcular o valor atualizado do patrimonio
    historico = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, dia])
    
    for operacao in operacoes:
        if operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
            # DI
            taxas_dos_dias = dict(historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.atual, operacao.porcentagem())
        elif operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
            # Prefixado
            operacao.atual = calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), qtd_dias_uteis_no_periodo(operacao.data, datetime.date.today()))
            
        # Arredondar valores
        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        
    # Preencher os valores nas letras de crédito
    for cdb_rdb_id in cdb_rdb.keys():
        cdb_rdb[cdb_rdb_id] += sum([operacao.atual for operacao in operacoes if operacao.investimento.id == cdb_rdb_id])
        
    return cdb_rdb

def buscar_operacoes_vigentes_ate_data(investidor, data=datetime.date.today()):
    """
    Calcula o valor das operações em CDB/RDB vigentes até data especificada
    Parâmetros: Investidor
                Data
    Retorno: Lista de operações vigentes, adicionando os campos qtd_disponivel_venda e qtd_vendida
    """
    operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor, tipo_operacao='C', data__lte=data).exclude(data__isnull=True) \
        .annotate(qtd_vendida=Coalesce(Sum('operacao_compra__operacao_venda__quantidade'), 0)).exclude(quantidade=F('qtd_vendida')) \
        .annotate(qtd_disponivel_venda=(F('quantidade') - F('qtd_vendida')))

    return operacoes