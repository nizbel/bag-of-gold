# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC
from bagogold.bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito, OperacaoVendaLetraCredito
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo
from decimal import Decimal, ROUND_DOWN
from django.db.models import Q
from django.db.models.aggregates import Sum, Count
import datetime

def calcular_valor_atualizado_com_taxa(taxa_do_dia, valor_atual, operacao_taxa):
    """
    Calcula o valor atualizado de uma operação em LC, a partir da taxa DI do dia
    Parâmetros: Taxa DI do dia
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa DI
    """
    return ((pow((Decimal(1) + taxa_do_dia/100), Decimal(1)/Decimal(252)) - Decimal(1)) * operacao_taxa/100 + Decimal(1)) * valor_atual

def calcular_valor_atualizado_com_taxas(taxas_dos_dias, valor_atual, operacao_taxa):
    """
    Calcula o valor atualizado de uma operação em LC, a partir das taxa DI dos dias
    Parâmetros: Taxas DI dos dias {taxa(Decimal): quantidade_de_dias}
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa DI
    """
    taxa_acumulada = 1
    for taxa_do_dia in taxas_dos_dias.keys():
        taxa_acumulada *= pow(((pow((Decimal(1) + taxa_do_dia/100), Decimal(1)/Decimal(252)) - Decimal(1)) * operacao_taxa/100 + Decimal(1)), taxas_dos_dias[taxa_do_dia])
    return taxa_acumulada * valor_atual

def calcular_valor_venda_lc(operacao_venda):
    # Definir período do histórico relevante para a operação
    historico_utilizado = HistoricoTaxaDI.objects.filter(data__range=[operacao_venda.operacao_compra_relacionada().data, operacao_venda.data - datetime.timedelta(days=1)]).values('taxa').annotate(qtd_dias=Count('taxa'))
    taxas_dos_dias = {}
    for taxa_quantidade in historico_utilizado:
        taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
    
    # Calcular
    return calcular_valor_atualizado_com_taxas(taxas_dos_dias, operacao_venda.quantidade, operacao_venda.porcentagem_di()).quantize(Decimal('.01'), ROUND_DOWN)

def calcular_valor_lc_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula o valor das letras de crédito no dia determinado
    Parâmetros: Investidor
                Data final
    Retorno: Valor de cada letra de crédito na data escolhida {id_letra: valor_na_data, }
    """
    # Definir vendas do investidor
    vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra__investidor=investidor, operacao_venda__investidor=investidor, operacao_compra__data__lte=dia,
                                                                             operacao_venda__data__lte=dia).values('operacao_compra').annotate(soma_venda=Sum('operacao_venda__quantidade'))
    qtd_vendida_operacoes = {}
    for venda in vendas:
        qtd_vendida_operacoes[venda['operacao_compra']] = venda['soma_venda']
    
    # Definir compras do investidor
    operacoes_queryset = OperacaoLetraCredito.objects.filter(investidor=investidor, data__lte=dia, tipo_operacao='C').exclude(data__isnull=True)
    if len(operacoes_queryset) == 0:
        return {}
    operacoes = list(operacoes_queryset)
    
    letras_credito = {}
    # Buscar taxas dos dias
    historico = HistoricoTaxaDI.objects.all()
    for operacao in operacoes:
        operacao.quantidade -= 0 if operacao.id not in qtd_vendida_operacoes.keys() else qtd_vendida_operacoes[operacao.id]
        if operacao.quantidade == 0:
            continue
        if operacao.letra_credito.id not in letras_credito.keys():
            letras_credito[operacao.letra_credito.id] = 0
        
        # Definir período do histórico relevante para a operação
        historico_utilizado = historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_utilizado:
            taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
        
        # Calcular
        letras_credito[operacao.letra_credito.id] += calcular_valor_atualizado_com_taxas(taxas_dos_dias, operacao.quantidade, operacao.porcentagem_di()).quantize(Decimal('.01'), ROUND_DOWN)
    
    return letras_credito

def calcular_valor_lc_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula o valor das letras de crédito da divisão no dia determinado
    Parâmetros: Data final
                ID da divisão
    Retorno: Valor de cada letra de crédito da divisão na data escolhida {id_letra: valor_na_data, }
    """
    if not DivisaoOperacaoLC.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).exists():
        return {}
    
    operacoes_divisao_id = DivisaoOperacaoLC.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    
    operacoes_queryset = OperacaoLetraCredito.objects.exclude(data__isnull=True).filter(id__in=operacoes_divisao_id).order_by('-tipo_operacao', 'data') 
    operacoes = list(operacoes_queryset)
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.atual = DivisaoOperacaoLC.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
            operacao.taxa = operacao.porcentagem_di()
    
    # Pegar data inicial
    data_inicial = operacoes_queryset.order_by('data')[0].data
    
    letras_credito = {}
    for operacao in operacoes:
        # Processar operações
        if operacao.letra_credito.id not in letras_credito.keys():
            letras_credito[operacao.letra_credito.id] = 0
                
        # Vendas
        if operacao.tipo_operacao == 'V':
            # Remover quantidade da operação de compra
            operacao_compra_id = operacao.operacao_compra_relacionada().id
            for operacao_c in operacoes:
                if (operacao_c.id == operacao_compra_id):
                    operacao.atual = DivisaoOperacaoLC.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
                    operacao_c.atual -= operacao.atual
                    break
                
    # Remover operações de venda e operações de compra totalmente vendidas
    operacoes = [operacao for operacao in operacoes if operacao.tipo_operacao == 'C' and operacao.atual > 0]
    
    # Calcular o valor atualizado do patrimonio
    historico = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, dia])
    
    for operacao in operacoes:
        taxas_dos_dias = dict(historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
        operacao.atual = calcular_valor_atualizado_com_taxas(taxas_dos_dias, operacao.atual, operacao.taxa)
        # Arredondar valores
        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            
    # Preencher os valores nas letras de crédito
    for letra_credito_id in letras_credito.keys():
        letras_credito[letra_credito_id] += sum([operacao.atual for operacao in operacoes if operacao.letra_credito.id == letra_credito_id])
        
        if letras_credito[letra_credito_id] == 0:
            del letras_credito[letra_credito_id]
    
    return letras_credito

def simulador_lci_lca(filtros):
    """
    Simula uma aplicação em LCI/LCA para os valores especificados nos filtros
    Parâmetros:
    Retorno:    Lista de datas (mes a mes) com valores, ex.: [(data, valor),...]
    """
    qtd_atual = filtros['aplicacao']
    data_atual = datetime.date.today()
    resultado = [(data_atual, qtd_atual)]
    if filtros['tipo'] == 'POS':
        for _ in range(filtros['periodo']):
            qtd_dias_uteis = qtd_dias_uteis_no_periodo(data_atual, data_atual + datetime.timedelta(days=30))
            data_atual = data_atual + datetime.timedelta(days=30)
            qtd_atual = calcular_valor_atualizado_com_taxas({Decimal('14.13'): qtd_dias_uteis}, qtd_atual, filtros['percentual_indice'])
            resultado.append((data_atual, qtd_atual))
    return resultado