# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao
from bagogold.bagogold.models.fii import OperacaoFII
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import HistoricoIPCA, OperacaoTitulo
from decimal import Decimal
from itertools import chain
from operator import attrgetter
from urllib2 import Request, urlopen, URLError, HTTPError
import datetime
import math
import re


def calcular_iof_regressivo(dias):
    return Decimal(max((100 - (dias * 3 + math.ceil((float(dias)/3)))), 0)/100)

def buscar_historico_ipca():
    td_url = 'http://www.portalbrasil.net/ipca.htm'
    req = Request(td_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
#         print 'Host: %s' % (req.get_host())
        data = response.read()
#         print data
        string_importante = (data[data.find('simplificada'):
                                 data.find('FONTES')])
#         print string_importante
        linhas = re.findall('<tr.*?>.*?</tr>', string_importante, re.MULTILINE|re.DOTALL|re.IGNORECASE)
        for linha in linhas[1:]:
            linha = re.sub('<.*?>', '', linha, flags=re.MULTILINE|re.DOTALL|re.IGNORECASE)
            linha = linha.replace(' ', '').replace('&nbsp;', '')
            campos = re.findall('([\S]*)', linha, re.MULTILINE|re.DOTALL|re.IGNORECASE)
            campos = filter(bool, campos)
#             print campos
            for mes in range(1,13):
                try:
#                     print 'Ano:', campos[0], 'Mes:', mes, 'Valor:', Decimal(campos[mes].replace(',', '.'))
                    historico_ipca = HistoricoIPCA(ano=int(campos[0]), mes=mes, valor=Decimal(campos[mes].replace(',', '.')))
                    historico_ipca.save()
                except:
                    print 'Não foi possível converter', campos[mes]
               
def buscar_valores_diarios_selic(data_inicial, data_final):
    """
    Retorna os valores da taxa SELIC pelo site do Banco Central
    Parâmetros: Data inicial
                Data final
    Retorno: Lista com tuplas (data, fator diário)
    """
    # from bagogold.bagogold.utils.misc import buscar_valores_diarios_selic
    # http://www3.bcb.gov.br/selic/consulta/taxaSelic.do?method=listarTaxaDiaria&dataInicial=11/11/2016&dataFinal=16/11/2016&tipoApresentacao=arquivo
    td_url = 'http://www3.bcb.gov.br/selic/consulta/taxaSelic.do?method=listarTaxaDiaria&dataInicial=11/11/2016&dataFinal=16/11/2016&tipoApresentacao=arquivo'
    req = Request(td_url)
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
#         print data
        # data vem como um arquivo txt separado por linhas com \n e delimitado por ;
        linhas = data.split('\n')
        # ler a partir da terceira linha
        for linha in linhas[2:]:
            if len(linha.split(';')) > 2:
                print linha.split(';')[0], linha.split(';')[2]
     
def trazer_primeiro_registro(queryset):
    """
    Traz o primeiro registro de um queryset
    Parâmetros: Queryset
    Retorno: Primeiro registro ou nulo
    """
    resultado = list(queryset[:1])
    if resultado:
        return resultado[0]
    return None

def calcular_domingo_pascoa_no_ano(ano):
    """
    Calcula o domingo de páscoa para o ano especificado. Usado para achar as datas dos feriados eclesiásticos
    Parâmetros: Ano
    Retorno: Dia do domingo de páscoa no ano
    """
    numero_dourado = (ano % 19)
    # Verificar na tabela
    """
    1  14 de abril
    2   3 de abril
    3  23 de março
    4  11 de abril
    5  31 de março
    6  18 de abril
    7   8 de abril
    8  28 de março
    9  16 de abril
    10  5 de abril
    11 25 de março
    12 13 de abril
    13  2 de abril
    14 22 de março
    15 10 de abril
    16 30 de março
    17 17 de abril
    18  7 de abril
    19 27 de março
    """
    data_encontrada = ['14/4', '3/4', '23/3', '11/4', '31/3', '18/4', '8/4', '28/3', '16/4', '5/4', '25/3', '13/4', '2/4', '22/3', '10/4', '30/3', '17/4', '7/4', '27/3'][numero_dourado]
    data_encontrada = datetime.date(ano, int(data_encontrada.split('/')[1]), int(data_encontrada.split('/')[0]))
    # Verifica os próximos 7 dias a fim de encontrar o próximo domingo
    semana_generator = [data_encontrada + datetime.timedelta(days=x) for x in xrange(7)]
    for dia in semana_generator:
        if dia.weekday() == 6:
            return dia
    
def verificar_feriado_bovespa(data):
    """
    Verifica se o dia informado é feriado na Bovespa
    Parâmetros: Data
    Retorno: É feriado?
    """
    dia_mes = (data.day, data.month)
    # Calcular feriados dependentes da páscoa
    domingo_pascoa = calcular_domingo_pascoa_no_ano(data.year)
    carnaval = domingo_pascoa - datetime.timedelta(days=47)
    sexta_santa = domingo_pascoa - datetime.timedelta(days=2)
    corpus_christi = domingo_pascoa + datetime.timedelta(days=60)
    lista_feriados = ((1, 1), # Confraternização Universal
                      (carnaval.day, carnaval.month), # Carnaval
                      (sexta_santa.day, sexta_santa.month), # Sexta-feira santa
                      (corpus_christi.day, corpus_christi.month), # Corpus Christi
                      (21, 4), # Tiradentes
                      (1, 5), # Dia do trabalho
                      (7, 9), # Independência do Brasil
                      (12, 10), # Nossa Senhora Aparecida
                      (2, 11), # Finados
                      (15, 11), # Proclamação da República
                      (25, 12), # Natal
                      (31, 12), # Ano novo
                      )
    return (dia_mes in lista_feriados)

def qtd_dias_uteis_no_periodo(data_inicial, data_final):
    """
    Calcula a quantidade de dias úteis entre as datas enviadas, incluindo a primeira e excluindo a segunda
    Parâmetros: Data inicial (inclusiva)
                Data final (exclusiva)
    Retorno: Número de dias entre as datas
    """
    # Se data final menor que inicial, retornar erro
    if data_final < data_inicial:
        raise ValueError('Data final deve ser igual ou maior que data inicial')
    daygenerator = (data_inicial + datetime.timedelta(days=x) for x in xrange((data_final - data_inicial).days))
    return sum(1 for day in daygenerator if day.weekday() < 5 and not verificar_feriado_bovespa(day))

