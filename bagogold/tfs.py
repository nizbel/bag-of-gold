# -*- coding: utf-8 -*-
from bagogold.models.acoes import Acao, OperacaoAcao, Provento, HistoricoAcao
from bagogold.models.fii import FII, HistoricoFII
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from yahoo_finance import Share
import datetime
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


def preencher_historico(ticker):
    papel = Share('%s.SA' % (ticker))
    historico = papel.get_historical('2010-01-01', datetime.datetime.now().strftime('%Y-%m-%d'))
    try:
        fii = FII.objects.get(ticker=ticker)
#         print fii
        for dia_papel in historico:
            if not HistoricoFII.objects.filter(fii=fii, data=dia_papel['Date']):
                historico_fii = HistoricoFII(fii=fii, data=dia_papel['Date'], preco_unitario=dia_papel['Close'])
                historico_fii.save()
        return
    except FII.DoesNotExist:
        pass
        
    try:
        acao = Acao.objects.get(ticker=ticker)
#         print acao
        for dia_papel in historico:
            if not HistoricoAcao.objects.filter(acao=acao, data=dia_papel['Date']):
                historico_acao = HistoricoAcao(acao=acao, data=dia_papel['Date'], preco_unitario=dia_papel['Close'])
                historico_acao.save()
        return
    except Acao.DoesNotExist:
        pass
        
def preencher_acoes_completo():
    for acao in Acao.objects.all():
        preencher_historico(acao.ticker)
        
def preencher_fii_completo():
    for fii in FII.objects.all():
        preencher_historico(fii.ticker)

def buscar_ultimos_valores_geral():
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
