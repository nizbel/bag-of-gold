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
documentos_para_download = list()

class CriarDocumentoThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(documentos_para_download) > 0:
                while len(documentos_para_download) > 0:
                    documento = documentos_para_download.pop(0)
                    
                    # Baixar e salvar documento
                    documento.baixar_e_salvar_documento()
                
                    # Gerar pendencia para o documento
                    pendencia = PendenciaDocumentoProvento()
                    pendencia.documento = documento
#                     pendencia.save()
                
                time.sleep(5)
        except Exception as e:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(e).__name__, e.args)
                print message

class BuscaProventosAcaoThread(Thread):
    def __init__(self, codigo_cvm, ticker):
        self.codigo_cvm = codigo_cvm 
        self.ticker = ticker
        super(BuscaProventosAcaoThread, self).__init__()
 
    def run(self):
        try:
            ano_atual = datetime.date.today().year
            if DocumentoProventoBovespa.objects.filter(data_referencia__year=ano_atual):
                ano_inicial = ano_atual
            else:
                ano_inicial = ano_atual - 1 
            for ano in range(ano_inicial, datetime.date.today().year+1):
                buscar_proventos_acao(self.codigo_cvm, self.ticker, ano, 0)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.codigo_cvm, "Thread:", message
#             pass
        del threads_rodando[self.codigo_cvm]

class Command(BaseCommand):
    help = 'Busca proventos de ações na Bovespa'

    def handle(self, *args, **options):
        # O incremento mostra quantas threads de busca de documentos correrão por vez
        qtd_threads = 20
        
        # Prepara thread de criação de documentos no sistema
        thread_criar_documento = CriarDocumentoThread()
        thread_criar_documento.start()
        
        # Prepara threads de busca
#         acoes = Acao.objects.filter(empresa__codigo_cvm__isnull=False).order_by('empresa__codigo_cvm').distinct('empresa__codigo_cvm')
        acoes = Acao.objects.filter(ticker__in=['BBAS3'])
        contador = 0
        while contador < len(acoes):
            acao = acoes[contador]
            t = BuscaProventosAcaoThread(acao.empresa.codigo_cvm, re.sub(r'\d', '', acao.ticker))
            threads_rodando[acao.empresa.codigo_cvm] = 1
            t.start()
            contador += 1
            while (len(threads_rodando) > qtd_threads):
                print 'Documentos para download:', len(documentos_para_download), '... Threads:', len(threads_rodando)
                time.sleep(3)
        del threads_rodando['Principal']
        
def buscar_proventos_acao(codigo_cvm, ticker, ano, num_tentativas):
    # Busca todos os proventos
    prov_url = 'http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoRelevantes.asp?codCVM=%s&ano=%s' % (codigo_cvm, ano)
    req = Request(prov_url)
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
        # Verificar se sistema está indisponível
        if 'Sistema indisponivel' in data:
            if num_tentativas == 3:
                raise URLError('Sistema indisponível')
                return
            return buscar_proventos_acao(codigo_cvm, ticker, ano, num_tentativas+1)
        inicio = data.find('id="frmConsultaEmpresas"')
        fim = data.find('</form>', inicio)
        data = data[inicio : fim]
        
        print 'Buscar', Empresa.objects.get(codigo_cvm=codigo_cvm), ano
        divisoes = re.findall('<div class="large-12 columns">(.*?)(?=<div class="large-12 columns">|$)', data, flags=re.IGNORECASE|re.DOTALL)
        informacoes_rendimentos = list()
        for divisao in divisoes:
            # Pega as informações necessárias dentro da divisão, não há como existir mais de uma tupla (data, protocolo)
            informacao_divisao = re.findall('Data Referência.*?(\d+/\d+/\d+).*?Assunto.*?(?:juro|dividendo|provento|capital social).*?<a href=".*?protocolo=(\d+).*?" target="_blank">.*?</a>', divisao, flags=re.IGNORECASE|re.DOTALL)
            if informacao_divisao:
                informacoes_rendimentos.append(informacao_divisao[0])
        print 'Buscou', Empresa.objects.get(codigo_cvm=codigo_cvm), ano
        
        for data_referencia, protocolo in informacoes_rendimentos:
            print protocolo, Empresa.objects.get(codigo_cvm=codigo_cvm), ano
            if not DocumentoProventoBovespa.objects.filter(empresa__codigo_cvm=codigo_cvm, protocolo=protocolo):
                documento = DocumentoProventoBovespa()
                documento.empresa = Empresa.objects.get(codigo_cvm=codigo_cvm)
                documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=%s' % (protocolo)
                documento.tipo = 'A'
                documento.protocolo = protocolo
                documento.data_referencia = datetime.datetime.strptime(data_referencia, '%d/%m/%Y')
                documentos_para_download.append(documento)
        
