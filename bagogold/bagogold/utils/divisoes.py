# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD,\
    DivisaoPrincipal

def preencher_operacoes_div_principal(operacao):
    """
    Adiciona a divisão principal à quantidades não alocadas da operação
    """
    # Verificar qual o tipo de investimento da operação
    if isinstance(operacao, OperacaoTitulo):
        divisoes_operacao = DivisaoOperacaoTD.objects.filter(operacao=operacao)
        # Guarda a quantidade alocada para todas as divisões
        qtd_divisoes = 0
        div_principal_ja_inclusa = False
        for divisao in divisoes_operacao:
            qtd_divisoes += divisao.quantidade
            if divisao.divisao_principal():
                div_principal_ja_inclusa = True
        if qtd_divisoes > operacao.quantidade:
            raise Exception('Erro na quantidade total alocada')
        if qtd_divisoes < divisao.quantidade:
            div_principal = DivisaoPrincipal.objects.get()
            if div_principal_ja_inclusa:
                operacao_div_principal = DivisaoOperacaoTD.objects.get(operacao=operacao, divisao=div_principal)
                operacao_div_principal.quantidade += divisao.quantidade - qtd_divisoes
            else:
                operacao_div_principal = DivisaoOperacaoTD(operacao=operacao, divisao=div_principal, quantidade=(divisao.quantidade - qtd_divisoes))
            operacao_div_principal.save()