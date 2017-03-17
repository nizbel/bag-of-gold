# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento
from django.core.management.base import BaseCommand
from threading import Thread
from urllib2 import Request, urlopen, HTTPError, URLError
import datetime
import re
import time

# A thread 'Principal' indica se ainda está rodando a thread principal
threads_rodando = {'Principal': 1}
tipo_documento_para_adicionar = list()

class AdicionaTipoDocumentoThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(tipo_documento_para_adicionar) > 0:
                while len(tipo_documento_para_adicionar) > 0:
                    info = tipo_documento_para_adicionar.pop(0)
                    protocolo = info['protocolo']
                    tipo_documento = info['tipo_documento']
                    if DocumentoProventoBovespa.objects.filter(protocolo=protocolo).exists():
                        documento = DocumentoProventoBovespa.objects.get(protocolo=protocolo)
                        documento.tipo_documento = tipo_documento
                        documento.save()
                
                time.sleep(10)
        except Exception as e:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(e).__name__, e.args)
                print message

class BuscaProventosAcaoThread(Thread):
    def __init__(self, protocolo):
        self.protocolo = protocolo 
        super(BuscaProventosAcaoThread, self).__init__()
 
    def run(self):
        try:
            buscar_proventos_acao(self.protocolo)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.protocolo, "Thread:", message
#             pass
        # Tenta remover seu código da listagem de threads até conseguir
        while self.protocolo in threads_rodando:
            del threads_rodando[self.protocolo]

class Command(BaseCommand):
    help = 'TEMPORÁRIO adiciona tipo de documento a um documento'

    def handle(self, *args, **options):
        inicio = datetime.datetime.now()
        
        # O incremento mostra quantas threads de busca de documentos correrão por vez
        qtd_threads = 20
        
        # Prepara thread de adicionar tipo de documento
        thread_gerar_info = AdicionaTipoDocumentoThread()
        thread_gerar_info.start()
        
        try:
            # Prepara threads de busca
            documentos = DocumentoProventoBovespa.objects.filter(tipo_documento='')
            contador = 0
            while contador < len(documentos):
                documento = documentos[contador]
                t = BuscaProventosAcaoThread(documento.protocolo)
                threads_rodando[documento.protocolo] = 1
                t.start()
                contador += 1
                while (len(threads_rodando) > qtd_threads):
                    print 'Tipos para adicionar:', len(tipo_documento_para_adicionar), '... Threads:', len(threads_rodando), contador
                    time.sleep(3)
            while (len(threads_rodando) > 0 or len(tipo_documento_para_adicionar) > 0):
                print 'Tipos para adicionar:', len(tipo_documento_para_adicionar), '... Threads:', len(threads_rodando), contador
                if 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)
        except KeyboardInterrupt:
            print 'Tipos para adicionar:', len(tipo_documento_para_adicionar), '... Threads:', len(threads_rodando), contador
            if 'Principal' in threads_rodando.keys():
                del threads_rodando['Principal']
            time.sleep(3)
        fim = datetime.datetime.now()
        print (fim-inicio)
        
def buscar_proventos_acao(protocolo):
    # Busca todos os proventos
    prov_url = 'http://www2.bmfbovespa.com.br/empresas/consbov/CabecalhoArquivo.asp?motivo=&protocolo=%s&site=B' % (protocolo)
    req = Request(prov_url)
    try:
        response = urlopen(req, timeout=30)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        return buscar_proventos_acao(protocolo)
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
        return buscar_proventos_acao(protocolo)
    else:
        data = response.read().decode('latin-1')
        # Verificar se sistema está indisponível
        if 'Sistema indisponivel' in data:
            return buscar_proventos_acao(protocolo)
        inicio = data.find('<td')
        fim = data.find('&nbsp;', inicio)
        inicio = data.rfind('<br>', 0, fim)
        data = data[inicio : fim].replace('<br>', '').strip()
        tipo_documento_para_adicionar.append({'protocolo': protocolo, 'tipo_documento': data})
