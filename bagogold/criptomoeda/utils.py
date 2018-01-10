# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    DivisaoTransferenciaCriptomoeda, Divisao
from bagogold.criptomoeda.models import OperacaoCriptomoeda, \
    TransferenciaCriptomoeda, Criptomoeda, OperacaoCriptomoedaTaxa, \
    OperacaoCriptomoedaMoeda
from decimal import Decimal
from django.db import transaction
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When
from django.db.models.fields import DecimalField
from urllib2 import urlopen
import datetime
import json

def calcular_qtd_moedas_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de moedas até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de moedas por fundo {moeda_id: qtd}
    """
    # Pega primeiro moedas operadas
    qtd_moedas1 = dict(OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia).values('criptomoeda') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('criptomoeda', 'total').exclude(total=0))
    
    # Moedas utilizadas, sem taxas
    qtd_moedas2 = dict(OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, operacaocriptomoedamoeda__isnull=False,
                                                          operacaocriptomoedataxa__isnull=True) \
                       .annotate(moeda_utilizada=F('operacaocriptomoedamoeda__criptomoeda')).values('moeda_utilizada') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade') * F('preco_unitario') *-1),
                            When(tipo_operacao='V', then=F('quantidade') * F('preco_unitario')),
                            output_field=DecimalField()))).values_list('moeda_utilizada', 'total').exclude(total=0))
    
    # Moedas utilizadas, com taxas
    qtd_moedas3 = dict(OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, operacaocriptomoedamoeda__isnull=False,
                                                          operacaocriptomoedataxa__isnull=False) \
                       .annotate(moeda_utilizada=F('operacaocriptomoedamoeda__criptomoeda')).values('moeda_utilizada') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', \
                  # Para compras, verificar se taxa está na moeda comprada ou na utilizada
                  then=Case(When(operacaocriptomoedataxa__moeda=F('criptomoeda'), 
                                 then=(F('quantidade') + F('operacaocriptomoedataxa__valor')) * F('preco_unitario') *-1),
                            When(operacaocriptomoedataxa__moeda=F('operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('quantidade') * F('preco_unitario') *-1 - F('operacaocriptomoedataxa__valor')))),
                                 When(tipo_operacao='V', \
                  # Para vendas, verificar se a taxa está na moeda vendida ou na utilizada
                  then=Case(When(operacaocriptomoedataxa__moeda=F('criptomoeda'), 
                                 then=(F('quantidade') - F('operacaocriptomoedataxa__valor')) * F('preco_unitario')),
                            When(operacaocriptomoedataxa__moeda=F('operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('quantidade') * F('preco_unitario') - F('operacaocriptomoedataxa__valor')))),
                        output_field=DecimalField()))).values_list('moeda_utilizada', 'total').exclude(total=0))
    
    # Transferências, remover taxas
    qtd_moedas4 = dict(TransferenciaCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, moeda__isnull=False).values('moeda') \
        .annotate(total=Sum(F('taxa')*-1)).values_list('moeda', 'total').exclude(total=0))
    
    qtd_moedas = { k: qtd_moedas1.get(k, 0) + qtd_moedas2.get(k, 0) + qtd_moedas3.get(k, 0) + qtd_moedas4.get(k, 0) \
                   for k in set(qtd_moedas1) | set(qtd_moedas2) | set(qtd_moedas3) | set(qtd_moedas4) }
    
    return qtd_moedas

def calcular_qtd_moedas_ate_dia_por_criptomoeda(investidor, moeda_id, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de moedas até dia determinado para uma criptomoeda
    Parâmetros: Investidor
                ID da Criptomoeda
                Dia final
    Retorno: Quantidade de moedas para a criptomoeda determinada
    """
    # Pega primeiro moedas operadas
    qtd_moedas = OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, criptomoeda__id=moeda_id) \
        .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField())))['total'] or 0
    
    # Moedas utilizadas, sem taxas
    qtd_moedas += OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, operacaocriptomoedamoeda__criptomoeda__id=moeda_id,
                                                          operacaocriptomoedataxa__isnull=True) \
        .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade') * F('preco_unitario') *-1),
                            When(tipo_operacao='V', then=F('quantidade') * F('preco_unitario')),
                            output_field=DecimalField())))['total'] or 0
    
    # Moedas utilizadas, com taxas
    qtd_moedas += OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, operacaocriptomoedamoeda__criptomoeda__id=moeda_id,
                                                          operacaocriptomoedataxa__isnull=False) \
        .aggregate(total=Sum(Case(When(tipo_operacao='C', \
                  # Para compras, verificar se taxa está na moeda comprada ou na utilizada
                  then=Case(When(operacaocriptomoedataxa__moeda=F('criptomoeda'), 
                                 then=(F('quantidade') + F('operacaocriptomoedataxa__valor')) * F('preco_unitario') *-1),
                            When(operacaocriptomoedataxa__moeda=F('operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('quantidade') * F('preco_unitario') *-1 - F('operacaocriptomoedataxa__valor')))),
                                 When(tipo_operacao='V', \
                  # Para vendas, verificar se a taxa está na moeda vendida ou na utilizada
                  then=Case(When(operacaocriptomoedataxa__moeda=F('criptomoeda'), 
                                 then=(F('quantidade') - F('operacaocriptomoedataxa__valor')) * F('preco_unitario')),
                            When(operacaocriptomoedataxa__moeda=F('operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('quantidade') * F('preco_unitario') - F('operacaocriptomoedataxa__valor')))),
                        output_field=DecimalField())))['total'] or 0
    
    # Transferências, remover taxas
    qtd_moedas += TransferenciaCriptomoeda.objects.filter(investidor=investidor, data__lte=dia, moeda__id=moeda_id) \
        .aggregate(total=Sum(F('taxa')*-1))['total'] or 0
        
    return qtd_moedas

def calcular_qtd_moedas_ate_dia_por_divisao(divisao_id, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de moedas até dia determinado para uma divisão
    Parâmetros: Id da divisão
                Dia final
    Retorno: Quantidade de moedas {moeda_id: qtd}
    """
    # Pega primeiro moedas operadas
    qtd_moedas1 = dict(DivisaoOperacaoCriptomoeda.objects.filter(divisao__id=divisao_id, operacao__data__lte=dia) \
                       .values('operacao__criptomoeda') \
        .annotate(total=Sum(Case(When(operacao__tipo_operacao='C', then=F('operacao__quantidade')),
                            When(operacao__tipo_operacao='V', then=F('operacao__quantidade')*-1),
                            output_field=DecimalField()))).values_list('operacao__criptomoeda', 'total').exclude(total=0))
    
    # Moedas utilizadas, sem taxas
    qtd_moedas2 = dict(DivisaoOperacaoCriptomoeda.objects.filter(divisao__id=divisao_id, operacao__data__lte=dia, 
                                                                 operacao__operacaocriptomoedamoeda__isnull=False,
                                                                 operacao__operacaocriptomoedataxa__isnull=True) \
                       .values('operacao__operacaocriptomoedamoeda__criptomoeda') \
        .annotate(total=Sum(Case(When(operacao__tipo_operacao='C', then=F('operacao__quantidade') * F('operacao__preco_unitario') *-1),
                            When(operacao__tipo_operacao='V', then=F('operacao__quantidade') * F('operacao__preco_unitario')),
                            output_field=DecimalField()))).values_list('operacao__operacaocriptomoedamoeda__criptomoeda', 'total').exclude(total=0))
     
    # Moedas utilizadas, com taxas
    qtd_moedas3 = dict(DivisaoOperacaoCriptomoeda.objects.filter(divisao__id=divisao_id, operacao__data__lte=dia, 
                                                          operacao__operacaocriptomoedamoeda__isnull=False,
                                                          operacao__operacaocriptomoedataxa__isnull=False) \
                       .values('operacao__operacaocriptomoedamoeda__criptomoeda') \
        .annotate(total=Sum(Case(When(operacao__tipo_operacao='C', \
                  # Para compras, verificar se taxa está na moeda comprada ou na utilizada
                  then=Case(When(operacao__operacaocriptomoedataxa__moeda=F('operacao__criptomoeda'), 
                                 then=(F('operacao__quantidade') + F('operacao__operacaocriptomoedataxa__valor')) * F('operacao__preco_unitario') *-1),
                            When(operacao__operacaocriptomoedataxa__moeda=F('operacao__operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('operacao__quantidade') * F('operacao__preco_unitario') *-1 - F('operacao__operacaocriptomoedataxa__valor')))),
                                 When(operacao__tipo_operacao='V', \
                  # Para vendas, verificar se a taxa está na moeda vendida ou na utilizada
                  then=Case(When(operacao__operacaocriptomoedataxa__moeda=F('operacao__criptomoeda'), 
                                 then=(F('operacao__quantidade') - F('operacao__operacaocriptomoedataxa__valor')) * F('operacao__preco_unitario')),
                            When(operacao__operacaocriptomoedataxa__moeda=F('operacao__operacaocriptomoedamoeda__criptomoeda'), 
                                 then=F('operacao__quantidade') * F('operacao__preco_unitario') - F('operacao__operacaocriptomoedataxa__valor')))),
                        output_field=DecimalField()))).values_list('operacao__operacaocriptomoedamoeda__criptomoeda', 'total').exclude(total=0))
     
    # Transferências, remover taxas
    qtd_moedas4 = dict(DivisaoTransferenciaCriptomoeda.objects.filter(divisao__id=divisao_id, transferencia__data__lte=dia, 
                                                                      transferencia__moeda__isnull=False).values('transferencia__moeda') \
        .annotate(total=Sum(F('transferencia__taxa')*-1)).values_list('transferencia__moeda', 'total').exclude(total=0))
     
    qtd_moedas = { k: qtd_moedas1.get(k, 0) + qtd_moedas2.get(k, 0) + qtd_moedas3.get(k, 0) + qtd_moedas4.get(k, 0) \
                   for k in set(qtd_moedas1) | set(qtd_moedas2) | set(qtd_moedas3) | set(qtd_moedas4) }

    return qtd_moedas

def buscar_valor_criptomoeda_atual(criptomoeda_ticker):
    """ 
    Busca o valor atual de uma criptomoeda pela API do CryptoCompare
    Parâmetros: Ticker da criptomoeda
    Retorno: Valor atual
    """
    url = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms=%s&tsyms=BRL' % (criptomoeda_ticker)
    resultado = urlopen(url)
    dados = json.load(resultado) 
    return Decimal(dados[criptomoeda_ticker]['BRL'])

def buscar_valor_criptomoedas_atual(lista_tickers):
    """ 
    Busca o valor atual de várias criptomoedas pela API do CryptoCompare
    Parâmetros: Lista com os tickers das criptomoedas
    Retorno: Valores atuais {ticker: valor_atual}
    """
    url = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms=%s&tsyms=BRL' % (','.join(lista_tickers))
    resultado = urlopen(url)
    dados = json.load(resultado) 
    return {ticker: Decimal(str(dados[ticker.upper()]['BRL'])) for ticker in lista_tickers if ticker.upper() in dados.keys()}

def buscar_valor_criptomoedas_atual_varias_moedas(lista_tickers, lista_moedas):
    """ 
    Busca o valor atual de várias criptomoedas pela API do CryptoCompare
    Parâmetros: Lista com os tickers das criptomoedas
                Lista com as moedas utilizadas
    Retorno: Valores atuais {ticker: {moeda: valor, }, }
    """
    url = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms=%s&tsyms=%s' % (','.join(lista_tickers), ','.join(lista_moedas))
    resultado = urlopen(url)
    dados = json.load(resultado) 
    return {ticker: dados[ticker.upper()] for ticker in lista_tickers if ticker.upper() in dados.keys()}

def buscar_historico_criptomoeda(criptomoeda_ticker):
    """ 
    Busca os valores históricos de uma criptomoeda pela API do CryptoCompare
    Parâmetros: Ticker da criptomoeda
    Retorno: Tuplas com data e valor [(data, valor_na_data)]
    """
    url = 'https://min-api.cryptocompare.com/data/histoday?fsym=%s&tsym=BRL&allData=true' % criptomoeda_ticker
    resultado = urlopen(url)
    dados = json.load(resultado) 
    
    historico = list()
    for informacao in dados['Data']:
        data = datetime.date.fromtimestamp(informacao['time'])
        historico.append((data, Decimal(informacao['close'])))
    
    return historico

def criar_operacoes_lote(lista_operacoes, investidor, divisao_id, salvar=False):
    """
    Cria várias operações com base em uma lista de strings com ponto e vírgula como separador, 
    vinculando a uma única divisão. Retorna os objetos criados
    Parâmetros: Lista de strings
                Investidor
                ID da divisão
                Indicador se operações devem ser salvas na base
    Retorno: Lista com objetos referentes a operações em criptomoedas
    """
    if len(lista_operacoes) > 20:
        raise ValueError('Tamanho do lote é de no máximo 20 operações')
    
    if not Divisao.objects.filter(investidor=investidor, id=divisao_id).exists():
        raise ValueError('Investidor não possui a divisão enviada')
    divisao = Divisao.objects.get(id=divisao_id)
    
    objetos_operacoes = list()
    houve_erro = False
    lista_erros = list()
    for operacao_string in lista_operacoes:
        try:
            infos = operacao_string.split(';')
            if len(infos) != 7:
                raise ValueError('Informações devem estar no formato indicado')
            if len(infos[0].split('/')) != 2:
                raise ValueError('Moedas devem estar no formato MOEDA/MOEDA_UTILIZADA')
            if infos[0].split('/')[0] == infos[0].split('/')[1]:
                raise ValueError('Moeda comprada/vendida não pode ser igual a moeda utilizada')
            moeda = Criptomoeda.objects.get(ticker=infos[0].split('/')[0])
            moeda_utilizada = infos[0].split('/')[1]
            quantidade = Decimal(infos[1].replace('.', '').replace(',', '.'))
            if quantidade <= 0:
                raise ValueError('Quantidade deve ser maior que 0')
            preco_unitario = Decimal(infos[2].replace('.', '').replace(',', '.'))
            if preco_unitario < 0:
                raise ValueError('Preço unitário não pode ser negativo')
            data = datetime.datetime.strptime(infos[3], '%d/%m/%Y').date()
            tipo_operacao = infos[4]
            valor_taxa = Decimal(infos[5].replace('.', '').replace(',', '.'))
            if valor_taxa < 0:
                raise ValueError('Valor da taxa não pode ser negativo')
            moeda_taxa = infos[6]
            if moeda_taxa != moeda.ticker and moeda_taxa != moeda_utilizada:
                raise ValueError('Moeda utilizada para taxa deve ser uma das 2 moedas utilizadas na operação')
            
            # Criar objetos
            operacao = OperacaoCriptomoeda(quantidade=quantidade, preco_unitario=preco_unitario, data=data, tipo_operacao=tipo_operacao, 
                                                          criptomoeda=moeda, investidor=investidor)
            objetos_operacoes.append(operacao)
            
            objetos_operacoes.append(DivisaoOperacaoCriptomoeda(operacao=operacao, divisao=divisao, quantidade=quantidade))
            
            if moeda_utilizada != 'BRL':
                objetos_operacoes.append(OperacaoCriptomoedaMoeda(operacao=operacao, criptomoeda=Criptomoeda.objects.get(ticker=moeda_utilizada)))
            
            if valor_taxa > 0:
                if moeda_taxa != 'BRL':
                    objetos_operacoes.append(OperacaoCriptomoedaTaxa(valor=valor_taxa, operacao=operacao, 
                                                                     moeda=Criptomoeda.objects.get(ticker=moeda_taxa)))
                else:
                    objetos_operacoes.append(OperacaoCriptomoedaTaxa(valor=valor_taxa, operacao=operacao))
        except Exception as e:
            houve_erro = True
            lista_erros.append(str(e))
    if houve_erro:
        raise ValueError('\n'.join(lista_erros))
    
    return objetos_operacoes

# def salvar_operacoes_lote(lista_operacoes, investidor, divisao_id):
#     """
#     Salva operações criadas em lote
#     Parâmetros: Lista de strings
#                 Investidor
#                 ID da divisão
#     """
#     operacoes = criar_operacoes_lote(lista_operacoes, investidor, divisao_id)
#     try:
#         with transaction.atomic():
#             for objeto_operacao in operacoes:
#                 objeto_operacao.save()
#     except:
#         raise
# #         raise ValueError('Houve um erro ao salvar as operações geradas em lote')

def criar_transferencias_lote(lista_transferencias, investidor, divisao_id):
    """
    Cria várias transferências com base em uma lista de strings com ponto e vírgula como separador, 
    vinculando a uma única divisão. Retorna os objetos criados
    Parâmetros: Lista de strings
                Investidor
                ID da divisão
    Retorno: Lista com objetos referentes a transferências em criptomoedas
    """
    if len(lista_transferencias) > 20:
        raise ValueError('Tamanho do lote é de no máximo 20 transferências')
     
    if not Divisao.objects.filter(investidor=investidor, id=divisao_id).exists():
        raise ValueError('Investidor não possui a divisão enviada')
    divisao = Divisao.objects.get(id=divisao_id)
     
    houve_erro = False
    lista_erros = list()
    for transferencia_string in lista_transferencias:
        try:
            infos = transferencia_string.split(';')
            if len(infos) != 6:
                raise ValueError('Informações devem estar no formato indicado')
            moeda = infos[0]
            if moeda not in ['BRL',] or moeda not in Criptomoeda.objects.all().values_list('ticker', flat=True):
                raise ValueError('Moeda inválida')
            quantidade = Decimal(infos[1].replace('.', '').replace(',', '.'))
            if quantidade <= 0:
                raise ValueError('Quantidade deve ser maior que 0')
            origem = infos[2]
            if len(origem) > 50:
                raise ValueError('Nome da origem deve ser de no máximo 50 caracteres')
            destino = infos[3]
            if len(destino) > 50:
                raise ValueError('Nome da origem deve ser de no máximo 50 caracteres')
            data = datetime.datetime.strptime(infos[4], '%d/%m/%Y').date()
            taxa = Decimal(infos[5].replace('.', '').replace(',', '.'))
            if taxa < 0:
                raise ValueError('Valor da taxa não pode ser negativo')
             
            # Criar objetos
            transferencia = TransferenciaCriptomoeda.objects.create(quantidade=quantidade, data=data, origem=origem, destino=destino,
                                                                    taxa=taxa, moeda=moeda, investidor=investidor)
             
            DivisaoTransferenciaCriptomoeda.objects.create(transferencia=transferencia, divisao=divisao, quantidade=quantidade)
        except Exception as e:
            houve_erro = True
            lista_erros.append(str(e))
    if houve_erro:
        raise ValueError('\n'.join(lista_erros))
                         
def salvar_transferencias_lote(lista_transferencias, investidor, divisao_id):
    """
    Salva transferências criadas em lote
    Parâmetros: Lista de strings
                Investidor
                ID da divisão
    """
    transferencias = criar_transferencias_lote(lista_transferencias, investidor, divisao_id)
    try:
        with transaction.atomic():
            for objeto_operacao in transferencias:
                objeto_operacao.save()
    except:
        raise ValueError('Houve um erro ao salvar as transferências geradas em lote')