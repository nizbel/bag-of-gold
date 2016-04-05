# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII
from random import randint
from threading import Thread
from urllib2 import Request, urlopen, URLError, HTTPError
import datetime
import re
import simplejson
import sys
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

class BuscaTickerThread(Thread):
    def __init__(self, ticker):
        self.ticker = ticker 
        super(BuscaTickerThread, self).__init__()

    def run(self):
        try:
            busca_ticker(self.ticker, 0)
        except:
            print sys.exc_info()[1]
            pass


def verificar_fiis_listados():
#     http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=AEFI&tipoFundo=Imobiliario&aba=abaPrincipal&idioma=pt-br
    # Verificar siglas listadas
    fii_url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListados.aspx?tipoFundo=imobiliario&amp;Idioma=pt-br'
    req = Request(fii_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        print 'Host: %s' % (req.get_host())
        data = response.read()
        string_importante = (data[data.find('<table>'):data.find('</table>')])
#         urls = re.findall('[h]?[t]?[t]?[p]?[s]?[:]?[\/]?[\/]?(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.xls', string_importante)
        siglas = re.findall('[A-Za-z0-9]+', re.sub(r'.*?<tr>.*?<td>.*?<\/td>.*?<td>.*?<\/td>.*?<td>.*?<\/td>.*?<td><span.*?>(.*?)<\/span><\/td>.*?<\/tr>.*?', r'\1,', string_importante, flags=re.DOTALL))
        threads = []
        start_time = time.time()
        for sigla in siglas:
            t = BuscaTickerThread(sigla)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        print time.time() - start_time, len(siglas)
            

def busca_ticker(sigla, num_tentativas):
    tempo_espera = randint(1,max(1, 30-(num_tentativas*10)))
    time.sleep(tempo_espera)
    sigla_url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=abaPrincipal&idioma=pt-br' % (sigla)
    resposta = urlopen(sigla_url)
    string_retorno = resposta.read()
    if 'Sistema indisponivel' in string_retorno:
#         tempo_espera = randint(max(1, 3-num_tentativas),max(2, 8-num_tentativas))
#         print sigla, ": sistema indisponivel, tentando novamente em %s segundos" % (tempo_espera)
#         time.sleep(tempo_espera)
        busca_ticker(sigla, num_tentativas+1)
        return
    string_importante = string_retorno[string_retorno.find('Códigos de Negociação'):string_retorno.find('CNPJ')]
    if '</a>' in string_importante:
        cod_negociacao = re.sub(r'.*?<a.*?>(.*?)<\/a>.*', r'\1', string_importante, flags=re.DOTALL)
#         print sigla, ": ", cod_negociacao
        try:
            fii = FII(ticker=cod_negociacao)
            fii.save()
            print 'FII:', fii, 'criado'
        except:
            print 'FII:', cod_negociacao, 'ja existia'
    else:
        print sigla, ": Não possui código"