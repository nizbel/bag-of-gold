# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, HistoricoAcao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import FII, HistoricoFII
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from threading import Thread
from urllib2 import Request, urlopen
from yahoo_finance import Share
import datetime
import pyexcel
import simplejson

# Para buscar valor de multiplas acoes
try:
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
    
# Variável global para guardar resultados de busca de últimos valores diários
resultados_diarios_acao = {}
resultados_diarios_fii = {}

def ler_serie_historica_anual_bovespa(nome_arquivo):
    # Carregar FIIs disponíveis
    fiis = FII.objects.all()
    acoes = Acao.objects.all()
    fiis_lista = fiis.values_list('ticker', flat=True)
    acoes_lista = acoes.values_list('ticker', flat=True)
    with open(nome_arquivo) as f:
        content = f.readlines()
        for line in content[1:len(content)-1]:
#             if line[2:10] == '20160215':
            data = datetime.date(int(line[2:6]), int(line[6:8]), int(line[8:10]))
            valor = Decimal(line[108:119] + '.' + line[119:121])
            ticker = line[12:24].strip()
            if ticker in fiis_lista:
                objeto, criado = HistoricoFII.objects.update_or_create(fii=fiis.get(ticker=ticker), data=data, defaults={'preco_unitario':valor, 'oficial_bovespa': True})
                if criado:
                    print ticker, 'em', data, 'criado'
            elif line[39:41] == 'ON' or (line[39:41] == 'PN'):
                if len(ticker) == 5 and int(ticker[4]) in [3,4,5,6,7,8]:
#                     print line[12:24], line[39:49]
                    if ticker in acoes_lista:
                        objeto, criado = HistoricoAcao.objects.update_or_create(acao=acoes.get(ticker=ticker), data=data, defaults={'preco_unitario':valor, 'oficial_bovespa': True})
                        if criado:
                            print ticker, 'em', data, 'criado (Histórico)'
                    else:
                        empresa_existe = False
                        for acao_listada in acoes_lista:
                            if ticker[0:4] in acao_listada:
#                                 print 'Inserido'
                                empresa_existe = True
                                empresa = Acao.objects.get(ticker=acao_listada).empresa
                                break
                        if not empresa_existe:
                            empresa = Empresa(nome=line[27:39].strip(), nome_pregao=line[27:39].strip())
                            empresa.save()
                        acao = Acao(ticker=ticker, empresa=empresa)
                        acao.save()
                        objeto, criado = HistoricoAcao.objects.update_or_create(acao=acao, data=data, defaults={'preco_unitario':valor, 'oficial_bovespa': True})
                        print ticker, 'em', data, 'criado (TICKER)'
                        acoes = Acao.objects.all()
                        acoes_lista = acoes.values_list('ticker', flat=True)
                        
            

def buscar_historico(ticker):
    try:
        historico = list()
        response_csv = urlopen('http://ichart.finance.yahoo.com/table.csv?s=%s.SA&a=0&b=01&c=%s&d=%s&e=%s&f=%s&g=d&ignore=.csv' % \
                               (ticker, datetime.date.today().year, int(datetime.date.today().month), datetime.date.today().day, datetime.date.today().year))
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
    except Exception as ex:
#         template = "An exception of type {0} occured. Arguments:\n{1!r}"
#         message = template.format(type(ex).__name__, ex.args)
#         print ticker, ":", message
        try:
            papel = Share('%s.SA' % (ticker))
            historico = papel.get_historical('%s-01-01' % (datetime.date.today().year), datetime.datetime.now().strftime('%Y-%m-%d'))
        except Exception as ex:
#             template = "An exception of type {0} occured. Arguments:\n{1!r}"
#             message = template.format(type(ex).__name__, ex.args)
#             print ticker, ":", message
            return list()
#         print historico
    
    return historico
        
def preencher_historico_acao(ticker, historico):
    acao = Acao.objects.get(ticker=ticker)
    if len(historico) > 0 and 'Date' not in historico[0]:
        print acao, historico
    for dia_papel in historico:
        if not HistoricoAcao.objects.filter(acao=acao, data=dia_papel['Date']):
            historico_acao = HistoricoAcao(acao=acao, data=dia_papel['Date'], preco_unitario=Decimal(dia_papel['Close']).quantize(Decimal('0.01')))
            historico_acao.save()
    return

def preencher_historico_fii(ticker, historico):
    fii = FII.objects.get(ticker=ticker)
#     print fii
    for dia_papel in historico:
        if not HistoricoFII.objects.filter(fii=fii, data=dia_papel['Date']):
            historico_fii = HistoricoFII(fii=fii, data=dia_papel['Date'], preco_unitario=Decimal(dia_papel['Close']).quantize(Decimal('0.01')))
            historico_fii.save()
    return

# Threads usadas para buscar ultimos valores diários no yahoo finance
class BuscarValoresDiariosAcaoThread(Thread):
    def __init__(self, tickers, indice_thread):
        self.tickers = tickers 
        self.indice_thread = indice_thread
        super(BuscarValoresDiariosAcaoThread, self).__init__()

    def run(self):
        try:
            # Dados para a conexão
            PUBLIC_API_URL  = 'http://query.yahooapis.com/v1/public/yql'
            DATATABLES_URL  = 'store://datatables.org/alltableswithkeys'
            connection = HTTPConnection('query.yahooapis.com')
    
            yql = 'select Symbol, LastTradePriceOnly from yahoo.finance.quotes where symbol = "%s"' % (self.tickers)
            connection.request('GET', PUBLIC_API_URL + '?' + urlencode({ 'q': yql, 'format': 'json', 'env': DATATABLES_URL }))
            resultado = simplejson.loads(connection.getresponse().read())
            resultados_diarios_acao[self.indice_thread] = resultado
#             print self.indice_thread
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print self.indice_thread, "Thread:", message
            pass
        
class BuscarValoresDiariosFIIThread(Thread):
    def __init__(self, tickers, indice_thread):
        self.tickers = tickers 
        self.indice_thread = indice_thread
        super(BuscarValoresDiariosFIIThread, self).__init__()

    def run(self):
        try:
            # Dados para a conexão
            PUBLIC_API_URL  = 'http://query.yahooapis.com/v1/public/yql'
            DATATABLES_URL  = 'store://datatables.org/alltableswithkeys'
            connection = HTTPConnection('query.yahooapis.com')
    
            yql = 'select Symbol, LastTradePriceOnly from yahoo.finance.quotes where symbol = "%s"' % (self.tickers)
            connection.request('GET', PUBLIC_API_URL + '?' + urlencode({ 'q': yql, 'format': 'json', 'env': DATATABLES_URL }))
            resultado = simplejson.loads(connection.getresponse().read())
            resultados_diarios_fii[self.indice_thread] = resultado
#             print self.indice_thread
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print self.indice_thread, "Thread:", message
            pass
        
def buscar_ultimos_valores_geral_acao():
    resultados_diarios_acao.clear()
    
    # Preparar acoes a serem buscadas
    qtd_por_query = 120
    acoes = Acao.objects.all()
    
    # Preparar threads
    threads = []
    valores_diarios = {}
    for indice, grupo_acoes in enumerate([acoes[i:i+qtd_por_query] for i in range(0, len(acoes), qtd_por_query)]):
        acoes_formatadas = ''
        for acao in grupo_acoes:
            acoes_formatadas += '%s.SA ' % (acao.ticker)
        acoes_formatadas.strip()
        t = BuscarValoresDiariosAcaoThread(acoes_formatadas, indice)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
        
    # Preencher valores de ultimas negociacoes
    for resultado in resultados_diarios_acao.values():
        for dados in resultado['query']['results']['quote']:
            valores_diarios[dados['Symbol']] = dados['LastTradePriceOnly']
    return valores_diarios

def buscar_ultimos_valores_geral_fii():
    resultados_diarios_fii.clear()
       
    # Preparar fiis a serem buscados
    qtd_por_query = 120
    fiis = FII.objects.all()
    
    # Preparar threads
    threads = []
    valores_diarios = {}
    for indice, grupo_fiis in enumerate([fiis[i:i+qtd_por_query] for i in range(0, len(fiis), qtd_por_query)]):
        fiis_formatados = ''
        for fii in grupo_fiis:
            fiis_formatados += '%s.SA ' % (fii.ticker)
        fiis_formatados.strip()
        t = BuscarValoresDiariosFIIThread(fiis_formatados, indice)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # Preencher valores de ultimas negociacoes
    for resultado in resultados_diarios_fii.values():
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

