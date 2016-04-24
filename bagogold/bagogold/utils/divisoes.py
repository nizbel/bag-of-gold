# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD, \
    DivisaoPrincipal, DivisaoOperacaoLC, DivisaoOperacaoFII, DivisaoOperacaoAcao
from bagogold.bagogold.models.fii import OperacaoFII
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo
from django.apps import apps

def preencher_operacoes_div_principal(operacao):
    """
    Adiciona a divisão principal à quantidades não alocadas da operação
    """
    # Verificar qual o tipo de investimento da operação
    # Ação (B&H)
    if isinstance(operacao, OperacaoAcao):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoAcao')
        divisoes_operacao = DivisaoOperacaoAcao.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get().divisao 
    # FII
    elif isinstance(operacao, OperacaoFII):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoFII')
        divisoes_operacao = DivisaoOperacaoFII.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get().divisao
    # LC
    elif isinstance(operacao, OperacaoLetraCredito):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoLC')
        divisoes_operacao = DivisaoOperacaoLC.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get().divisao
    # TD
    else:
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoTD')
        divisoes_operacao = DivisaoOperacaoTD.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get().divisao
        
    # Guarda a quantidade alocada para todas as divisões
    qtd_divisoes = 0
    div_principal_ja_inclusa = False
    for divisao_operacao in divisoes_operacao:
        qtd_divisoes += divisao_operacao.quantidade
        if divisao_operacao.divisao.divisao_principal():
            div_principal_ja_inclusa = True
    if qtd_divisoes > operacao.quantidade:
        raise Exception('Erro na quantidade total alocada')
    elif qtd_divisoes < operacao.quantidade:
        if operacao.tipo_operacao == 'C':
            if div_principal_ja_inclusa:
                operacao_div_principal = modelo_operacao_div.objects.get(operacao=operacao, divisao=div_principal)
                operacao_div_principal.quantidade += operacao.quantidade - qtd_divisoes
                print 'Adicionado %s a divisão principal' % (operacao.quantidade - qtd_divisoes)
            else:
                operacao_div_principal = modelo_operacao_div(operacao=operacao, divisao=div_principal, quantidade=(operacao.quantidade - qtd_divisoes))
                print 'Criada divisão principal para alocar %s' % (operacao.quantidade - qtd_divisoes)
            print operacao_div_principal.operacao
            operacao_div_principal.save()
    else:
        print 'Operação %s totalmente alocada' % (operacao)
        
def verificar_operacao_nao_alocada():
    """
    Procura operações que não tenham sido totalmente alocadas em divisões
    """
    operacoes_nao_alocadas = []
    for operacao in OperacaoAcao.objects.filter():
        divisoes_operacao = DivisaoOperacaoAcao.objects.filter(operacao=operacao)
        quantidade_alocada = 0
        for divisao in divisoes_operacao:
            quantidade_alocada += divisao.quantidade
        if quantidade_alocada < operacao.quantidade:
            operacoes_nao_alocadas.append(operacao)
    
    # Adicionar alocação a pendencia do investidor
    if len(operacoes_nao_alocadas) > 0:
        return True
    return False