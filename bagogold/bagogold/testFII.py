# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII, ProventoFII
from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_ticker
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
import mechanize
import os
import re
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
        urls = re.findall('href=\"(.*?)\".*?>Distribuiç', string_importante,flags=re.IGNORECASE)
        urls += re.findall('href=\"(.*?)\".*?>Amortizaç', string_importante,flags=re.IGNORECASE)
#         print len(urls)
        for url in urls:
            url = url.replace('&amp;', '&')
            print url, ticker
#             proventos.append((ler_demonstrativo_rendimentos(url, ticker),url))
    
    print 'novo formato' 
    # Pesquisar no novo formato
    fii_url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=tabInformacoesRelevantes&idioma=pt-br' % ticker[0:4]
    # Usar mechanize para simular clique do usuario no javascript
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    response = br.open(fii_url)
    
    html = response.read()

    br.select_form(nr=0)
    br.set_all_readonly(False)
    br.find_control("ctl00$botaoNavegacaoVoltar").disabled = True
    br.find_control(id='ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_txtPeriodoDe').value = '01/01/2001'
    br.find_control(id='ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_txtPeriodoAte').value = time.strftime("%d/%m/%Y")
    br.find_control(id='ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_ddlCategoria').value = ['0']
    
    response = br.submit()
    html = response.read()
    if 'Sistema indisponivel' in html:
        return buscar_rendimentos_fii(ticker)
    
    inicio = html.find('<div id="ctl00_contentPlaceHolderConteudo_pvwInfoRelevantes">')
    fim = html.find('id="ctl00_contentPlaceHolderConteudo_pvwItem2"', inicio)
    string_importante = (html[inicio:fim])
    
    urls = re.findall('<tr><td>Assunto:</td><td>Distribuição de (?:Rendimento[s]?|Amortização)</td></tr>.*?<a href=\"(https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento\?id=[\d]*?)\">Aviso aos Cotistas</a>', string_importante,flags=re.IGNORECASE|re.DOTALL)
    
#     proventos_novo = list()
    for url in urls:
        print url, ticker
#         rendimento = ler_demonstrativo_rendimentos(url, ticker)
    
        
def baixar_demonstrativo_rendimentos(arquivo_url):
    req = Request(arquivo_url)
#     print pdf_url
    try:
        response = urlopen(req, timeout=30)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        return ()
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
        return ()
    # Buscar informações da extensão
    extensao = ''
    meta = response.info()
    if meta.getheaders("Content-Disposition"):
        content_disposition = meta.getheaders("Content-Disposition")[0]
        if 'filename=' in content_disposition:
            inicio = content_disposition.find('filename=')
            fim = content_disposition.find(';', inicio) if content_disposition.find(';', inicio) != -1 else len(content_disposition)
            if '.' in content_disposition[inicio:fim]:
                extensao = content_disposition[inicio:fim].split('.')[-1]
    resposta = response.read()
    teste_resposta = resposta.decode('latin-1').strip()
    if (u'Não Existem Arquivos com essas Características' in teste_resposta):
        raise URLError('URL da bovespa inválida')
    arquivo_rendimentos = StringIO(resposta)
    return (arquivo_rendimentos, extensao)
#         except Exception as e:
#             template = "An exception of type {0} occured. Arguments:\n{1!r}"
#             message = template.format(type(e).__name__, e.args)
#             print pdf_url, "->", message
#             return ()



def ler_demonstrativo_rendimentos(pdf_url, ticker):
#     http://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla=BBPO&strData=2016-04-01T11:55:11.357
#     pdf_url = 'http://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla=BBPO11&strData=2015-12-01T10:27:19.467'
    req = Request(pdf_url)
#     print pdf_url
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
            meta = response.info()
            arquivo_rendimentos = StringIO(response.read())
            pasta = 'doc proventos/%s' % (ticker)
            if not os.path.exists(pasta):
                os.makedirs(pasta)
                
            with open('%s/%s-%s.pdf' % (pasta, ticker, re.findall('protocolo=(\d+)', pdf_url,flags=re.IGNORECASE)[0]), "wb") as local_file:
                local_file.write(arquivo_rendimentos.getvalue())
            if True:
                return
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
                return buscar_info_proventos_no_texto(text)
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
        
