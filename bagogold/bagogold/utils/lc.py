# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC
from bagogold.bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito
from decimal import Decimal

def calcular_valor_lc_ate_dia(dia):
    """ 
    Calcula o valor das letras de crédito no dia determinado
    Parâmetros: Data final
    Retorno: Valor de cada letra de crédito na data escolhida
    """
    operacoes = OperacaoLetraCredito.objects.exclude(data__isnull=True).exclude(data__gte=dia).order_by('data')  
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.filter(data__lte=dia) 
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        operacao.taxa = historico_porcentagem.filter(data__lte=operacao.data).order_by('-data')[0].porcentagem_di
    
    if len(operacoes) == 0:
        return {}
    
    # Pegar data inicial
    data_inicial = operacoes[0].data
    
    data_final = HistoricoTaxaDI.objects.filter(data__lte=dia).order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    letras_credito = {}
    
    while data_iteracao <= data_final:
        # Processar operações
        operacoes_do_dia = operacoes.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            if operacao.letra_credito.id not in letras_credito.keys():
                letras_credito[operacao.letra_credito.id] = 0
                
            # TODO Implementar vendas
                
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
    Retorno: Valor de cada letra de crédito da divisão na data escolhida
    """
    operacoes_divisao_id = DivisaoOperacaoLC.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('id')
    operacoes = OperacaoLetraCredito.objects.exclude(data__isnull=True).filter(id__in=operacoes_divisao_id).order_by('data')  
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.filter(data__lte=dia) 
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        operacao.taxa = historico_porcentagem.filter(data__lte=operacao.data).order_by('-data')[0].porcentagem_di
    
    # Pegar data inicial
    data_inicial = operacoes[0].data
    
    data_final = HistoricoTaxaDI.objects.filter(data__lte=dia).order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    letras_credito = {}
    
    while data_iteracao <= data_final:
        # Processar operações
        operacoes_do_dia = operacoes.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            if operacao.letra_credito.id not in letras_credito.keys():
                letras_credito[operacao.letra_credito.id] = 0
                
            # TODO Implementar vendas
                
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