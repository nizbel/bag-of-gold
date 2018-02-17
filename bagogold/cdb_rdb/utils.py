# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCDB_RDB
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo, \
    calcular_iof_e_ir_longo_prazo
from bagogold.cdb_rdb.models import OperacaoCDB_RDB, CDB_RDB, CheckpointCDB_RDB, \
    OperacaoVendaCDB_RDB
from decimal import Decimal, ROUND_DOWN
from django.db.models.aggregates import Sum, Count
from django.db.models.expressions import F, Case, When
from django.db.models.functions import Coalesce
import datetime

def calcular_valor_venda_cdb_rdb(operacao_venda, valor_liquido=False):
    """
    Calcula o valor de venda de uma operação em CDB/RDB
    Parâmetros: Operação de venda
                Levar em consideração impostos (IOF e IR)
    Resultado: Valor em reais da venda
    """
    if operacao_venda.tipo_operacao != 'V':
        raise ValueError('Apenas para operações de venda')
    return calcular_valor_atualizado_operacao_ate_dia(operacao_venda.quantidade, operacao_venda.data_inicial(), operacao_venda.data - datetime.timedelta(days=1), operacao_venda, valor_liquido)
#     if operacao_venda.operacao_compra_relacionada().cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
#         # Definir período do histórico relevante para a operação
#         historico_utilizado = HistoricoTaxaDI.objects.filter(data__range=[operacao_venda.operacao_compra_relacionada().data, operacao_venda.data - datetime.timedelta(days=1)]).values('taxa').annotate(qtd_dias=Count('taxa'))
#         taxas_dos_dias = {}
#         for taxa_quantidade in historico_utilizado:
#             taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
#         
#         # Calcular
#         if considerar_impostos:
#             valor_final = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao_venda.quantidade, 
#                                                                                         operacao_venda.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
#             return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao_venda.quantidade, 
#                                                  (operacao_venda.data - operacao_venda.operacao_compra_relacionada().data).days))
#         else:
#             return calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao_venda.quantidade, operacao_venda.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
#     elif operacao_venda.operacao_compra_relacionada().cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
#         # Prefixado
#         if considerar_impostos:
#             valor_final = calcular_valor_atualizado_com_taxa_prefixado(operacao_venda.quantidade, operacao_venda.porcentagem(), 
#                                                                                               qtd_dias_uteis_no_periodo(operacao_venda.operacao_compra_relacionada().data, 
#                                                                                                                         operacao_venda.data - datetime.timedelta(days=1)))
#             return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao_venda.quantidade, 
#                                                  (operacao_venda.data - operacao_venda.operacao_compra_relacionada().data).days))
#         else:
#             return calcular_valor_atualizado_com_taxa_prefixado(operacao_venda.quantidade, operacao_venda.porcentagem(), qtd_dias_uteis_no_periodo(operacao_venda.operacao_compra_relacionada().data, 
#                                                                                                                                                operacao_venda.data - datetime.timedelta(days=1)))
    

def calcular_valor_operacao_cdb_rdb_ate_dia(operacao, dia):
    if operacao.tipo_operacao != 'C':
        raise ValueError('Apenas para operações de compra')
    if CheckpointCDB_RDB.objects.filter(operacao=operacao, ano=dia.year-1).exists():
        # Verificar se há vendas
        if OperacaoVendaCDB_RDB.objects.filter(operacao_compra=operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = CheckpointCDB_RDB.objects.get(operacao=operacao, ano=dia.year-1).qtd_restante
            qtd_restante -= sum(OperacaoVendaCDB_RDB.objects.filter(operacao_compra=operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).values_list('operacao_venda__quantidade', flat=True))
            operacao.quantidade = qtd_restante
            return calcular_valor_atualizado_operacao_ate_dia(qtd_restante, operacao.data, dia, operacao)
        else:
            # Se não, calcular valor da operação a partir do checkpoint
            operacao.quantidade = CheckpointCDB_RDB.objects.get(operacao=operacao, ano=dia.year-1).qtd_restante
            return calcular_valor_atualizado_operacao_ate_dia(CheckpointCDB_RDB.objects.get(operacao=operacao, ano=dia.year-1).qtd_atualizada, dia.replace(month=1).replace(day=1), dia, operacao)
    else:
        # Sem checkpoint, calcular do começo
        qtd_restante = operacao.qtd_disponivel_venda_na_data(dia)
        operacao.quantidade = qtd_restante
        return calcular_valor_atualizado_operacao_ate_dia(qtd_restante, operacao.data, dia, operacao)
        
    
def calcular_valor_atualizado_operacao_ate_dia(valor, data_inicial, data_final, operacao, valor_liquido=False):
    """
    Calcula o valor atualizado de uma operação em CDB/RDB entre um período
    Parâmetros: Valor a atualizar
                Data inicial da atualização
                Data final da atualização
                Operação para pegar dados como tipo de rendimento e porcentagem
                Deve retornar o valor líquido?
    Retorno: Valor atualizado
    """
    if operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
        # Definir período do histórico relevante para a operação
        historico_utilizado = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_final]).values('taxa').annotate(qtd_dias=Count('taxa'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_utilizado:
            taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
        
        # Calcular
        if valor_liquido:
            valor_final = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
            return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao.quantidade, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
    elif operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
        # Prefixado
        if valor_liquido:
            valor_final = calcular_valor_atualizado_com_taxa_prefixado(valor, operacao.porcentagem(), qtd_dias_uteis_no_periodo(data_inicial, 
                                                                                                                        data_final))
            return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao.quantidade, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return calcular_valor_atualizado_com_taxa_prefixado(valor, operacao.porcentagem(), qtd_dias_uteis_no_periodo(data_inicial, data_final))

def calcular_valor_cdb_rdb_ate_dia(investidor, dia=datetime.date.today(), considerar_impostos=False):
    """ 
    Calcula o valor dos CDB/RDB no dia determinado
    Parâmetros: Investidor
                Data final
                Levar em consideração impostos (IOF e IR)
    Retorno: Valor de cada CDB/RDB na data escolhida {id_letra: valor_na_data, }
    """
    operacoes = buscar_operacoes_vigentes_ate_data(investidor, dia)
    
    cdb_rdb = {}
    # Buscar taxas dos dias
    historico = HistoricoTaxaDI.objects.all()
    for operacao in operacoes:
        # TODO consertar verificação de todas vendidas
        operacao.quantidade = operacao.qtd_disponivel_venda

        if operacao.cdb_rdb.id not in cdb_rdb.keys():
            cdb_rdb[operacao.cdb_rdb.id] = 0
        
        if operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
            # DI
            # Definir período do histórico relevante para a operação
            historico_utilizado = historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa'))
            taxas_dos_dias = {}
            for taxa_quantidade in historico_utilizado:
                taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
            
            # Calcular
            if considerar_impostos:
                valor_final = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
                cdb_rdb[operacao.cdb_rdb.id] += valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao.quantidade, 
                                                 (dia - operacao.data).days))
            else:
                cdb_rdb[operacao.cdb_rdb.id] += calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
        elif operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
            # Prefixado
            if considerar_impostos:
                valor_final = calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), qtd_dias_uteis_no_periodo(operacao.data, datetime.date.today())) \
                    .quantize(Decimal('.01'), ROUND_DOWN)
                cdb_rdb[operacao.cdb_rdb.id] += valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao.quantidade, 
                                                 (dia - operacao.data).days))
            else:
                cdb_rdb[operacao.cdb_rdb.id] += calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), 
                                                                                                  qtd_dias_uteis_no_periodo(operacao.data, datetime.date.today())).quantize(Decimal('.01'), ROUND_DOWN)
    
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
    
    compras_cdb_rdb = dict(DivisaoOperacaoCDB_RDB.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id, operacao__tipo_operacao='C') \
                           .values_list('operacao', 'quantidade'))
       
    vendas_cdb_rdb = dict(DivisaoOperacaoCDB_RDB.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id, operacao__tipo_operacao='V') \
                          .annotate(compra=F('operacao__operacao_venda__operacao_compra')).values('compra').annotate(qtd_total=Sum('quantidade')) \
                          .values_list('compra', 'qtd_total'))
                                    
    operacoes_cdb_rdb = { k: compras_cdb_rdb.get(k, 0) - vendas_cdb_rdb.get(k, 0) for k in set(compras_cdb_rdb) | set(vendas_cdb_rdb) \
               if compras_cdb_rdb.get(k, 0) - vendas_cdb_rdb.get(k, 0) > 0}
      
    # Verificar se não há mais operações vigentes na divisão
    if len(operacoes_cdb_rdb.keys()) == 0:
        return {}
    
    # Buscar operações presentes
    operacoes = OperacaoCDB_RDB.objects.filter(id__in=operacoes_cdb_rdb.keys()).order_by('data')
    
    # Calcular o valor atualizado do patrimonio
    historico = HistoricoTaxaDI.objects.filter(data__range=[operacoes[0].data, dia])
      
    for operacao in operacoes:
        if operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
            # DI
            taxas_dos_dias = dict(historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacoes_cdb_rdb[operacao.id], operacao.porcentagem())
        elif operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
            # Prefixado
            operacao.atual = calcular_valor_atualizado_com_taxa_prefixado(operacoes_cdb_rdb[operacao.id], operacao.porcentagem(), qtd_dias_uteis_no_periodo(operacao.data, datetime.date.today()))
               
        # Arredondar valores
        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
           
    cdb_rdb = {}
  
    # Preencher os valores nos cdb/rdb
    for investimento in list(set(operacoes.values_list('cdb_rdb', flat=True))):
        cdb_rdb[investimento] = sum([operacao.atual for operacao in operacoes if operacao.cdb_rdb.id == investimento])
    
    return cdb_rdb

def buscar_operacoes_vigentes_ate_data(investidor, data=datetime.date.today()):
    """
    Calcula o valor das operações em CDB/RDB vigentes até data especificada
    Parâmetros: Investidor
                Data
    Retorno: Lista de operações vigentes, adicionando os campos qtd_disponivel_venda e qtd_vendida
    """
    operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor, tipo_operacao='C', data__lte=data).exclude(data__isnull=True) \
        .annotate(qtd_vendida=Coalesce(Sum(Case(When(operacao_compra__operacao_venda__data__lte=data, then='operacao_compra__operacao_venda__quantidade'))), 0)).exclude(quantidade=F('qtd_vendida')) \
        .annotate(qtd_disponivel_venda=(F('quantidade') - F('qtd_vendida')))

    return operacoes