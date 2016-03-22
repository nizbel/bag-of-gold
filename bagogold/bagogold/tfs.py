# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, OperacaoAcao, Provento, HistoricoAcao
from bagogold.bagogold.models.fii import FII, HistoricoFII
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from urllib2 import Request, urlopen, URLError, HTTPError
from yahoo_finance import Share
import datetime
import pyexcel
import simplejson
import time

# Para buscar valor de multiplas acoes
try:
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


def buscar_historico(ticker):
    try:
        historico = list()
        response_csv = urlopen('http://ichart.finance.yahoo.com/table.csv?s=%s.SA&a=0&b=01&c=2010&d=%s&e=%s&f=%s&g=d&ignore=.csv' % \
                               (ticker, int(datetime.date.today().month), datetime.date.today().day, datetime.date.today().year))
        csv = response_csv.read()
        book = pyexcel.get_book(file_type="csv", file_content=csv)
        sheets = book.to_dict()
        for key in sheets.keys():
            dados_papel = sheets[key]
            for linha in range(1,len(dados_papel)):
                # Testar se a linha de data está vazia, passar ao proximo
                if dados_papel[linha][0] == '':
                    break
                dados_data = {}
                dados_data['Date'] = dados_papel[linha][0]
                dados_data['Close'] = dados_papel[linha][4]
                historico.append(dados_data)
    except:
        papel = Share('%s.SA' % (ticker))
        historico = papel.get_historical('2010-01-01', datetime.datetime.now().strftime('%Y-%m-%d'))
    
    return historico
        
def preencher_historico_acao(ticker, historico):
    acao = Acao.objects.get(ticker=ticker)
#         print acao
    for dia_papel in historico:
        if not HistoricoAcao.objects.filter(acao=acao, data=dia_papel['Date']):
            historico_acao = HistoricoAcao(acao=acao, data=dia_papel['Date'], preco_unitario=Decimal(dia_papel['Close']).quantize(Decimal('0.01')))
            historico_acao.save()
    return

def preencher_historico_fii(ticker, historico):
    fii = FII.objects.get(ticker=ticker)
#         print fii
    for dia_papel in historico:
        if not HistoricoFII.objects.filter(fii=fii, data=dia_papel['Date']):
            historico_fii = HistoricoFII(fii=fii, data=dia_papel['Date'], preco_unitario=Decimal(dia_papel['Close']).quantize(Decimal('0.01')))
            historico_fii.save()
    return
        
def buscar_ultimos_valores_geral_acao():
    # Dados para a conexão
    PUBLIC_API_URL  = 'http://query.yahooapis.com/v1/public/yql'
    DATATABLES_URL  = 'store://datatables.org/alltableswithkeys'
    connection = HTTPConnection('query.yahooapis.com')
    
    # Preparar acoes a serem buscadas
    acoes_formatadas = ''
    for acao in Acao.objects.all():
        acoes_formatadas += '%s.SA ' % (acao.ticker)
    acoes_formatadas.strip()
    
    yql = 'select * from yahoo.finance.quotes where symbol = "%s"' % (acoes_formatadas)
    connection.request('GET', PUBLIC_API_URL + '?' + urlencode({ 'q': yql, 'format': 'json', 'env': DATATABLES_URL }))
    resultado = simplejson.loads(connection.getresponse().read())
    
    # Preencher valores de ultimas negociacoes
    valores_diarios = {}
    
    for dados in resultado['query']['results']['quote']:
        valores_diarios[dados['Symbol']] = dados['LastTradePriceOnly']
    return valores_diarios

def buscar_ultimos_valores_geral_fii():
    # Dados para a conexão
    PUBLIC_API_URL  = 'http://query.yahooapis.com/v1/public/yql'
    DATATABLES_URL  = 'store://datatables.org/alltableswithkeys'
    connection = HTTPConnection('query.yahooapis.com')
    
    # Preparar acoes a serem buscadas
    fiis_formatados = ''
    for fii in FII.objects.all():
        fiis_formatados += '%s.SA ' % (fii.ticker)
    fiis_formatados.strip()
    
    yql = 'select * from yahoo.finance.quotes where symbol = "%s"' % (fiis_formatados)
    connection.request('GET', PUBLIC_API_URL + '?' + urlencode({ 'q': yql, 'format': 'json', 'env': DATATABLES_URL }))
    resultado = simplejson.loads(connection.getresponse().read())
    
    # Preencher valores de ultimas negociacoes
    valores_diarios = {}
    
    for dados in resultado['query']['results']['quote']:
        valores_diarios[dados['Symbol']] = dados['LastTradePriceOnly']
    return valores_diarios

# TODO TEST THIS
def buscar_historico_geral():
    # Dados para a conexão
    PUBLIC_API_URL  = 'http://query.yahooapis.com/v1/public/yql'
    DATATABLES_URL  = 'store://datatables.org/alltableswithkeys'
    connection = HTTPConnection('query.yahooapis.com')
    
    # Preparar acoes a serem buscadas
    acoes_formatadas = ''
    for acao in Acao.objects.all():
        acoes_formatadas += '%s.SA ' % (acao.ticker)
    acoes_formatadas.strip()
    
    yql = 'select * from yahoo.finance.quotes where symbol = "%s"' % (acoes_formatadas)
    connection.request('GET', PUBLIC_API_URL + '?' + urlencode({ 'q': yql, 'format': 'json', 'env': DATATABLES_URL }))
    resultado = simplejson.loads(connection.getresponse().read())
    
    # Preencher valores de ultimas negociacoes
    valores_diarios = {}
    
    for dados in resultado['query']['results']['quote']:
        valores_diarios[dados['Symbol']] = dados['LastTradePriceOnly']
    return valores_diarios
