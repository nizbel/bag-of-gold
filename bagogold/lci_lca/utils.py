# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal, ROUND_DOWN
from django.db.models.expressions import Case, When, F

from django.db.models.aggregates import Sum, Count
from django.db.models.functions import Coalesce

from bagogold.bagogold.models.divisoes import DivisaoOperacaoLCI_LCA, \
    CheckpointDivisaoLCI_LCA
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo, \
    calcular_iof_e_ir_longo_prazo
from bagogold.bagogold.utils.taxas_indexacao import \
    calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.lci_lca.models import OperacaoLetraCredito, \
    OperacaoVendaLetraCredito, CheckpointLetraCredito, LetraCredito


def calcular_valor_venda_lci_lca(operacao_venda, arredondar=True, valor_liquido=False):
    """
    Calcula o valor de venda de uma operação em LCI/LCA
    
    Parâmetros: Operação de venda
                Arredondar?
                Levar em consideração impostos (IOF e IR)?
    Resultado: Valor em reais da venda
    """
    if operacao_venda.tipo_operacao != 'V':
        raise ValueError('Apenas para operações de venda')
    # Adicionar informação de taxa para evitar buscas excessivas na base
    operacao_venda.taxa = operacao_venda.porcentagem()
    
    # Verificar se há checkpoints para a operação de compra
    if CheckpointLetraCredito.objects.filter(operacao=operacao_venda.operacao_compra_relacionada(), ano=operacao_venda.data.year-1).exists():
        # Se não, calcular valor da operação a partir do checkpoint
        checkpoint = CheckpointLetraCredito.objects.get(operacao=operacao_venda.operacao_compra_relacionada(), ano=operacao_venda.data.year-1)
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
#     # Definir período do histórico relevante para a operação
#     historico_utilizado = HistoricoTaxaDI.objects.filter(data__range=[operacao_venda.operacao_compra_relacionada().data, operacao_venda.data - datetime.timedelta(days=1)]).values('taxa').annotate(qtd_dias=Count('taxa'))
#     taxas_dos_dias = {}
#     for taxa_quantidade in historico_utilizado:
#         taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
#     
#     # Calcular
#     return calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao_venda.quantidade, operacao_venda.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)

def calcular_valor_operacao_lci_lca_ate_dia(operacao, dia=datetime.date.today(), arredondar=True, valor_liquido=False):
    """
    Calcula o valor de uma operação de compra em LCI/LCA até dia especificado
    
    Parâmetros: Operação de compra
                Data
                Arredondar?
                Levar em consideração impostos (IOF e IR)?
    Resultado: Valor em reais da venda
    """
    if operacao.tipo_operacao != 'C':
        raise ValueError('Apenas para operações de compra')
    # Calcular limitado ao vencimento da LCI/LCA
    dia = min(operacao.data_vencimento(), dia)
    data_ultima_valorizacao = min(operacao.data_vencimento() - datetime.timedelta(days=1), dia)
    
    # Adicionar informação de taxa para evitar buscas excessivas na base
    operacao.taxa = operacao.porcentagem()
    
    if CheckpointLetraCredito.objects.filter(operacao=operacao, ano=dia.year-1).exists():
        # Verificar se há vendas
        if OperacaoVendaLetraCredito.objects.filter(operacao_compra=operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = CheckpointLetraCredito.objects.get(operacao=operacao, ano=dia.year-1).qtd_restante
            qtd_restante -= sum(OperacaoVendaLetraCredito.objects.filter(operacao_compra=operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                                .values_list('operacao_venda__quantidade', flat=True))
            valor = calcular_valor_atualizado_operacao_ate_dia(qtd_restante, operacao.data, dia, operacao, qtd_restante, valor_liquido, data_ultima_valorizacao)
        else:
            # Se não, calcular valor da operação a partir do checkpoint
            checkpoint = CheckpointLetraCredito.objects.get(operacao=operacao, ano=dia.year-1)
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
    Calcula o valor atualizado de uma operação em LCI/LCA entre um período
    
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
        
    if operacao.letra_credito.tipo_rendimento == LetraCredito.LCI_LCA_DI:
        # Definir período do histórico relevante para a operação
        taxas_dos_dias = dict(HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_ultima_valorizacao]).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            
        # Calcular
        if valor_liquido:
            valor_final = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor, operacao.taxa)
            return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - qtd_original, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor, operacao.taxa)
    elif operacao.letra_credito.tipo_rendimento == LetraCredito.LCI_LCA_PREFIXADO:
        # Prefixado
        if valor_liquido:
            valor_final = calcular_valor_atualizado_com_taxa_prefixado(valor, operacao.taxa, qtd_dias_uteis_no_periodo(data_inicial, 
                                                                                                                        data_ultima_valorizacao + datetime.timedelta(days=1)))
            return valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - qtd_original, 
                                                 (data_final - operacao.data_inicial()).days))
        else:
            return calcular_valor_atualizado_com_taxa_prefixado(valor, operacao.taxa, qtd_dias_uteis_no_periodo(data_inicial, data_ultima_valorizacao + datetime.timedelta(days=1)))
    elif operacao.letra_credito.tipo_rendimento == LetraCredito.LCI_LCA_IPCA:
        # IPCA
        if valor_liquido:
            return Decimal(valor)
        else:
            return Decimal(valor)

def calcular_valor_lci_lca_ate_dia(investidor, dia=datetime.date.today(), valor_liquido=False):
    """ 
    Calcula o valor das letras de crédito no dia determinado
    
    Parâmetros: Investidor
                Data final
                Deve considerar IOF e IR?
    Retorno: Valor de cada letra de crédito na data escolhida {id_letra: valor_na_data, }
    """
#     # Definir vendas do investidor
#     vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra__investidor=investidor, operacao_venda__investidor=investidor, operacao_compra__data__lte=dia,
#                                                                              operacao_venda__data__lte=dia).values('operacao_compra').annotate(soma_venda=Sum('operacao_venda__quantidade'))
#     qtd_vendida_operacoes = {}
#     for venda in vendas:
#         qtd_vendida_operacoes[venda['operacao_compra']] = venda['soma_venda']
#     
#     # Definir compras do investidor
#     operacoes_queryset = OperacaoLetraCredito.objects.filter(investidor=investidor, data__lte=dia, tipo_operacao='C').exclude(data__isnull=True)
#     if len(operacoes_queryset) == 0:
#         return {}
#     operacoes = list(operacoes_queryset)
#     
#     letras_credito = {}
#     # Buscar taxas dos dias
#     historico = HistoricoTaxaDI.objects.all()
#     for operacao in operacoes:
#         operacao.quantidade -= 0 if operacao.id not in qtd_vendida_operacoes.keys() else qtd_vendida_operacoes[operacao.id]
#         if operacao.quantidade == 0:
#             continue
#         if operacao.letra_credito.id not in letras_credito.keys():
#             letras_credito[operacao.letra_credito.id] = 0
#         
#         # Definir período do histórico relevante para a operação
#         historico_utilizado = historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa'))
#         taxas_dos_dias = {}
#         for taxa_quantidade in historico_utilizado:
#             taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
#         
#         # Calcular
#         letras_credito[operacao.letra_credito.id] += calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
#     
#     return letras_credito
    
    
    operacoes = buscar_operacoes_vigentes_ate_data(investidor, dia)
    
    lci_lca = {}
    for operacao in operacoes:

        if operacao.letra_credito_id not in lci_lca.keys():
            lci_lca[operacao.letra_credito_id] = 0
        
        lci_lca[operacao.letra_credito_id] += calcular_valor_operacao_lci_lca_ate_dia(operacao, dia, True, valor_liquido)
    
    return lci_lca

def calcular_valor_lci_lca_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula o valor das letras de crédito da divisão no dia determinado
    
    Parâmetros: Data final
                ID da divisão
    Retorno: Valor de cada letra de crédito da divisão na data escolhida {id_letra: valor_na_data, }
    """
    if not DivisaoOperacaoLCI_LCA.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).exists():
        return {}
    
    operacoes = list(DivisaoOperacaoLCI_LCA.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).annotate(data=F('operacao__data')).exclude(data__isnull=True) \
                     .annotate(atual=F('quantidade')).annotate(tipo_operacao=F('operacao__tipo_operacao')).annotate(letra_credito_id=F('operacao__letra_credito')) \
                     .select_related('operacao').order_by('-tipo_operacao', 'data'))
     
    # Pegar data inicial
    data_inicial = operacoes[0].data
     
    letras_credito = {}
    for operacao in operacoes:
        # Processar operações
        if operacao.letra_credito_id not in letras_credito.keys():
            letras_credito[operacao.letra_credito_id] = 0
                 
        # Vendas
        if operacao.tipo_operacao == 'V':
            # Remover quantidade da operação de compra
            operacao_compra_id = operacao.operacao.operacao_compra_relacionada().id
            for operacao_c in operacoes:
                if (operacao_c.operacao_id == operacao_compra_id):
#                     operacao.atual = DivisaoOperacaoLCI_LCA.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
                    operacao_c.atual -= operacao.atual
                    break
#                 
    # Remover operações de venda e operações de compra totalmente vendidas
    operacoes = [operacao for operacao in operacoes if operacao.tipo_operacao == 'C' and operacao.atual > 0]
     
    # Calcular o valor atualizado do patrimonio
    historico = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, dia])
     
    for operacao in operacoes:
        taxas_dos_dias = dict(historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
        operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.atual, operacao.operacao.porcentagem())
        # Arredondar valores
        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
             
    # Preencher os valores nas letras de crédito
    for letra_credito_id in letras_credito.keys():
        letras_credito[letra_credito_id] += sum([operacao.atual for operacao in operacoes if operacao.letra_credito_id == letra_credito_id])
         
        if letras_credito[letra_credito_id] == 0:
            del letras_credito[letra_credito_id]
    
    return letras_credito

def calcular_valor_um_lci_lca_ate_dia_por_divisao(lci_lca, divisao_id, dia=datetime.date.today()):
    """ 
    Calcula o valor total de um LCI/LCA da divisão no dia determinado
    
    Parâmetros: LCI/LCA escolhido
                ID da divisão
                Data final
    Retorno: Valor atualizado do LCI/LCA na data
    """
    valor_atualizado = 0
    # Buscar checkpoints de divisão para o LCI/LCA
    for checkpoint in CheckpointDivisaoLCI_LCA.objects.filter(divisao_operacao__operacao__letra_credito=lci_lca, ano=dia.year-1, divisao_operacao__divisao__id=divisao_id):
        # Adicionar informação de taxa para evitar buscas excessivas na base
        checkpoint.divisao_operacao.operacao.taxa = checkpoint.divisao_operacao.operacao.porcentagem()
        
        # Verificar se há vendas
        if OperacaoVendaLetraCredito.objects.filter(operacao_compra=checkpoint.divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = checkpoint.qtd_restante
            vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra=checkpoint.divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                .values_list('operacao_venda__id', flat=True)
            for venda in DivisaoOperacaoLCI_LCA.objects.filter(operacao__id__in=vendas, divisao__id=divisao_id):
                qtd_restante -= venda.quantidade
            
            valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(qtd_restante, checkpoint.divisao_operacao.operacao.data, dia, checkpoint.divisao_operacao.operacao, qtd_restante).quantize(Decimal('.01'), ROUND_DOWN)
        else:
            # Se não, calcular valor da operação a partir do checkpoint
            valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(checkpoint.qtd_atualizada, dia.replace(month=1).replace(day=1), dia, 
                                                              checkpoint.divisao_operacao.operacao, checkpoint.qtd_restante).quantize(Decimal('.01'), ROUND_DOWN)
                                                              
    # Somar operações feitas no ano    
    for divisao_operacao in DivisaoOperacaoLCI_LCA.objects.filter(divisao__id=divisao_id, operacao__data__range=[dia.replace(day=1).replace(month=1), dia], operacao__letra_credito=lci_lca,
                                                                  operacao__tipo_operacao='C'):
        # Adicionar informação de taxa para evitar buscas excessivas na base
        divisao_operacao.operacao.taxa = divisao_operacao.operacao.porcentagem()
        
        valor_restante = divisao_operacao.qtd_disponivel_venda_na_data(dia)
        valor_atualizado += calcular_valor_atualizado_operacao_ate_dia(valor_restante, divisao_operacao.operacao.data, dia, divisao_operacao.operacao, valor_restante).quantize(Decimal('.01'), ROUND_DOWN)
    
    return valor_atualizado

def calcular_valor_op_lci_lca_ate_dia_por_divisao(divisao_operacao, dia=datetime.date.today(), arredondar=True):
    """ 
    Calcula o valor de uma operação em LCI/LCA para uma divisão divisão no dia determinado
    
    Parâmetros: Divisão da operação em LCI/LCA
                Data final
    Retorno: Valor atualizado da operação na data
    """
    # Adicionar informação de taxa para evitar buscas excessivas na base
    divisao_operacao.operacao.taxa = divisao_operacao.operacao.porcentagem()
    
    # Verificar existência de checkpoint
    if CheckpointDivisaoLCI_LCA.objects.filter(divisao_operacao=divisao_operacao, ano=dia.year-1).exists():
        checkpoint = CheckpointDivisaoLCI_LCA.objects.get(divisao_operacao=divisao_operacao, ano=dia.year-1)
        # Verificar se há vendas
        if OperacaoVendaLetraCredito.objects.filter(operacao_compra=divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]).exists():
            # Se sim, calcular valor restante e então calcular valor da operação no dia desde o começo
            qtd_restante = checkpoint.qtd_restante
            vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra=divisao_operacao.operacao, operacao_venda__data__range=[dia.replace(month=1).replace(day=1), dia]) \
                .values_list('operacao_venda__id', flat=True)
            for venda in DivisaoOperacaoLCI_LCA.objects.filter(operacao__id__in=vendas, divisao=divisao_operacao.divisao):
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
    Calcula o valor das operações em LCI/LCA vigentes até data especificada
    
    Parâmetros: Investidor
                Data
    Retorno: Lista de operações vigentes, adicionando os campos qtd_disponivel_venda e qtd_vendida
    """
    operacoes = OperacaoLetraCredito.objects.filter(investidor=investidor, tipo_operacao='C', data__lte=data).exclude(data__isnull=True) \
        .annotate(qtd_vendida=Coalesce(Sum(Case(When(operacao_compra__operacao_venda__data__lte=data, then='operacao_compra__operacao_venda__quantidade'))), 0)).exclude(quantidade=F('qtd_vendida')) \
        .annotate(qtd_disponivel_venda=(F('quantidade') - F('qtd_vendida'))).select_related('letra_credito')
    
    return operacoes

def atualizar_operacoes_lci_lca_no_periodo(operacoes, data_inicial, data_final):
    """
    Atualiza o atributo 'atual' para cada operação em LCI/LCA enviada, em um período (incluindo data final)
    
    Parâmetros: Operações
                Data inicial
                Data final
    Retorno: Operações com o atributo atual atualizado
    """
    # Buscar taxa DI
    historico_di = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_final])
    taxas_dos_dias = dict(historico_di.values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
    
    for operacao in operacoes:
        # Verificar data de vencimento da operação, não atualizar além dela
        data_final_operacao = min(data_final, operacao.data_vencimento() - datetime.timedelta(days=1))
        if data_final_operacao < data_inicial:
            continue
        
        if operacao.tipo_rendimento_lci_lca == LetraCredito.LCI_LCA_DI:
            # DI
            # Definir período do histórico relevante
            if data_final == data_final_operacao:
                taxas_dos_dias_operacao = taxas_dos_dias
            else:
                taxas_dos_dias_operacao = dict(historico_di.filter(data__lte=data_final_operacao).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias_operacao, operacao.atual, operacao.porcentagem())
        elif operacao.tipo_rendimento_lci_lca == LetraCredito.LCI_LCA_PREFIXADO:
            # Prefixado
            operacao.atual = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.porcentagem(), qtd_dias_uteis_no_periodo(data_inicial, data_final_operacao + datetime.timedelta(days=1)))
        elif operacao.tipo_rendimento_lci_lca == LetraCredito.LCI_LCA_IPCA:
            # IPCA
            operacao.atual = Decimal(operacao.atual)
    return operacoes

def simulador_lci_lca(filtros):
    """
    Simula uma aplicação em LCI/LCA para os valores especificados nos filtros
    
    Parâmetros: Dicionário com filtros
    Retorno:    Lista de datas (mes a mes) com valores, ex.: [(data, valor),...]
    """
    data_atual = datetime.date.today()
    resultado = [(data_atual, filtros['aplicacao'])]
    
    num_dias_grafico = min(filtros['periodo'], 64)
    
    # Marcar dias
    qtds_dias = [round(0 + (Decimal(filtros['periodo'])/num_dias_grafico)*parte) for parte in xrange(1, num_dias_grafico+1)]
    if filtros['tipo'] == 'POS':
        ultima_taxa_di = HistoricoTaxaDI.objects.all().order_by('-data')[0].taxa
        for qtd_dias in qtds_dias:
            qtd_dias_uteis = qtd_dias_uteis_no_periodo(data_atual, data_atual + datetime.timedelta(days=qtd_dias))
            qtd_atual = calcular_valor_atualizado_com_taxas_di({ultima_taxa_di: qtd_dias_uteis}, filtros['aplicacao'], filtros['percentual_indice'])
            resultado.append((data_atual + datetime.timedelta(days=qtd_dias), qtd_atual))
    elif filtros['tipo'] == 'PRE':
        for qtd_dias in qtds_dias:
            qtd_dias_uteis = qtd_dias_uteis_no_periodo(data_atual, data_atual + datetime.timedelta(days=qtd_dias))
            qtd_atual = calcular_valor_atualizado_com_taxa_prefixado(filtros['aplicacao'], filtros['percentual_indice'], qtd_dias_uteis)
            resultado.append((data_atual + datetime.timedelta(days=qtd_dias), qtd_atual))
    return resultado