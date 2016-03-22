# -*- coding: utf-8 -*-
from bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI
from decimal import Decimal

def calcular_valor_lc_ate_dia(dia):
    """ 
    Calcula o valor das letras de crédito no dia determinado
    Parâmetros: Data final
    Retorno: Valor somado das letras de crédito
    """
    operacoes = OperacaoLetraCredito.objects.exclude(data__isnull=True, data__lte=dia).order_by('data')  
    
    # Pegar data inicial
    data_inicial = operacoes[0].data
    
    data_iteracao = data_inicial
    
    letras_credito = {}
    total_patrimonio = 0
    
    while data_iteracao <= dia:
        # Processar operações
        operacoes_do_dia = operacoes.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            if operacao.letra_credito not in letras_credito.keys():
                letras_credito[operacao.letra_credito] = 0
            # Verificar se se trata de compra ou venda
            if operacao.tipo_operacao == 'C':
                operacao.tipo = 'Compra'
                operacao.total = operacao.quantidade
                letras_credito[operacao.letra_credito] += operacao.quantidade
                total_patrimonio += operacao.total
                    
            elif operacao.tipo_operacao == 'V':
                operacao.tipo = 'Venda'
                operacao.total = operacao.quantidade
                letras_credito[operacao.letra_credito] -= operacao.quantidade
                total_patrimonio -= operacao.total
                
        # Calcular o valor atualizado do patrimonio diariamente
        total_patrimonio = 0
        for letra_credito in letras_credito:
            taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
            # TODO preparar rendimento da letra
            letras_credito[letra_credito] = Decimal((pow((float(1) + float(taxa_do_dia)/float(100)), float(1)/float(252)) - float(1)) * float(0.8) + float(1)) * letras_credito[letra_credito]
            # Arredondar
            letras_credito[letra_credito] = letras_credito[letra_credito].quantize(Decimal('.01'))
            total_patrimonio += letras_credito[letra_credito]
            
        # Proximo dia útil
        proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
        if len(proximas_datas) > 0:
            data_iteracao = proximas_datas[0].data
        else:
            break
    
    return total_patrimonio
