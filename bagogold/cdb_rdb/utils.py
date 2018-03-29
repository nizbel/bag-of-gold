# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCDB_RDB, \
    CheckpointDivisaoCDB_RDB
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo, \
    calcular_iof_e_ir_longo_prazo
from bagogold.bagogold.utils.taxas_indexacao import \
    calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.cdb_rdb.models import OperacaoCDB_RDB, CDB_RDB, CheckpointCDB_RDB, \
    OperacaoVendaCDB_RDB
from decimal import Decimal, ROUND_DOWN
from django.db.models.aggregates import Sum, Count
from django.db.models.expressions import F, Case, When
from django.db.models.functions import Coalesce
from django.db.models.query_utils import Q
import datetime

def calcular_valor_venda_cdb_rdb(operacao_venda, arredondar=True, valor_liquido=False):
    """
    Calcula o valor de venda de uma operação em CDB/RDB
    Parâmetros: Operação de venda
                Levar em consideração impostos (IOF e IR)
    Resultado: Valor em reais da venda
    """
    if operacao_venda.tipo_operacao != 'V':
        raise ValueError('Apenas para operações de venda')
    # Adicionar informação de taxa para evitar buscas excessivas na base
    operacao_venda.taxa = operacao_venda.porcentagem()
    
    # Verificar se há checkpoints para a operação de compra
    if CheckpointCDB_RDB.objects.filter(operacao=operacao_venda.operacao_compra_relacionada(), ano=operacao_venda.data.year-1).exists():
        # Se não, calcular valor da operação a partir do checkpoint
        checkpoint = CheckpointCDB_RDB.objects.get(operacao=operacao_venda.operacao_compra_relacionada(), ano=operacao_venda.data.year-1)
        valor = calcular_valor_atualizado_operacao_ate_dia(checkpoint.qtd_atualizada, operacao_venda.data.replace(month=1).replace(day=1), operacao_venda.data, 
                                                          operacao_venda, checkpoint.qtd_restante, valor_liquido, 
                                                          operacao_venda.data - datetime.timedelta(days=1)) \
                                                          * (operacao_venda.quantidade / checkpoint.qtd_restante)
    else:
        # Sem checkpoint, calcular do começo
        valor = calcular_valor_atualizado_operacao_ate_dia(operacao_venda.quantidade, operacao_venda.data_inicial(), operacao_venda.data, operacao_venda,
                                                      operacao_venda.quantidade, valor_liquido, operacao_venda.data - datetime.timedelta(days=1))
    if arredondar:
        return valor.quantize(Decimal('.01'), ROUND_DOWN)
    return valor
    

def calcular_valor_operacao_cdb_rdb_ate_dia(operacao, dia=datetime.date.today(), arredondar=True, valor_liquido=False):
    if operacao.tipo_operacao != 'C':
        raise ValueError('Apenas para operações de compra')
    # Calcular limitado ao vencimento do CDB/RDB
    dia = min(operacao.data_vencimento(), dia)
    data_ultima_valorizacao = min(operacao.data_vencimento() - datetime.timedelta(days=1), dia)
    
    # Adicionar informação de taxa para evitar buscas excessivas na base
    operacao.taxa = operacao.porcentagem()
    
    if CheckpointCDB_RDB.objects.filter(operacao=operacao, ano=dia.year-1).exists():
        # Verificar se há vendas
        if OperacaoVendaCDB_RDB.objects.filter(operacao_compra=operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = CheckpointCDB_RDB.objects.get(operacao=operacao, ano=dia.year-1).qtd_restante
            qtd_restante -= sum(OperacaoVendaCDB_RDB.objects.filter(operacao_compra=operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                                .values_list('operacao_venda__quantidade', flat=True))
            valor = calcular_valor_atualizado_operacao_ate_dia(qtd_restante, operacao.data, dia, operacao, qtd_restante, valor_liquido, data_ultima_valorizacao)
        else:
            # Se não, calcular valor da operação a partir do checkpoint
            checkpoint = CheckpointCDB_RDB.objects.get(operacao=operacao, ano=dia.year-1)
            valor = calcular_valor_atualizado_operacao_ate_dia(checkpoint.qtd_atualizada, dia.replace(month=1).replace(day=1), dia, 
                                                              operacao, checkpoint.qtd_restante, valor_liquido, data_ultima_valorizacao)
    else:
        # Sem checkpoint, calcular do começo
        qtd_restante = operacao.qtd_disponivel_venda_na_data(dia)
        valor = calcular_valor_atualizado_operacao_ate_dia(qtd_restante, operacao.data, dia, operacao, qtd_restante, valor_liquido, data_ultima_valorizacao)
    if arredondar:
        return valor.quantize(Decimal('.01'), ROUND_DOWN)
    return valor
        
    
def calcular_valor_atualizado_operacao_ate_dia(valor, data_inicial, data_final, operacao, qtd_original, valor_liquido=False, data_ultima_valorizacao=None):
    """
    Calcula o valor atualizado de uma operação em CDB/RDB entre um período
    Parâmetros: Valor a atualizar
                Data inicial da atualização
                Data final da atualização
                Operação para pegar dados como tipo de rendimento e taxa (deve ser preenchida com a porcentagem)
                Quantidade original para cálculo de impostos
                Deve retornar o valor líquido?
                Data da última valorização para o cálculo
    Retorno: Valor atualizado
    """
    if data_final < data_inicial:
        if valor_liquido:
            return valor - sum(calcular_iof_e_ir_longo_prazo(valor - qtd_original, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return valor
    # Se não informada, última valorização acontece na data final
    if not data_ultima_valorizacao:
        data_ultima_valorizacao = data_final
        
    if operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
        # Definir período do histórico relevante para a operação
        taxas_dos_dias = dict(HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_ultima_valorizacao]).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            
        # Calcular
        if valor_liquido:
            valor_final = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor, operacao.taxa)
            return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - qtd_original, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor, operacao.taxa)
    elif operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
        # Prefixado
        if valor_liquido:
            valor_final = calcular_valor_atualizado_com_taxa_prefixado(valor, operacao.taxa, qtd_dias_uteis_no_periodo(data_inicial, 
                                                                                                                        data_ultima_valorizacao + datetime.timedelta(days=1)))
            return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - qtd_original, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return calcular_valor_atualizado_com_taxa_prefixado(valor, operacao.taxa, qtd_dias_uteis_no_periodo(data_inicial, data_ultima_valorizacao + datetime.timedelta(days=1)))
    elif operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_IPCA:
        # IPCA
        if valor_liquido:
            return Decimal(valor)
        else:
            return Decimal(valor)

def calcular_valor_cdb_rdb_ate_dia(investidor, dia=datetime.date.today(), valor_liquido=False):
    """ 
    Calcula o valor dos CDB/RDB no dia determinado
    Parâmetros: Investidor
                Data final
                Levar em consideração impostos (IOF e IR)
    Retorno: Valor de cada CDB/RDB na data escolhida {id_letra: valor_na_data, }
    """
    operacoes = buscar_operacoes_vigentes_ate_data(investidor, dia)
    
    cdb_rdb = {}
    for operacao in operacoes:
        # TODO consertar verificação de todas vendidas
#         operacao.quantidade = operacao.qtd_disponivel_venda

        if operacao.cdb_rdb.id not in cdb_rdb.keys():
            cdb_rdb[operacao.cdb_rdb.id] = 0
        
#         cdb_rdb[operacao.cdb_rdb.id] += calcular_valor_atualizado_operacao_ate_dia(operacao.quantidade, operacao.data, dia, operacao, valor_liquido)
        cdb_rdb[operacao.cdb_rdb.id] += calcular_valor_operacao_cdb_rdb_ate_dia(operacao, dia, True, valor_liquido)
    
    return cdb_rdb

def calcular_valor_cdb_rdb_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula o valor dos CDB/RDB da divisão no dia determinado
    Parâmetros: Data final
                ID da divisão
    Retorno: Valor de cada CDB/RDB da divisão na data escolhida {id_cdb_rdb: valor_na_data, }
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
     
    # Buscar operações não totalmente vendidas
    operacoes = DivisaoOperacaoCDB_RDB.objects.filter(operacao__id__in=operacoes_cdb_rdb.keys(), divisao__id=divisao_id).annotate(cdb_rdb=F('operacao__cdb_rdb')).order_by('operacao__data')
    
    for operacao in operacoes:
        operacao.atual = calcular_valor_op_cdb_rdb_ate_dia_por_divisao(operacao, dia, True)
        
    cdb_rdb = {}
    
    # Preencher os valores nos CDB/RDB
    for investimento in list(set(operacoes.values_list('cdb_rdb', flat=True))):
        cdb_rdb[investimento] = sum([operacao.atual for operacao in operacoes if operacao.cdb_rdb == investimento])

    return cdb_rdb

def calcular_valor_um_cdb_rdb_ate_dia_por_divisao(cdb_rdb, divisao_id, dia=datetime.date.today()):
    """ 
    Calcula o valor total de um CDB/RDB da divisão no dia determinado
    Parâmetros: CDB/RDB escolhido
                ID da divisão
                Data final
    Retorno: Valor atualizado do CDB/RDB na data
    """
    valor_atualizado = 0
    # Buscar checkpoints de divisão para o CDB/RDB
    for checkpoint in CheckpointDivisaoCDB_RDB.objects.filter(divisao_operacao__operacao__cdb_rdb=cdb_rdb, ano=dia.year-1, divisao_operacao__divisao__id=divisao_id):
        # Adicionar informação de taxa para evitar buscas excessivas na base
        checkpoint.divisao_operacao.operacao.taxa = checkpoint.divisao_operacao.operacao.porcentagem()
        
        # Verificar se há vendas
        if OperacaoVendaCDB_RDB.objects.filter(operacao_compra=checkpoint.divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = checkpoint.qtd_restante
            vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=checkpoint.divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                .values_list('operacao_venda__id', flat=True)
            for venda in DivisaoOperacaoCDB_RDB.objects.filter(operacao__id__in=vendas, divisao__id=divisao_id):
                qtd_restante -= venda.quantidade
            
            valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(qtd_restante, checkpoint.divisao_operacao.operacao.data, dia, checkpoint.divisao_operacao.operacao, qtd_restante).quantize(Decimal('.01'), ROUND_DOWN)
        else:
            # Se não, calcular valor da operação a partir do checkpoint
            valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(checkpoint.qtd_atualizada, dia.replace(month=1).replace(day=1), dia, 
                                                              checkpoint.divisao_operacao.operacao, checkpoint.qtd_restante).quantize(Decimal('.01'), ROUND_DOWN)
                                                              
    # Somar operações feitas no ano    
    for divisao_operacao in DivisaoOperacaoCDB_RDB.objects.filter(divisao__id=divisao_id, operacao__data__range=[dia.replace(day=1).replace(month=1), dia], operacao__cdb_rdb=cdb_rdb,
                                                                  operacao__tipo_operacao='C'):
        # Adicionar informação de taxa para evitar buscas excessivas na base
        divisao_operacao.operacao.taxa = divisao_operacao.operacao.porcentagem()
        
        valor_restante = divisao_operacao.qtd_disponivel_venda_na_data(dia)
        valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(valor_restante, divisao_operacao.operacao.data, dia, divisao_operacao.operacao, valor_restante).quantize(Decimal('.01'), ROUND_DOWN)
    
    return valor_atualizado

def calcular_valor_op_cdb_rdb_ate_dia_por_divisao(divisao_operacao, dia=datetime.date.today(), arredondar=True):
    """ 
    Calcula o valor de uma operação em CDB/RDB para uma divisão divisão no dia determinado
    Parâmetros: Divisão da operação em CDB/RDB
                Data final
    Retorno: Valor atualizado da operação na data
    """
    # Adicionar informação de taxa para evitar buscas excessivas na base
    divisao_operacao.operacao.taxa = divisao_operacao.operacao.porcentagem()
    
    # Verificar existência de checkpoint
    if CheckpointDivisaoCDB_RDB.objects.filter(divisao_operacao=divisao_operacao, ano=dia.year-1).exists():
        checkpoint = CheckpointDivisaoCDB_RDB.objects.get(divisao_operacao=divisao_operacao, ano=dia.year-1)
        # Verificar se há vendas
        if OperacaoVendaCDB_RDB.objects.filter(operacao_compra=divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = checkpoint.qtd_restante
            vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                .values_list('operacao_venda__id', flat=True)
            for venda in DivisaoOperacaoCDB_RDB.objects.filter(operacao__id__in=vendas, divisao=divisao_operacao.divisao):
                qtd_restante -= venda.quantidade
            
            valor_atualizado = calcular_valor_atualizado_operacao_ate_dia(qtd_restante, divisao_operacao.operacao.data, dia, divisao_operacao.operacao, qtd_restante)
        else:
            # Se não, calcular valor da operação a partir do checkpoint
            valor_atualizado = calcular_valor_atualizado_operacao_ate_dia(checkpoint.qtd_atualizada, dia.replace(month=1).replace(day=1), dia, 
                                                              divisao_operacao.operacao, checkpoint.qtd_restante)
    
    else:
        valor_restante = divisao_operacao.qtd_disponivel_venda_na_data(dia)
        valor_atualizado = calcular_valor_atualizado_operacao_ate_dia(valor_restante, divisao_operacao.operacao.data, dia, divisao_operacao.operacao, valor_restante)
    
    if arredondar:
        return valor_atualizado.quantize(Decimal('.01'), ROUND_DOWN)
    return valor_atualizado
    

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
    
#     operacoes = OperacaoCDB_RDB.objects.filter(Q(investidor=investidor, checkpointcdb_rdb__ano=data.year-1) | \
#                                                Q(investidor=investidor, tipo_operacao='C', data__range=[data.replace(month=1).replace(day=1), data])) \
#         .annotate(qtd_restante=Coalesce(F('checkpointcdb_rdb__qtd_restante'), F('quantidade'))) \
#         .annotate(qtd_vendida=Coalesce(Sum(Case(When(operacao_compra__operacao_venda__data__range=[data.replace(month=1).replace(day=1), data], then='operacao_compra__operacao_venda__quantidade'))), 0)).exclude(qtd_restante=F('qtd_vendida')) \
#         .annotate(qtd_disponivel_venda=(F('qtd_restante') - F('qtd_vendida')))

    return operacoes