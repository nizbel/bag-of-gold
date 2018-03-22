# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLetraCambio,\
    CheckpointDivisaoLetraCambio
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo, \
    calcular_iof_e_ir_longo_prazo
from bagogold.lc.models import OperacaoLetraCambio, LetraCambio, CheckpointLetraCambio, \
    OperacaoVendaLetraCambio
from decimal import Decimal, ROUND_DOWN
from django.db.models.aggregates import Sum, Count
from django.db.models.expressions import F, Case, When
from django.db.models.functions import Coalesce
from django.db.models.query_utils import Q
import datetime

def calcular_valor_venda_lc(operacao_venda, arredondar=True, valor_liquido=False):
    """
    Calcula o valor de venda de uma operação em Letras de Câmbio
    Parâmetros: Operação de venda
                Levar em consideração impostos (IOF e IR)
    Resultado: Valor em reais da venda
    """
    if operacao_venda.tipo_operacao != 'V':
        raise ValueError('Apenas para operações de venda')
    # Adicionar informação de taxa para evitar buscas excessivas na base
    operacao_venda.taxa = operacao_venda.porcentagem()
    
    # Verificar se há checkpoints para a operação de compra
    if CheckpointLetraCambio.objects.filter(operacao=operacao_venda.operacao_compra_relacionada(), ano=operacao_venda.data.year-1).exists():
        # Se não, calcular valor da operação a partir do checkpoint
        checkpoint = CheckpointLetraCambio.objects.get(operacao=operacao_venda.operacao_compra_relacionada(), ano=operacao_venda.data.year-1)
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
    

def calcular_valor_operacao_lc_ate_dia(operacao, dia=datetime.date.today(), arredondar=True, valor_liquido=False):
    if operacao.tipo_operacao != 'C':
        raise ValueError('Apenas para operações de compra')
    # Calcular limitado ao vencimento da Letras de Câmbio
    dia = min(operacao.data_vencimento(), dia)
    data_ultima_valorizacao = min(operacao.data_vencimento() - datetime.timedelta(days=1), dia)
    
    # Adicionar informação de taxa para evitar buscas excessivas na base
    operacao.taxa = operacao.porcentagem()
    
    if CheckpointLetraCambio.objects.filter(operacao=operacao, ano=dia.year-1).exists():
        # Verificar se há vendas
        if OperacaoVendaLetraCambio.objects.filter(operacao_compra=operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = CheckpointLetraCambio.objects.get(operacao=operacao, ano=dia.year-1).qtd_restante
            qtd_restante -= sum(OperacaoVendaLetraCambio.objects.filter(operacao_compra=operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                                .values_list('operacao_venda__quantidade', flat=True))
            valor = calcular_valor_atualizado_operacao_ate_dia(qtd_restante, operacao.data, dia, operacao, qtd_restante, valor_liquido, data_ultima_valorizacao)
        else:
            # Se não, calcular valor da operação a partir do checkpoint
            checkpoint = CheckpointLetraCambio.objects.get(operacao=operacao, ano=dia.year-1)
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
    Calcula o valor atualizado de uma operação em Letras de Câmbio entre um período
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
        
    if operacao.lc.tipo_rendimento == LetraCambio.LC_DI:
        # Definir período do histórico relevante para a operação
        taxas_dos_dias = dict(HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_ultima_valorizacao]).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            
        # Calcular
        if valor_liquido:
            valor_final = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor, operacao.taxa)
            return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - qtd_original, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor, operacao.taxa)
    elif operacao.lc.tipo_rendimento == LetraCambio.LC_PREFIXADO:
        # Prefixado
        if valor_liquido:
            valor_final = calcular_valor_atualizado_com_taxa_prefixado(valor, operacao.taxa, qtd_dias_uteis_no_periodo(data_inicial, 
                                                                                                                        data_ultima_valorizacao + datetime.timedelta(days=1)))
            return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - qtd_original, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return calcular_valor_atualizado_com_taxa_prefixado(valor, operacao.taxa, qtd_dias_uteis_no_periodo(data_inicial, data_ultima_valorizacao + datetime.timedelta(days=1)))
    elif operacao.lc.tipo_rendimento == LetraCambio.LC_IPCA:
        # IPCA
        if valor_liquido:
            return Decimal(valor)
        else:
            return Decimal(valor)

def calcular_valor_lc_ate_dia(investidor, dia=datetime.date.today(), valor_liquido=False):
    """ 
    Calcula o valor das Letras de Câmbio no dia determinado
    Parâmetros: Investidor
                Data final
                Levar em consideração impostos (IOF e IR)
    Retorno: Valor de cada Letra de Câmbio na data escolhida {id_letra: valor_na_data, }
    """
    operacoes = buscar_operacoes_vigentes_ate_data(investidor, dia)
    
    lc = {}
    for operacao in operacoes:
        # TODO consertar verificação de todas vendidas
#         operacao.quantidade = operacao.qtd_disponivel_venda

        if operacao.lc.id not in lc.keys():
            lc[operacao.lc.id] = 0
        
#         lc[operacao.lc.id] += calcular_valor_atualizado_operacao_ate_dia(operacao.quantidade, operacao.data, dia, operacao, valor_liquido)
        lc[operacao.lc.id] += calcular_valor_operacao_lc_ate_dia(operacao, dia, True, valor_liquido)
    
    return lc

def calcular_valor_lc_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula o valor das Letras de Câmbio da divisão no dia determinado
    Parâmetros: Data final
                ID da divisão
    Retorno: Valor de cada Letra de Câmbio da divisão na data escolhida {id_lc: valor_na_data, }
    """
    if not DivisaoOperacaoLetraCambio.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).exists():
        return {}
    
    compras_lc = dict(DivisaoOperacaoLetraCambio.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id, operacao__tipo_operacao='C') \
                           .values_list('operacao', 'quantidade'))
        
    vendas_lc = dict(DivisaoOperacaoLetraCambio.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id, operacao__tipo_operacao='V') \
                          .annotate(compra=F('operacao__operacao_venda__operacao_compra')).values('compra').annotate(qtd_total=Sum('quantidade')) \
                          .values_list('compra', 'qtd_total'))
                                     
    operacoes_lc = { k: compras_lc.get(k, 0) - vendas_lc.get(k, 0) for k in set(compras_lc) | set(vendas_lc) \
               if compras_lc.get(k, 0) - vendas_lc.get(k, 0) > 0}
       
    # Verificar se não há mais operações vigentes na divisão
    if len(operacoes_lc.keys()) == 0:
        return {}
     
    # Buscar operações não totalmente vendidas
    operacoes = OperacaoLetraCambio.objects.filter(id__in=operacoes_lc.keys()).order_by('data')
      
    # Calcular o valor atualizado do patrimonio
    historico = HistoricoTaxaDI.objects.filter(data__range=[operacoes[0].data, dia])
        
    for operacao in operacoes:
        if operacao.lc.tipo_rendimento == LetraCambio.LC_DI:
            # DI
            taxas_dos_dias = dict(historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacoes_lc[operacao.id], operacao.porcentagem())
        elif operacao.lc.tipo_rendimento == LetraCambio.LC_PREFIXADO:
            # Prefixado
            operacao.atual = calcular_valor_atualizado_com_taxa_prefixado(operacoes_lc[operacao.id], operacao.porcentagem(), qtd_dias_uteis_no_periodo(operacao.data, datetime.date.today()))
                 
        # Arredondar valores
        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
             
    lc = {}
    
    # Preencher os valores nas Letras de Câmbio
    for investimento in list(set(operacoes.values_list('lc', flat=True))):
        lc[investimento] = sum([operacao.atual for operacao in operacoes if operacao.lc.id == investimento])
        
    return lc

def calcular_valor_um_lc_ate_dia_por_divisao(lc, divisao_id, dia=datetime.date.today()):
    """ 
    Calcula o valor total de uma Letras de Câmbio da divisão no dia determinado
    Parâmetros: Letras de Câmbio escolhida
                ID da divisão
                Data final
    Retorno: Valor atualizado da Letras de Câmbio na data
    """
    valor_atualizado = 0
    # Buscar checkpoints de divisão para a Letras de Câmbio
    for checkpoint in CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao__lc=lc, ano=dia.year-1, divisao_operacao__divisao__id=divisao_id):
        # Adicionar informação de taxa para evitar buscas excessivas na base
        checkpoint.divisao_operacao.operacao.taxa = checkpoint.divisao_operacao.operacao.porcentagem()
        
        # Verificar se há vendas
        if OperacaoVendaLetraCambio.objects.filter(operacao_compra=checkpoint.divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = checkpoint.qtd_restante
            vendas = OperacaoVendaLetraCambio.objects.filter(operacao_compra=checkpoint.divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                .values_list('operacao_venda__id', flat=True)
            for venda in DivisaoOperacaoLetraCambio.objects.filter(operacao__id__in=vendas, divisao__id=divisao_id):
                qtd_restante -= venda.quantidade
            
            valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(qtd_restante, checkpoint.divisao_operacao.operacao.data, dia, checkpoint.divisao_operacao.operacao, qtd_restante).quantize(Decimal('.01'), ROUND_DOWN)
        else:
            # Se não, calcular valor da operação a partir do checkpoint
            valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(checkpoint.qtd_atualizada, dia.replace(month=1).replace(day=1), dia, 
                                                              checkpoint.divisao_operacao.operacao, checkpoint.qtd_restante).quantize(Decimal('.01'), ROUND_DOWN)
                                                              
    # Somar operações feitas no ano    
    for divisao_operacao in DivisaoOperacaoLetraCambio.objects.filter(divisao__id=divisao_id, operacao__data__range=[dia.replace(day=1).replace(month=1), dia], operacao__lc=lc,
                                                                  operacao__tipo_operacao='C'):
        # Adicionar informação de taxa para evitar buscas excessivas na base
        divisao_operacao.operacao.taxa = divisao_operacao.operacao.porcentagem()
        
        valor_restante = divisao_operacao.qtd_disponivel_venda_na_data(dia)
        valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(valor_restante, divisao_operacao.operacao.data, dia, divisao_operacao.operacao, valor_restante).quantize(Decimal('.01'), ROUND_DOWN)
    
    return valor_atualizado

def calcular_valor_op_lc_ate_dia_por_divisao(divisao_operacao, dia=datetime.date.today(), arredondar=True):
    """ 
    Calcula o valor de uma operação em Letras de Câmbio para uma divisão divisão no dia determinado
    Parâmetros: Divisão da operação em Letras de Câmbio
                Data final
    Retorno: Valor atualizado da operação na data
    """
    # Adicionar informação de taxa para evitar buscas excessivas na base
    divisao_operacao.operacao.taxa = divisao_operacao.operacao.porcentagem()
    
    # Verificar existência de checkpoint
    if CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao=divisao_operacao, ano=dia.year-1).exists():
        checkpoint = CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=dia.year-1)
        # Verificar se há vendas
        if OperacaoVendaLetraCambio.objects.filter(operacao_compra=divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = checkpoint.qtd_restante
            vendas = OperacaoVendaLetraCambio.objects.filter(operacao_compra=divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                .values_list('operacao_venda__id', flat=True)
            for venda in DivisaoOperacaoLetraCambio.objects.filter(operacao__id__in=vendas, divisao=divisao_operacao.divisao):
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
    Calcula o valor das operações em Letras de Câmbio vigentes até data especificada
    Parâmetros: Investidor
                Data
    Retorno: Lista de operações vigentes, adicionando os campos qtd_disponivel_venda e qtd_vendida
    """
    operacoes = OperacaoLetraCambio.objects.filter(investidor=investidor, tipo_operacao='C', data__lte=data).exclude(data__isnull=True) \
        .annotate(qtd_vendida=Coalesce(Sum(Case(When(operacao_compra__operacao_venda__data__lte=data, then='operacao_compra__operacao_venda__quantidade'))), 0)).exclude(quantidade=F('qtd_vendida')) \
        .annotate(qtd_disponivel_venda=(F('quantidade') - F('qtd_vendida')))
    
#     operacoes = OperacaoLetraCambio.objects.filter(Q(investidor=investidor, checkpointlc__ano=data.year-1) | \
#                                                Q(investidor=investidor, tipo_operacao='C', data__range=[data.replace(month=1).replace(day=1), data])) \
#         .annotate(qtd_restante=Coalesce(F('checkpointlc__qtd_restante'), F('quantidade'))) \
#         .annotate(qtd_vendida=Coalesce(Sum(Case(When(operacao_compra__operacao_venda__data__range=[data.replace(month=1).replace(day=1), data], then='operacao_compra__operacao_venda__quantidade'))), 0)).exclude(qtd_restante=F('qtd_vendida')) \
#         .annotate(qtd_disponivel_venda=(F('qtd_restante') - F('qtd_vendida')))

    return operacoes