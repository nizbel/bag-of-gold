# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao
from bagogold.cdb_rdb.models import OperacaoCDB_RDB
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD, \
    DivisaoPrincipal, DivisaoOperacaoLC, DivisaoOperacaoFII, DivisaoOperacaoAcao, \
    Divisao, DivisaoOperacaoFundoInvestimento, DivisaoOperacaoCDB_RDB
from bagogold.bagogold.models.fii import OperacaoFII
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.fundo_investimento.models import OperacaoFundoInvestimento
from django.apps import apps

def preencher_operacoes_div_principal(operacao):
    """
    Adiciona a divisão principal à quantidades não alocadas da operação
    """
    # Verificar qual o tipo de investimento da operação
    # Ação
    if isinstance(operacao, OperacaoAcao):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoAcao')
        divisoes_operacao = DivisaoOperacaoAcao.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get(investidor=operacao.investidor).divisao 
    # CDB/RDB
    elif isinstance(operacao, OperacaoCDB_RDB):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoCDB_RDB')
        divisoes_operacao = DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get(investidor=operacao.investidor).divisao
    # Fundo de Investimento
    elif isinstance(operacao, OperacaoFundoInvestimento):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoFundoInvestimento')
        divisoes_operacao = DivisaoOperacaoFundoInvestimento.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get(investidor=operacao.investidor).divisao
    # FII
    elif isinstance(operacao, OperacaoFII):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoFII')
        divisoes_operacao = DivisaoOperacaoFII.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get(investidor=operacao.investidor).divisao
    # LC
    elif isinstance(operacao, OperacaoLetraCredito):
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoLC')
        divisoes_operacao = DivisaoOperacaoLC.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get(investidor=operacao.investidor).divisao
    # TD
    else:
        modelo_operacao_div = apps.get_model('bagogold', 'DivisaoOperacaoTD')
        divisoes_operacao = DivisaoOperacaoTD.objects.filter(operacao=operacao)
        div_principal = DivisaoPrincipal.objects.get(investidor=operacao.investidor).divisao
        
    # Guarda a quantidade alocada para todas as divisões
    qtd_divisoes = 0
    div_principal_ja_inclusa = False
    for divisao_operacao in divisoes_operacao:
        qtd_divisoes += divisao_operacao.quantidade
        if divisao_operacao.divisao.divisao_principal():
            div_principal_ja_inclusa = True
    print operacao, qtd_divisoes
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
            operacao_div_principal.save()
    else:
        print 'Operação %s totalmente alocada' % (operacao)
        
def verificar_operacoes_nao_alocadas(investidor):
    """
    Procura operações que não tenham sido totalmente alocadas em divisões
    """
    operacoes_nao_alocadas = []
    # Ações
    for operacao in OperacaoAcao.objects.filter(investidor=investidor):
        divisoes_operacao = DivisaoOperacaoAcao.objects.filter(operacao=operacao)
        quantidade_alocada = 0
        for divisao in divisoes_operacao:
            quantidade_alocada += divisao.quantidade
        if quantidade_alocada < operacao.quantidade:
            print quantidade_alocada, operacao.quantidade, operacao.destinacao
            if operacao.destinacao == 'B':
                operacao.tipo = 'Ações (B & H)'
            elif operacao.destinacao == 'T':
                operacao.tipo = 'Ações (Trading)'
            operacao.quantidade_nao_alocada = operacao.quantidade - quantidade_alocada
            operacoes_nao_alocadas.append(operacao)
    
    # CDB/RDB
    for operacao in OperacaoCDB_RDB.objects.filter(investidor=investidor):
        divisoes_operacao = DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao)
        quantidade_alocada = 0
        for divisao in divisoes_operacao:
            quantidade_alocada += divisao.quantidade
        if quantidade_alocada < operacao.quantidade:
            operacao.tipo = 'CDB/RDB'
            operacao.quantidade_nao_alocada = operacao.quantidade - quantidade_alocada
            operacoes_nao_alocadas.append(operacao)
    
    # FII
    for operacao in OperacaoFII.objects.filter(investidor=investidor):
        divisoes_operacao = DivisaoOperacaoFII.objects.filter(operacao=operacao)
        quantidade_alocada = 0
        for divisao in divisoes_operacao:
            quantidade_alocada += divisao.quantidade
        if quantidade_alocada < operacao.quantidade:
            operacao.tipo = 'FII'
            operacao.quantidade_nao_alocada = operacao.quantidade - quantidade_alocada
            operacoes_nao_alocadas.append(operacao)
            
    # Fundo de investimento
    for operacao in OperacaoFundoInvestimento.objects.filter(investidor=investidor):
        divisoes_operacao = DivisaoOperacaoFundoInvestimento.objects.filter(operacao=operacao)
        quantidade_alocada = 0
        for divisao in divisoes_operacao:
            quantidade_alocada += divisao.quantidade
        if quantidade_alocada < operacao.quantidade:
            operacao.tipo = 'Fundo Inv.'
            operacao.quantidade_nao_alocada = operacao.quantidade - quantidade_alocada
            operacoes_nao_alocadas.append(operacao)
    
    # LC
    for operacao in OperacaoLetraCredito.objects.filter(investidor=investidor):
        divisoes_operacao = DivisaoOperacaoLC.objects.filter(operacao=operacao)
        quantidade_alocada = 0
        for divisao in divisoes_operacao:
            quantidade_alocada += divisao.quantidade
        if quantidade_alocada < operacao.quantidade:
            operacao.tipo = 'Letra de Crédito'
            operacao.quantidade_nao_alocada = operacao.quantidade - quantidade_alocada
            operacoes_nao_alocadas.append(operacao)
    
    # TD
    for operacao in OperacaoTitulo.objects.filter(investidor=investidor):
        divisoes_operacao = DivisaoOperacaoTD.objects.filter(operacao=operacao)
        quantidade_alocada = 0
        for divisao in divisoes_operacao:
            quantidade_alocada += divisao.quantidade
        if quantidade_alocada < operacao.quantidade:
            operacao.tipo = 'Tesouro Direto'
            operacao.quantidade_nao_alocada = operacao.quantidade - quantidade_alocada
            operacoes_nao_alocadas.append(operacao)
    
    # Adicionar alocação a pendencia do investidor
    if len(operacoes_nao_alocadas) > 0:
        pass
    return operacoes_nao_alocadas

# TODO repensar isso
def calcular_saldo_geral_acoes_bh():
    saldo_geral = 0
    for divisao in Divisao.objects.all():
        saldo_geral += divisao.saldo_acoes_bh()
    return saldo_geral