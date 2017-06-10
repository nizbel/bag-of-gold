# -*- coding: utf-8 -*-
from cStringIO import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from subprocess import call
from urllib2 import Request, urlopen, URLError, HTTPError
import os

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
