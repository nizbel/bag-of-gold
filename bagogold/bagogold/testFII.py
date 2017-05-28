# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII
from cStringIO import StringIO
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

        
def baixar_demonstrativo_rendimentos(arquivo_url):
    req = Request(arquivo_url)
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
#     print meta
    # Busca extensão pelo content disposition, depois pelo content-type se não encontrar
    if meta.getheaders("Content-Disposition"):
        content_disposition = meta.getheaders("Content-Disposition")[0]
        if 'filename=' in content_disposition:
            inicio = content_disposition.find('filename=')
            fim = content_disposition.find(';', inicio) if content_disposition.find(';', inicio) != -1 else len(content_disposition)
            if '.' in content_disposition[inicio:fim]:
                extensao = content_disposition[inicio:fim].split('.')[-1].replace('"', '')
    if extensao == '':
        if meta.getheaders("Content-Type"):
            content_type = meta.getheaders("Content-Type")[0]
            if '/' in content_type:
                extensao = content_type.split('/')[1]
    resposta = response.read()
#     print resposta
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
                
#             with open('%s/%s-%s.pdf' % (pasta, ticker, re.findall('protocolo=(\d+)', pdf_url,flags=re.IGNORECASE)[0]), "wb") as local_file:
#                 local_file.write(arquivo_rendimentos.getvalue())
#             if True:
#                 return
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
        
