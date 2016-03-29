# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC
from bagogold.bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito, OperacaoVendaLetraCredito
from decimal import Decimal
from django.db.models import Q

def calcular_valor_lc_ate_dia(dia):
    """ 
    Calcula o valor das letras de crédito no dia determinado
    Parâmetros: Data final
    Retorno: Valor de cada letra de crédito na data escolhida {id_letra: valor_na_data, }
    """
    operacoes_queryset = OperacaoLetraCredito.objects.exclude(data__isnull=True).exclude(data__gte=dia).order_by('-tipo_operacao', 'data') 
    if len(operacoes_queryset) == 0:
        return {}
    operacoes = list(operacoes_queryset)
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.filter(Q(data__lte=dia) | Q(data__isnull=True)).order_by('-data')
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.atual = operacao.quantidade
            try:
                operacao.taxa = historico_porcentagem.filter(data__lte=operacao.data, letra_credito=operacao.letra_credito)[0].porcentagem_di
            except:
                operacao.taxa = historico_porcentagem.get(data__isnull=True, letra_credito=operacao.letra_credito).porcentagem_di
    
    # Pegar data inicial
    data_inicial = operacoes_queryset.order_by('data')[0].data
    
    data_final = HistoricoTaxaDI.objects.filter(data__lte=dia).order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    letras_credito = {}
    
    while data_iteracao <= data_final:
        # Processar operações
        operacoes_do_dia = operacoes_queryset.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            if operacao.letra_credito.id not in letras_credito.keys():
                letras_credito[operacao.letra_credito.id] = 0
                
            # Vendas
            if operacao.tipo_operacao == 'V':
                # Remover quantidade da operação de compra
                for operacao_c in operacoes:
                    if (operacao_c.id == OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao).id):
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
                operacao.atual = Decimal((pow((float(1) + float(taxa_do_dia)/float(100)), float(1)/float(252)) - float(1)) * float(operacao.taxa/100) + float(1)) * operacao.atual
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
    for letra_credito_id in letras_credito.keys():
        for operacao in operacoes:
            if operacao.letra_credito.id == letra_credito_id:
                letras_credito[letra_credito_id] += operacao.atual
    
    return letras_credito

def calcular_valor_lc_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula o valor das letras de crédito da divisão no dia determinado
    Parâmetros: Data final, id da divisão
    Retorno: Valor de cada letra de crédito da divisão na data escolhida {id_letra: valor_na_data, }
    """
    operacoes_divisao_id = DivisaoOperacaoLC.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes_queryset = OperacaoLetraCredito.objects.exclude(data__isnull=True).filter(id__in=operacoes_divisao_id).order_by('-tipo_operacao', 'data') 
    operacoes = list(operacoes_queryset)
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.filter(Q(data__lte=dia) | Q(data__isnull=True)).order_by('-data')
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.atual = DivisaoOperacaoLC.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
            try:
                operacao.taxa = historico_porcentagem.filter(data__lte=operacao.data, letra_credito=operacao.letra_credito)[0].porcentagem_di
            except:
                operacao.taxa = historico_porcentagem.get(data__isnull=True, letra_credito=operacao.letra_credito).porcentagem_di
    
    # Pegar data inicial
    data_inicial = operacoes_queryset.order_by('data')[0].data
    
    data_final = HistoricoTaxaDI.objects.filter(data__lte=dia).order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    letras_credito = {}
    
    while data_iteracao <= data_final:
        # Processar operações
        operacoes_do_dia = operacoes_queryset.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            if operacao.letra_credito.id not in letras_credito.keys():
                letras_credito[operacao.letra_credito.id] = 0
                
            # Vendas
            if operacao.tipo_operacao == 'V':
                # Remover quantidade da operação de compra
                for operacao_c in operacoes:
                    if (operacao_c.id == OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao).id):
                        operacao.atual = (DivisaoOperacaoLC.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade/DivisaoOperacaoLC.objects.get(divisao__id=divisao_id, operacao=operacao_c).quantidade) * operacao_c.atual
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
                operacao.atual = Decimal((pow((float(1) + float(taxa_do_dia)/float(100)), float(1)/float(252)) - float(1)) * float(operacao.taxa/100) + float(1)) * operacao.atual
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
    for letra_credito_id in letras_credito.keys():
        for operacao in operacoes:
            if operacao.letra_credito.id == letra_credito_id:
                letras_credito[letra_credito_id] += operacao.atual
    
    return letras_credito