# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII, ProventoFII
from cStringIO import StringIO
from decimal import Decimal
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from random import randint
from subprocess import call
from threading import Thread
from urllib2 import Request, urlopen, URLError, HTTPError
import datetime
import os
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
        
def buscar_rendimentos_fii(ticker):
    """
    Busca distribuições de rendimentos de FII no site da Bovespa
    """
    fii_url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=abaDocumento&idioma=pt-br' % ticker[0:4]
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
#         print 'Host: %s' % (req.get_host())
        data = response.read()
        if 'Sistema indisponivel' in data:
            return buscar_rendimentos_fii(ticker)
        inicio = data.find('<div id="tbArqListados">')
#         print 'inicio', inicio
        fim = data.find('</div>', inicio)
        string_importante = (data[inicio:fim])
#         http://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla=BBPO&amp;strData=
        urls = re.findall('href=\"(.*?)\".*?>Distribuição', string_importante,flags=re.IGNORECASE)
        urls += re.findall('href=\"(.*?)\".*?>Amortização', string_importante,flags=re.IGNORECASE)
#         print len(urls)
        proventos = list()
        for url in urls:
            url = url.replace('&amp;', '&')
#             print url
            proventos.append((ler_demonstrativo_rendimentos(url, ticker),url))
        
        # Adicionar proventos
        # Buscar FII
        fii = FII.objects.get(ticker=ticker)
        for provento in proventos:
            if provento[0][0] and provento[0][1]:
                datas_lidas = list()
                for data_lida in provento[0][0]:
                    datas_lidas.append(datetime.datetime.strptime(data_lida, "%d/%m/%Y").date())
                # Retirar datas duplicadas
                datas_lidas = list(set(datas_lidas))
                # Ordenar por data
                datas_lidas.sort()
                # Se lista tiver pelo menos 2 datas diferentes, preparar para adicionar
                if len(datas_lidas) >= 2:
                    # Primeiro valor é o do provento
                    valor = Decimal(provento[0][1][0].replace(' ', '').replace(',', '.'))
                    print ticker, ':', datas_lidas[-2:], valor 
                    novo_provento = ProventoFII(fii=fii, data_ex=datas_lidas[-2], data_pagamento=datas_lidas[-1], valor_unitario=valor, url_documento=provento[1])
                    novo_provento.save()
                
        
        

def ler_demonstrativo_rendimentos(pdf_url, ticker):
#     http://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla=BBPO&strData=2016-04-01T11:55:11.357
#     pdf_url = 'http://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla=BBPO11&strData=2015-12-01T10:27:19.467'
    req = Request(pdf_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        return ()
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
        return ()
    else:
        try:
            arquivo_rendimentos = StringIO(response.read())
            rsrcmgr = PDFResourceManager()
            retstr = StringIO()
            codec = 'utf-8'
            laparams = LAParams()
            device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            password = ""
            maxpages = 0
            caching = True
            pagenos=set()
            
            for page in PDFPage.get_pages(arquivo_rendimentos, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
                interpreter.process_page(page)
             
            arquivo_rendimentos.close()
            device.close()
            text = retstr.getvalue()
            retstr.close()
            return buscar_info_proventos_fii_no_texto(text)
        except PDFTextExtractionNotAllowed as e:
            # Tenta descriptografar o arquivo com qpdf para poder ler
            try:
#                 print 'Using qpdf'
                with open('%s.pdf' % (ticker), "wb") as local_file:
                    local_file.write(arquivo_rendimentos.getvalue())
                call('qpdf --password=%s --decrypt %s %s' %('', '%s.pdf' % (ticker), '%s-decrypted.pdf' % (ticker)), shell=True)
#                 print 'Done!'
                # Abrir arquivo
                arquivo_rendimentos = open('%s-decrypted.pdf' % (ticker), 'rb')
                rsrcmgr = PDFResourceManager()
                retstr = StringIO()
                codec = 'utf-8'
                laparams = LAParams()
                device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                password = ""
                maxpages = 0
                caching = True
                pagenos=set()
                
                for page in PDFPage.get_pages(arquivo_rendimentos, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
                    interpreter.process_page(page)
                 
                arquivo_rendimentos.close()
                device.close()
                text = retstr.getvalue()
                retstr.close()
                os.remove('%s.pdf' % (ticker))
                os.remove('%s-decrypted.pdf' % (ticker))
                return buscar_info_proventos_fii_no_texto(text)
            except Exception as e:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(e).__name__, e.args)
                print pdf_url, "->", message
                return ()
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print pdf_url, "->", message
            return ()

def buscar_info_proventos_fii_no_texto(texto):
    datas = re.findall('(\d{1,2}[\.\/]\d{1,2}[\.\/]\d\d\d\d)', texto)
    valor = re.findall('(\d+\s*?,\s*?\d+)', texto)
#     print 'datas:', datas, 'valor', valor
    return (datas, valor)