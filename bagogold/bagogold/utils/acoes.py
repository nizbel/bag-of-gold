# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import UsoProventosOperacaoAcao, \
    OperacaoAcao, AcaoProvento, Acao, Provento
from decimal import Decimal
from django.db.models import Sum, Case, When, IntegerField, F
from itertools import chain
from operator import attrgetter
from urllib2 import Request, urlopen, HTTPError, URLError
import calendar
import datetime
import re

def calcular_operacoes_sem_proventos_por_mes(operacoes):
    """ 
    Calcula a quantidade de ações compradas sem usar proventos por mes
    Parâmetros: Queryset de operações ordenadas por data
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

def calcular_uso_proventos_por_mes():
    """ 
    Calcula a quantidade de uso de proventos em operações por mes
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

def calcular_media_uso_proventos_6_meses():
    """ 
    Calcula a média de uso de proventos em operações nos últimos 6 meses
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
    
def calcular_provento_por_mes(proventos, operacoes):
    """ 
    Calcula a quantidade de proventos em dinheiro recebido por mes
    Parâmetros: Queryset de proventos ordenados por data
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

def calcular_media_proventos_6_meses(proventos, operacoes):
    """ 
    Calcula a média de proventos recebida nos últimos 6 meses
    Parâmetros: Queryset de proventos ordenados por data
                Queryset de operações ordenadas por data
    Retorno: Lista de tuplas (data, quantidade)
    """
    
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

def quantidade_acoes_ate_dia(ticker, dia):
    """ 
    Calcula a quantidade de ações até dia determinado
    Parâmetros: Ticker da ação
                Dia final
    Retorno: Quantidade de ações
    """
    operacoes = OperacaoAcao.objects.filter(destinacao='B', acao__ticker=ticker, data__lte=dia).exclude(data__isnull=True).order_by('data')
    # Pega os proventos em ações recebidos por outras ações
    proventos_em_acoes = AcaoProvento.objects.filter(acao_recebida__ticker=ticker).order_by('provento__data_ex')
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

def buscar_proventos_acao(ticker):
    """
    Busca proventos de ações no site da Bovespa
    """
    acao_url = 'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/ResumoEventosCorporativos.aspx?codigoCvm=1023&tab=3&idioma=pt-br'
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
            return buscar_proventos_acao(ticker)
        inicio = data.find('<div id="divDividendo">')
#         print 'inicio', inicio
        fim = data.find('<div id="divSubscricao">', inicio)
        string_importante = (data[inicio:fim])
        proventos = re.findall('<tr.*?>(.*?)<\/tr>', string_importante, flags=re.DOTALL)
        contador = 1
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
                provento = Provento(acao=Acao.objects.get(ticker='BBAS3'), valor_unitario=Decimal(texto_provento[3].replace(',', '.')), tipo_provento=texto_provento[0][0], \
                                    data_pagamento=datetime.datetime.strptime(texto_provento[6],'%d/%m/%Y').date(), observacao=texto_provento[7], data_ex=data_ex)
                print provento
                try:
                    teste_prov = Provento.objects.get(acao__ticker='BBAS3', tipo_provento=texto_provento[0][0], data_pagamento=datetime.datetime.strptime(texto_provento[6],'%d/%m/%Y').date())
                    print contador, teste_prov
                    contador += 1
                except Provento.DoesNotExist:
                    print 'Nao achou'