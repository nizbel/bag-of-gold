# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa
from django.core.management.base import BaseCommand
from threading import Thread
from urllib2 import Request, urlopen, HTTPError, URLError
import datetime
import re
import time

# A thread 'Principal' indica se ainda está rodando a thread principal
threads_rodando = {'Principal': 1}
documentos_para_download = list()
informacoes_rendimentos = list()

class CriarDocumentoThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(documentos_para_download) > 0 or len(informacoes_rendimentos) > 0:
                while len(documentos_para_download) > 0:
                    documento = documentos_para_download.pop(0)
                    
                    # Baixar e salvar documento
                    documento.baixar_e_salvar_documento()
                
                time.sleep(5)
        except Exception as e:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(e).__name__, e.args)
                print message
                
class GeraInfoDocumentoProtocoloThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(informacoes_rendimentos) > 0:
                while len(informacoes_rendimentos) > 0:
                    info = informacoes_rendimentos.pop(0)
                    codigo_cvm = info['codigo_cvm']
                    data_referencia, protocolo, tipo_documento = info['info_doc']

        #             print protocolo, Empresa.objects.get(codigo_cvm=codigo_cvm), ano
                    # Apenas adiciona caso seja dos tipos válidos, decodificando de utf-8
                    if not DocumentoProventoBovespa.objects.filter(empresa__codigo_cvm=codigo_cvm, protocolo=protocolo).exists() \
                        and tipo_documento.decode('utf-8') in DocumentoProventoBovespa.TIPOS_DOCUMENTO_VALIDOS:
                        documento = DocumentoProventoBovespa()
                        documento.empresa = Empresa.objects.get(codigo_cvm=codigo_cvm)
                        documento.tipo_documento = tipo_documento
                        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=%s' % (protocolo)
                        documento.tipo = 'A'
                        documento.protocolo = protocolo
                        documento.data_referencia = datetime.datetime.strptime(data_referencia, '%d/%m/%Y')
                        documentos_para_download.append(documento)
                
                time.sleep(10)
        except Exception as e:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(e).__name__, e.args)
                print message

class BuscaProventosAcaoThread(Thread):
    def __init__(self, codigo_cvm, ticker, ano_inicial):
        self.codigo_cvm = codigo_cvm 
        self.ticker = ticker
        self.ano_inicial = ano_inicial
        super(BuscaProventosAcaoThread, self).__init__()
 
    def run(self):
        try:
            for ano in range(self.ano_inicial, datetime.date.today().year+1):
                buscar_proventos_acao(self.codigo_cvm, ano, 0)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.codigo_cvm, "Thread:", message
#             pass
        # Tenta remover seu código da listagem de threads até conseguir
        while self.codigo_cvm in threads_rodando:
            del threads_rodando[self.codigo_cvm]

class Command(BaseCommand):
    help = 'Busca proventos de ações na Bovespa'

    def add_arguments(self, parser):
        parser.add_argument('ano', type=int)

    def handle(self, *args, **options):
#         inicio = datetime.datetime.now()
        # Buscar ano atual
        if not options['ano'] == 0:
            ano_atual = options['ano']
        else:
            ano_atual = datetime.date.today().year
        
        # O incremento mostra quantas threads de busca de documentos correrão por vez
        qtd_threads = 20
        
        # Prepara thread de criação de documentos no sistema
        for _ in range(6):
            thread_criar_documento = CriarDocumentoThread()
            thread_criar_documento.start()
            
        # Prepara thread de geração de info para documento
        thread_gerar_info = GeraInfoDocumentoProtocoloThread()
        thread_gerar_info.start()
        
        # Prepara threads de busca
        acoes = Acao.objects.filter(empresa__codigo_cvm__isnull=False).order_by('empresa__codigo_cvm').distinct('empresa__codigo_cvm')
#         acoes = Acao.objects.filter(ticker__in=['CIEL3'])
        contador = 0
        try:
            while contador < len(acoes):
                acao = acoes[contador]
                # Verificar ano inicial para busca de documentos
                if DocumentoProventoBovespa.objects.filter(data_referencia__year=ano_atual, empresa=acao.empresa).exists():
                    ano_inicial = ano_atual
                else:
                    ano_inicial = ano_atual - 1 
                t = BuscaProventosAcaoThread(acao.empresa.codigo_cvm, re.sub(r'\d', '', acao.ticker), ano_inicial)
                threads_rodando[acao.empresa.codigo_cvm] = 1
                t.start()
                contador += 1
                while (len(threads_rodando) > qtd_threads):
#                     print 'Documentos para download:', len(documentos_para_download), '... Threads:', len(threads_rodando), '... Infos:', len(informacoes_rendimentos), contador
                    time.sleep(3)
            while (len(threads_rodando) > 0 or len(documentos_para_download) > 0 or len(informacoes_rendimentos) > 0):
#                 print 'Documentos para download:', len(documentos_para_download), '... Threads:', len(threads_rodando), '... Infos:', len(informacoes_rendimentos), contador
                if 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)
        except KeyboardInterrupt:
#             print 'Documentos para download:', len(documentos_para_download), '... Threads:', len(threads_rodando), '... Infos:', len(informacoes_rendimentos), contador
            while 'Principal' in threads_rodando.keys():
                del threads_rodando['Principal']
                time.sleep(3)
#         fim = datetime.datetime.now()
#         print (fim-inicio)
        
def buscar_proventos_acao(codigo_cvm, ano, num_tentativas):
    # Busca todos os proventos
    prov_url = 'http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoRelevantes.asp?codCVM=%s&ano=%s' % (codigo_cvm, ano)
    req = Request(prov_url)
    try:
        response = urlopen(req, timeout=30)
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
            return buscar_proventos_acao(codigo_cvm, ano, num_tentativas+1)
        inicio = data.find('id="frmConsultaEmpresas"')
        fim = data.find('</form>', inicio)
        data = data[inicio : fim]
        
#         print 'Buscar', Empresa.objects.get(codigo_cvm=codigo_cvm), ano
        divisoes = re.findall('<div class="large-12 columns">(.*?)(?=<div class="large-12 columns">|$)', data, flags=re.IGNORECASE|re.DOTALL)
        for divisao in divisoes:
            # Pega as informações necessárias dentro da divisão, não há como existir mais de uma tupla (data, protocolo)
            informacao_divisao = re.findall('Data Referência.*?(\d+/\d+/\d+).*?Assunto.*?(?:juro|dividendo|provento|capital social|remuneraç|agrupamento|desdobramento|orçamento de capital|bonus|bônus|bonificaç).*?<a href=".*?protocolo=(\d+).*?" target="_blank">(.*?)</a>', divisao, flags=re.IGNORECASE|re.DOTALL)
            if informacao_divisao:
                informacoes_rendimentos.append({'info_doc': informacao_divisao[0], 'codigo_cvm': codigo_cvm})
#         print 'Buscou', Empresa.objects.get(codigo_cvm=codigo_cvm), ano
