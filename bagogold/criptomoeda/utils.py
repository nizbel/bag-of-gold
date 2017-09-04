# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    DivisaoTransferenciaCriptomoeda
from bagogold.criptomoeda.models import OperacaoCriptomoeda, \
    TransferenciaCriptomoeda
from decimal import Decimal
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
