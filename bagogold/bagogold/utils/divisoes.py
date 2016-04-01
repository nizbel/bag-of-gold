# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD, \
    DivisaoPrincipal, DivisaoOperacaoLC, DivisaoOperacaoFII
from bagogold.bagogold.models.fii import OperacaoFII
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo
from django.apps import apps

def preencher_operacoes_div_principal(operacao):
    """
    Adiciona a divisão principal à quantidades não alocadas da operação
    """
    # Verificar qual o tipo de investimento da operação
    # FII
    if isinstance(operacao, OperacaoFII):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoFII')
        print modelo_operacao_div
        divisoes_operacao = DivisaoOperacaoFII.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get()
    # LC
    elif isinstance(operacao, OperacaoLetraCredito):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoLC')
        print modelo_operacao_div
        divisoes_operacao = DivisaoOperacaoLC.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get()
    # TD
    else:
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoTD')
        print modelo_operacao_div
        divisoes_operacao = DivisaoOperacaoTD.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get()
        
    # Guarda a quantidade alocada para todas as divisões
    qtd_divisoes = 0
    div_principal_ja_inclusa = False
    for divisao in divisoes_operacao:
        qtd_divisoes += divisao.quantidade
        if divisao.divisao_principal():
            div_principal_ja_inclusa = True
    if qtd_divisoes > operacao.quantidade:
        raise Exception('Erro na quantidade total alocada')
    elif qtd_divisoes < divisao.quantidade:
        if operacao.tipo_operacao == 'C':
            if div_principal_ja_inclusa:
                operacao_div_principal = modelo_operacao_div.objects.get(operacao=operacao, divisao=div_principal)
                operacao_div_principal.quantidade += divisao.quantidade - qtd_divisoes
            else:
                operacao_div_principal = modelo_operacao_div(operacao=operacao, divisao=div_principal, quantidade=(divisao.quantidade - qtd_divisoes))
            print operacao_div_principal, operacao_div_principal.operacao
#             operacao_div_principal.save()
    else:
        print 'Operação %s totalmente alocada' % (operacao)