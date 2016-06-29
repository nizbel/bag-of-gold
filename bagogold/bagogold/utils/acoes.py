# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import UsoProventosOperacaoAcao, \
    OperacaoAcao, AcaoProvento, Acao, Provento
from bagogold.bagogold.models.divisoes import DivisaoOperacaoAcao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import OperacaoFII
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_DOWN, ROUND_UP
from django.db.models import Sum, Case, When, IntegerField, F
from itertools import chain
from operator import attrgetter, itemgetter
from urllib2 import Request, urlopen, HTTPError, URLError
import calendar
import datetime
import mechanize
import re

def calcular_operacoes_sem_proventos_por_mes(investidor, operacoes):
    """ 
    Calcula a quantidade de ações compradas sem usar proventos por mes
    Parâmetros: Investidor, Queryset de operações ordenadas por data
    Retorno: Lista de tuplas (data, quantidade)
    """
    lista_ids_operacoes = list()
    usos_proventos = UsoProventosOperacaoAcao.objects.filter()
    for uso_proventos in usos_proventos:
        lista_ids_operacoes.append(uso_proventos.operacao.id)
    
    anos_meses = list()
    for operacao in operacoes:
        ano_mes = (operacao.data.month, operacao.data.year)
        if ano_mes not in anos_meses:
            anos_meses.append(ano_mes)

    graf_gasto_op_sem_prov_mes = list()    
    for mes, ano in anos_meses:
        operacoes_mes = operacoes.filter(data__month=mes, data__year=ano)
        total_mes = 0
        for operacao in operacoes_mes:                      
            if operacao.id not in lista_ids_operacoes:  
#                 print 'Sem uso de proventos'
                total_mes += (operacao.quantidade * operacao.preco_unitario + \
                operacao.emolumentos + operacao.corretagem)
            else:
                qtd_usada = usos_proventos.get(operacao__id=operacao.id).qtd_utilizada
#                 print 'Com uso de proventos: %s' % (qtd_usada)
                total_mes += (operacao.quantidade * operacao.preco_unitario + \
                operacao.emolumentos + operacao.corretagem) - qtd_usada
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 15).timetuple()) * 1000)
        graf_gasto_op_sem_prov_mes += [[data_formatada, float(total_mes)]]
        
    return graf_gasto_op_sem_prov_mes

def calcular_uso_proventos_por_mes(investidor):
    """ 
    Calcula a quantidade de uso de proventos em operações por mes
    Parâmetros: Investidor
    Retorno: Lista de tuplas (data, quantidade)
    """
    lista_ids_operacoes = list()
    usos_proventos = UsoProventosOperacaoAcao.objects.filter()
    for uso_proventos in usos_proventos:
        lista_ids_operacoes.append(uso_proventos.operacao.id)
    
    # Guarda as operações que tiveram uso de proventos
    operacoes = OperacaoAcao.objects.filter(id__in=lista_ids_operacoes)
    
    anos_meses = list()
    for operacao in operacoes:
        ano_mes = (operacao.data.month, operacao.data.year)
        if ano_mes not in anos_meses:
            anos_meses.append(ano_mes)
    
    graf_uso_proventos_mes = list()
    for mes, ano in anos_meses:
        operacoes_mes = operacoes.filter(data__month=mes, data__year=ano)
        total_mes = 0
        for operacao in operacoes_mes:                      
            total_mes += usos_proventos.get(operacao__id=operacao.id).qtd_utilizada
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 15).timetuple()) * 1000)
        graf_uso_proventos_mes += [[data_formatada, float(total_mes)]]
        
    return graf_uso_proventos_mes

def calcular_media_uso_proventos_6_meses(investidor):
    """ 
    Calcula a média de uso de proventos em operações nos últimos 6 meses
    Parâmetros: Investidor
    Retorno: Lista de tuplas (data, quantidade)
    """
    ultimos_6_meses = list()
    lista_ids_operacoes = list()
    usos_proventos = UsoProventosOperacaoAcao.objects.filter()
    for uso_proventos in usos_proventos:
        lista_ids_operacoes.append(uso_proventos.operacao.id)
    
    # Guarda as operações que tiveram uso de proventos
    operacoes = OperacaoAcao.objects.filter(id__in=lista_ids_operacoes)
    
    anos_meses = list()
    for operacao in operacoes:
        ano_mes = (operacao.data.month, operacao.data.year)
        if ano_mes not in anos_meses:
            anos_meses.append(ano_mes)
    
    graf_uso_proventos_mes = list()
    for mes, ano in anos_meses:
        operacoes_mes = operacoes.filter(data__month=mes, data__year=ano)
        total_mes = 0
        for operacao in operacoes_mes:                      
            total_mes += usos_proventos.get(operacao__id=operacao.id).qtd_utilizada
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 15).timetuple()) * 1000)
        # Adicionar a lista de valores e calcular a media
        ultimos_6_meses.append(total_mes)
        if len(ultimos_6_meses) > 6:
            ultimos_6_meses.pop(0)
        media_6_meses = 0
        for valor in ultimos_6_meses:
            media_6_meses += valor
        graf_uso_proventos_mes += [[data_formatada, float(media_6_meses/6)]]
        
    return graf_uso_proventos_mes
    
def calcular_provento_por_mes(investidor, proventos, operacoes):
    """ 
    Calcula a quantidade de proventos em dinheiro recebido por mes
    Parâmetros: Investidor
                Queryset de proventos ordenados por data
                Queryset de operações ordenadas por data
    Retorno: Lista de tuplas (data, quantidade)
    """
    
    anos_meses = list()
    for provento in proventos:
        ano_mes = (provento.data_ex.month, provento.data_ex.year)
        if ano_mes not in anos_meses:
            anos_meses.append(ano_mes)
    
    # Adicionar mes atual caso não tenha sido adicionado
    if (datetime.date.today().month, datetime.date.today().year) not in anos_meses:
        anos_meses.append((datetime.date.today().month, datetime.date.today().year))

    graf_proventos_mes = list()    
    for mes, ano in anos_meses:
#         print '%s %s' % (mes, ano)
        proventos_mes = proventos.filter(data_ex__month=mes, data_ex__year=ano)
        total_mes_div = 0
        total_mes_jscp = 0
        for provento in proventos_mes:                        
            qtd_acoes = operacoes.filter(acao=provento.acao, data__lt=provento.data_ex).aggregate(qtd_acoes=Sum(
                        Case(When(tipo_operacao='C', then=F('quantidade')), When(tipo_operacao='V', then=(F('quantidade')*-1)),
                              output_field=IntegerField())))['qtd_acoes']
            if (qtd_acoes is not None):
                # TODO adicionar frações de proventos em ações
                if provento.tipo_provento == 'D':
                    total_mes_div += qtd_acoes * provento.valor_unitario
                elif provento.tipo_provento == 'J':
                    total_mes_jscp += qtd_acoes * provento.valor_unitario * Decimal(0.85)
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 15).timetuple()) * 1000)
        graf_proventos_mes += [[data_formatada, float(total_mes_div), float(total_mes_jscp)]]
        
    return graf_proventos_mes

def calcular_media_proventos_6_meses(investidor, proventos, operacoes):
    """ 
    Calcula a média de proventos recebida nos últimos 6 meses
    Parâmetros: Investidor
                Queryset de proventos ordenados por data
                Queryset de operações ordenadas por data
    Retorno: Lista de tuplas (data, quantidade)
    """
    # Verifica se há proventos a serem calculados
    if not proventos:
        return list()
    
    ultimos_6_meses = list()
    meses_anos = list()
    # Primeiro valor de mes_ano é o primeiro mês em que foi recebido algum provento
    mes_ano = (proventos[0].data_ex.month, proventos[0].data_ex.year)
    meses_anos.append(mes_ano)
    while mes_ano[0] != datetime.date.today().month or mes_ano[1] != datetime.date.today().year:
        mes_ano = (mes_ano[0] + 1, mes_ano[1])
        if mes_ano[0] > 12:
            mes_ano = (1, mes_ano[1] + 1)
        meses_anos.append(mes_ano)

    graf_proventos_mes = list()    
    for mes, ano in meses_anos:
#         print '%s %s' % (mes, ano)
        proventos_mes = proventos.filter(data_ex__month=mes, data_ex__year=ano)
        total_mes = 0
        for provento in proventos_mes:                        
            qtd_acoes = operacoes.filter(acao=provento.acao, data__lt=provento.data_ex).aggregate(qtd_acoes=Sum(
                        Case(When(tipo_operacao='C', then=F('quantidade')), When(tipo_operacao='V', then=(F('quantidade')*-1)),
                              output_field=IntegerField())))['qtd_acoes']
            if (qtd_acoes is not None):
                if provento.tipo_provento == 'D':
                    total_mes += qtd_acoes * provento.valor_unitario
                elif provento.tipo_provento == 'J':
                    total_mes += qtd_acoes * provento.valor_unitario * Decimal(0.85)
#         print total_mes
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 15).timetuple()) * 1000)
        # Adicionar a lista de valores e calcular a media
        ultimos_6_meses.append(total_mes)
        if len(ultimos_6_meses) > 6:
            ultimos_6_meses.pop(0)
        media_6_meses = 0
        for valor in ultimos_6_meses:
            media_6_meses += valor
        graf_proventos_mes += [[data_formatada, float(media_6_meses/6)]]
        
    return graf_proventos_mes

def calcular_lucro_trade_ate_data(investidor, data):
    """
    Calcula o lucro acumulado em trades até a data especificada
    Parâmetros: Investidor, Data
    Retorno: Lucro/Prejuízo
    """
    trades = OperacaoAcao.objects.exclude(data__isnull=True).filter(investidor=investidor, tipo_operacao='V', destinacao='T', data__lt=data).order_by('data')
    lucro_acumulado = 0
    
    for operacao in trades:
        venda_com_taxas = operacao.quantidade * operacao.preco_unitario - operacao.emolumentos - operacao.corretagem
        
        # Calcular lucro bruto da operação de venda
        # Pegar operações de compra
        # TODO PREPARAR CASO DE MUITAS COMPRAS PARA MUITAS VENDAS
        qtd_compra = 0
        gasto_total_compras = 0
        for operacao_compra in operacao.venda.get_queryset().order_by('compra__preco_unitario'):
            qtd_compra += min(operacao_compra.compra.quantidade, operacao.quantidade)
            # TODO NAO PREVÊ MUITAS COMPRAS PARA MUITAS VENDAS
            gasto_total_compras += (qtd_compra * operacao_compra.compra.preco_unitario + operacao_compra.compra.emolumentos + \
                                    operacao_compra.compra.corretagem)
        
        lucro_bruto_venda = (operacao.quantidade * operacao.preco_unitario - operacao.corretagem - operacao.emolumentos) - \
            gasto_total_compras
        lucro_acumulado += lucro_bruto_venda
        
    return lucro_acumulado

def quantidade_acoes_ate_dia(investidor, ticker, dia, considerar_trade=False):
    """ 
    Calcula a quantidade de ações até dia determinado
    Parâmetros: Investidor
                Ticker da ação
                Dia final
    Retorno: Quantidade de ações
    """
    if considerar_trade:
        operacoes = OperacaoAcao.objects.filter(acao__ticker=ticker, data__lte=dia).exclude(data__isnull=True).order_by('data')
    else:
        operacoes = OperacaoAcao.objects.filter(destinacao='B', acao__ticker=ticker, data__lte=dia).exclude(data__isnull=True).order_by('data')
    # Pega os proventos em ações recebidos por outras ações
    proventos_em_acoes = AcaoProvento.objects.filter(acao_recebida__ticker=ticker, provento__data_ex__lte=dia).exclude(provento__data_ex__isnull=True).order_by('provento__data_ex')
    for provento in proventos_em_acoes:
        provento.data = provento.provento.data_ex
    
    lista_conjunta = sorted(chain(operacoes, proventos_em_acoes), key=attrgetter('data'))
    
    qtd_acoes = 0
    
    for item in lista_conjunta:
        if isinstance(item, OperacaoAcao): 
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                qtd_acoes += item.quantidade
                
            elif item.tipo_operacao == 'V':
                qtd_acoes -= item.quantidade
        
        elif isinstance(item, AcaoProvento): 
            if item.provento.acao.ticker == ticker:
                qtd_acoes += int(item.provento.valor_unitario * qtd_acoes / 100)
            else:
                qtd_acoes += int(item.provento.valor_unitario * quantidade_acoes_ate_dia(item.provento.acao.ticker, item.data) / 100)
    return qtd_acoes

def calcular_qtd_acoes_ate_dia_por_divisao(investidor, dia, divisao_id):
    """ 
    Calcula a quantidade de ações até dia determinado por divisão
    Parâmetros: Investidor
                Dia final
                ID da divisão
    Retorno: Quantidade de ações {ticker: qtd}
    """
    operacoes_divisao_id = DivisaoOperacaoAcao.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
    if len(operacoes_divisao_id) == 0:
        return {}
    operacoes = OperacaoAcao.objects.filter(destinacao='B', id__in=operacoes_divisao_id).exclude(data__isnull=True).order_by('data')
    # Pega os proventos em ações recebidos por outras ações
    proventos_em_acoes = AcaoProvento.objects.filter(provento__acao__in=operacoes.values_list('acao', flat=True), provento__data_ex__lte=dia).exclude(provento__data_ex__isnull=True).order_by('provento__data_ex')
    for provento in proventos_em_acoes:
        provento.acao = provento.acao_recebida
        provento.data = provento.provento.data_ex
    
    lista_conjunta = sorted(chain(operacoes, proventos_em_acoes), key=attrgetter('data'))
    
    qtd_acoes = {}
    
    for item in lista_conjunta:
        if item.acao.ticker not in qtd_acoes:
            qtd_acoes[item.acao.ticker] = 0
                
        if isinstance(item, OperacaoAcao): 
            # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
            item.quantidade = DivisaoOperacaoAcao.objects.get(divisao__id=divisao_id, operacao=item).quantidade
            
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                qtd_acoes[item.acao.ticker] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                qtd_acoes[item.acao.ticker] -= item.quantidade
        
        elif isinstance(item, AcaoProvento): 
            if item.provento.acao.ticker not in qtd_acoes:
                qtd_acoes[item.provento.acao.ticker] = 0
            
            if item.provento.acao.ticker == item.acao_recebida.ticker:
                qtd_acoes[item.acao.ticker] += int(item.provento.valor_unitario * qtd_acoes[item.acao.ticker] / 100)
            else:
                qtd_acoes[item.acao.ticker] += int(item.provento.valor_unitario * qtd_acoes[item.provento.acao.ticker] / 100)
    
    for key, item in qtd_acoes.items():
        if qtd_acoes[key] == 0:
            del qtd_acoes[key]
    
    return qtd_acoes

def calcular_poupanca_proventos_ate_dia(investidor, dia):
    """
    Calcula a quantidade de proventos provisionada até dia determinado
    Parâmetros: Dia da posição de proventos
    Retorno: Quantidade provisionada no dia
    """
    operacoes = OperacaoAcao.objects.filter(destinacao='B', data__lte=dia).order_by('data')

    proventos = Provento.objects.filter(data_ex__lte=dia).order_by('data_ex')
    for provento in proventos:
        provento.data = provento.data_ex
     
    lista_conjunta = sorted(chain(operacoes, proventos),
                            key=attrgetter('data'))
    
    total_proventos = 0
    
    # Guarda as ações correntes para o calculo do patrimonio
    acoes = {}
    # Calculos de patrimonio e gasto total
    for item_lista in lista_conjunta:      
        if item_lista.acao.ticker not in acoes.keys():
            acoes[item_lista.acao.ticker] = 0
            
        # Verifica se é uma compra/venda
        if isinstance(item_lista, OperacaoAcao):   
            # Verificar se se trata de compra ou venda
            if item_lista.tipo_operacao == 'C':
                if item_lista.utilizou_proventos():
                    total_proventos -= item_lista.qtd_proventos_utilizada()
                acoes[item_lista.acao.ticker] += item_lista.quantidade
                
            elif item_lista.tipo_operacao == 'V':
                acoes[item_lista.acao.ticker] -= item_lista.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item_lista, Provento):
            if item_lista.data_pagamento <= datetime.date.today():
                if item_lista.tipo_provento in ['D', 'J']:
                    total_recebido = acoes[item_lista.acao.ticker] * item_lista.valor_unitario
                    if item_lista.tipo_provento == 'J':
                        total_recebido = total_recebido * Decimal(0.85)
                    total_proventos += total_recebido
                    
                elif item_lista.tipo_provento == 'A':
                    provento_acao = item_lista.acaoprovento_set.all()[0]
                    if provento_acao.acao_recebida.ticker not in acoes.keys():
                        acoes[provento_acao.acao_recebida.ticker] = 0
                    acoes_recebidas = int((acoes[item_lista.acao.ticker] * item_lista.valor_unitario ) / 100 )
                    item_lista.total_gasto = acoes_recebidas
                    acoes[provento_acao.acao_recebida.ticker] += acoes_recebidas
                    if provento_acao.valor_calculo_frac > 0:
                        if provento_acao.data_pagamento_frac <= datetime.date.today():
                            total_proventos += (((acoes[item_lista.acao.ticker] * item_lista.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
    
    return total_proventos.quantize(Decimal('0.01'))

# TODO melhorar isso
def calcular_preco_medio_ir(ano):
    class Object(object):
        pass
    operacoes_ano = OperacaoAcao.objects.filter(data__lte='%s-12-31' % (ano), destinacao='B').order_by('data')
    proventos_ano = Provento.objects.exclude(data_ex__isnull=True).filter(data_ex__range=[operacoes_ano[0].data, '%s-12-31' % (ano)]).order_by('data_ex')
    for provento in proventos_ano:
        provento.data = provento.data_ex
    
    lista_eventos = sorted(chain(operacoes_ano, proventos_ano), key=attrgetter('data'))
    
    acoes = {}
    for evento in lista_eventos:
        if evento.acao.ticker not in acoes:
            acoes[evento.acao.ticker] = Object()
            acoes[evento.acao.ticker].quantidade = 0
            acoes[evento.acao.ticker].preco_medio = Decimal(0)
            acoes[evento.acao.ticker].jscp = Decimal(0)
            acoes[evento.acao.ticker].dividendos = Decimal(0)
            acoes[evento.acao.ticker].credito_prox_ano = Decimal(0)
            
        
        # Verificar se é operação
        if isinstance(evento, OperacaoAcao):  
            if evento.tipo_operacao == 'C':
                acoes[evento.acao.ticker].quantidade += evento.quantidade
                acoes[evento.acao.ticker].preco_medio += (evento.quantidade * evento.preco_unitario + \
                    evento.emolumentos + evento.corretagem)
                
            elif evento.tipo_operacao == 'V':
                acoes[evento.acao.ticker].quantidade -= evento.quantidade
                acoes[evento.acao.ticker].preco_medio -= (evento.quantidade * evento.preco_unitario - \
                    evento.emolumentos - evento.corretagem)
        
        # Verificar se é provento
        elif isinstance(evento, Provento):  
            if evento.tipo_provento in ['D', 'J']:
                if evento.data_pagamento >= datetime.date(ano,1,1):
                    total_recebido = acoes[evento.acao.ticker].quantidade * evento.valor_unitario
                    print evento.acao.ticker, acoes[evento.acao.ticker].quantidade, evento.valor_unitario, total_recebido, 'pagos em', evento.data_pagamento
                    if evento.data_pagamento <= datetime.date(ano,12,31):
                        if evento.tipo_provento == 'J':
                            total_recebido = total_recebido * Decimal(0.85)
                            acoes[evento.acao.ticker].jscp += total_recebido
                        else:
                            acoes[evento.acao.ticker].dividendos += total_recebido
                    else:
                        acoes[evento.acao.ticker].credito_prox_ano += total_recebido
                    
                
            elif evento.tipo_provento == 'A':
                provento_acao = evento.acaoprovento_set.all()[0]
                if provento_acao.acao_recebida.ticker not in acoes:
                    acoes[provento_acao.acao_recebida.ticker] = Object()
                    acoes[provento_acao.acao_recebida.ticker].quantidade = 0
                    acoes[provento_acao.acao_recebida.ticker].preco_medio = Decimal(0)
                    acoes[provento_acao.acao_recebida.ticker].jscp = Decimal(0)
                    acoes[provento_acao.acao_recebida.ticker].dividendos = Decimal(0)
                    acoes[provento_acao.acao_recebida.ticker].credito_prox_ano = Decimal(0)
                acoes_recebidas = int((acoes[evento.acao.ticker].quantidade * evento.valor_unitario ) / 100 )
                valor_unitario_acoes_recebidas = Decimal(0)
                acoes[provento_acao.acao_recebida.ticker].preco_medio += (acoes_recebidas * valor_unitario_acoes_recebidas)
                acoes[provento_acao.acao_recebida.ticker].quantidade += acoes_recebidas
#                 if provento_acao.valor_calculo_frac > 0:
#                     if provento_acao.data_pagamento_frac <= datetime.date.today():
#                                 print u'recebido fracionado %s, %s ações de %s a %s' % (total_recebido, acoes[evento.acao.ticker], evento.acao.ticker, evento.valor_unitario)
#                         total_gasto += (((acoes[evento.acao.ticker] * evento.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
#                         total_proventos += (((acoes[evento.acao.ticker] * evento.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac

    for acao in sorted(acoes.keys()):
        if acoes[acao].quantidade > 0:
            print acao, '->', acoes[acao].quantidade, 'a', (acoes[acao].preco_medio/Decimal(acoes[acao].quantidade)), 'Div.:', acoes[acao].dividendos, 'JSCP:', acoes[acao].jscp, 'Ano seguinte:', \
                acoes[acao].credito_prox_ano
            print acao, '->', acoes[acao].quantidade, 'a', Decimal(format(acoes[acao].preco_medio/Decimal(acoes[acao].quantidade), '.2f')), 'Div.:', Decimal(format(acoes[acao].dividendos, '.2f')), \
                                                                   'JSCP:', Decimal(format(acoes[acao].jscp, '.2f')), 'Ano seguinte:', acoes[acao].credito_prox_ano
            
    fiis = {}
    for operacao in OperacaoFII.objects.filter(data__lte='%s-12-31' % (ano)).order_by('data'):
        if operacao.fii.ticker not in fiis:
            fiis[operacao.fii.ticker] = Object()
            fiis[operacao.fii.ticker].quantidade = 0
            fiis[operacao.fii.ticker].preco_medio = Decimal(0)
            
        if operacao.tipo_operacao == 'C':
            fiis[operacao.fii.ticker].quantidade += operacao.quantidade
            fiis[operacao.fii.ticker].preco_medio += (operacao.quantidade * operacao.preco_unitario + \
                operacao.emolumentos + operacao.corretagem)
            
        elif operacao.tipo_operacao == 'V':
            fiis[operacao.fii.ticker].quantidade -= operacao.quantidade
            fiis[operacao.fii.ticker].preco_medio -= (operacao.quantidade * operacao.preco_unitario - \
                operacao.emolumentos - operacao.corretagem)
    
    for fii in fiis.keys():
        if fiis[fii].quantidade > 0:
            print fii, '->', fiis[fii].quantidade, 'a', (fiis[fii].preco_medio/Decimal(fiis[fii].quantidade))

def buscar_proventos_acao(codigo_cvm, ticker, num_tentativas):
    """
    Busca proventos de ações no site da Bovespa
    """
    # Busca os dados dos proventos em 2 URLs da bovespa
    # Proventos em dinheiro
    prov_dinheiro_url = 'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/ResumoEventosCorporativos.aspx?codigoCvm=%s&tab=3.0&idioma=pt-br' % (codigo_cvm)
    # Usar mechanize para simular clique do usuario no javascript
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    response = br.open(prov_dinheiro_url)
    
    html = response.read()

    br.select_form(nr=0)
    br.set_all_readonly(False)
    mnext = re.search("""<a.*?href=\"javascript:__doPostBack\('(.*?)','(.*?)'\)\".*?id=\"ctl00_contentPlaceHolderConteudo_MenuEmpresasListadas1_tabMenuEmpresa_tabEventosCorporativos_tabProventosDinheiro\".*?>\*?Proventos em dinheiro""", html, re.IGNORECASE)
    if not mnext:
        print 'not found'
        return
    br["__EVENTTARGET"] = mnext.group(1)
    br["__EVENTARGUMENT"] = mnext.group(2)
    br.find_control("ctl00$botaoNavegacaoVoltar").disabled = True
    response = br.submit()
    html = response.read()
    if 'Sistema indisponivel' in html:
        if num_tentativas == 3:
            raise URLError('Sistema indisponível')
            return
        return buscar_proventos_acao(codigo_cvm, ticker, num_tentativas+1)
    
    inicio = html.find('<tbody>')
#         print 'inicio', inicio
    fim = html.find('</tbody>', inicio)
    string_importante = (html[inicio:fim])
    proventos_dinheiro_texto = re.findall('<tr.*?>(.*?)<\/tr>', string_importante, flags=re.DOTALL)
    proventos_dinheiro = list()
    for texto_provento in proventos_dinheiro_texto:
        provento = re.findall('<td.*?>(.*?)<\/td>', texto_provento)
        if provento:
            provento[5] = datetime.datetime.strptime(provento[5],'%d/%m/%Y').date() + datetime.timedelta(days=1)
            while provento[5].weekday() > 4:
                provento[5] += datetime.timedelta(days=1)
            proventos_dinheiro.append(provento)
    proventos_dinheiro = sorted(proventos_dinheiro, key=itemgetter(5))
#     for provento_dinheiro in proventos_dinheiro:
#         print provento_dinheiro
        
    # Busca todos os proventos
    prov_url = 'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/ResumoEventosCorporativos.aspx?codigoCvm=%s&tab=3.0&idioma=pt-br' % (codigo_cvm)
    req = Request(prov_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        data = response.read()
        if 'Sistema indisponivel' in data:
            if num_tentativas == 3:
                raise URLError('Sistema indisponível')
                return
            return buscar_proventos_acao(codigo_cvm, ticker, num_tentativas+1)
        inicio = data.find('<div id="divDividendo">')
#         print 'inicio', inicio
        fim = data.find('<div id="divSubscricao">', inicio)
        string_importante = (data[inicio:fim])
        proventos = re.findall('<tr.*?>(.*?)<\/tr>', string_importante, flags=re.DOTALL)
        contador = 1
        total = 0
        for provento in proventos:
            texto_provento = re.findall('<td.*?>(.*?)<\/td>', provento)
            texto_provento += re.findall('<span.*?>(.*?)<\/span>', provento)
            if texto_provento:
#                 print texto_provento
                # Criar provento
                data_ex = datetime.datetime.strptime(texto_provento[2],'%d/%m/%Y').date() + datetime.timedelta(days=1)
                # Incrementa data até que não seja fim de semana
                while data_ex.weekday() > 4:
                    data_ex += datetime.timedelta(days=1)
                    
                # Preparar data pagamento (pode ser vazia)
                try:
                    data_pagamento = datetime.datetime.strptime(texto_provento[6],'%d/%m/%Y').date()
                except:
                    data_pagamento = None
                provento = Provento(acao=Acao.objects.get(ticker=ticker), valor_unitario=Decimal(texto_provento[3].replace(',', '.')), tipo_provento=texto_provento[0][0], \
                                    data_pagamento=data_pagamento, observacao=texto_provento[7], data_ex=data_ex)
                
#                 print provento
                for provento_dinheiro in proventos_dinheiro:
                    if provento_dinheiro[5] == data_ex:
#                             print provento_dinheiro
                        valor = Decimal(quantidade_acoes_ate_dia(ticker, datetime.datetime.strptime(texto_provento[2],'%d/%m/%Y').date(), True))
                        if valor > 0:
                            if (provento_dinheiro[4][0] == 'R'):
                                valor *= Decimal(provento_dinheiro[2].replace(',', '.')) * Decimal(0.775)
                                print valor, valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
                                total += valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
                            elif (provento_dinheiro[4][0] == 'J'):
                                valor *= Decimal(provento_dinheiro[2].replace(',', '.')) * Decimal(0.85)
                                texto_valor = str(valor)
#                                 print len(texto_valor[texto_valor.find('.')+1:]), texto_valor[texto_valor.find('.')+1:], texto_valor[texto_valor.find('.')+1:][1]
                                if len(texto_valor[texto_valor.find('.')+1:]) > 2 and int(texto_valor[texto_valor.find('.')+1:][1]) % 2 != 0:
                                    print valor, valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
                                    total += valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
                                else:
                                    print valor, valor.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                                    total += valor.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                            else:
                                valor *= Decimal(provento_dinheiro[2].replace(',', '.'))
                                print valor, valor.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                                total += valor.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                            # Remover elemento da lista (evitar duplicidade)
                            proventos_dinheiro = [x for x in proventos_dinheiro if x[5] != data_ex]
                contador += 1
    print ticker, total
                    
def preencher_codigos_cvm():
    """
    Preenche códigos bvmf para as ações a partir das urls na listagem de empresas
    """
    acao_url = 'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/BuscaEmpresaListada.aspx?idioma=pt-br'
    req = Request(acao_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        data = response.read()
        if 'Sistema indisponivel' in data:
            return preencher_codigos_cvm()
        inicio = data.find('<div class="inline-list-letra">')
        fim = data.find('</div>', inicio)
        string_importante = (data[inicio:fim])
        letras = re.findall('<a.*?>(.*?)<\/a>', string_importante, flags=re.DOTALL)
#         print letras
        # Buscar empresas
        empresas = Empresa.objects.all()
        for letra in letras:
            letra_url = 'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/BuscaEmpresaListada.aspx?Letra=%s&idioma=pt-br' % letra
            req = Request(letra_url)
            conectou = False
            while not conectou:
                try:
                    response = urlopen(req)
                except HTTPError as e:
                    print 'The server couldn\'t fulfill the request.'
                    print 'Error code: ', e.code
                except URLError as e:
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
                else:
                    data = response.read()
                    if 'Sistema indisponivel' not in data:
                        conectou = True
            inicio = data.find('<tbody>')
            fim = data.find('</tbody>', inicio)
            string_importante = (data[inicio:fim])
            urls = re.findall('<a.*?codigoCvm=(.*?)\">(.*?)<\/a>', string_importante, flags=re.DOTALL)
            for codigo, nome in urls:
                if nome in empresas.values_list('nome_pregao', flat=True):
                    empresa = empresas.filter(nome_pregao=nome).order_by('-id')[0]
                    empresa.codigo_cvm = codigo
                    empresa.save()
#                     print 'Salvou empresa', empresa