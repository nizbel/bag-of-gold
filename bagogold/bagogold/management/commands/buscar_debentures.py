# -*- coding: utf-8 -*-
from bagogold.bagogold.models.debentures import Debenture
from decimal import Decimal
from django.core.management.base import BaseCommand
from threading import Thread
from urllib2 import Request, urlopen, HTTPError, URLError
import datetime
import re
import time

# A thread 'Principal' indica se ainda está rodando a thread principal
threads_rodando = {'Principal': 1}
debentures_para_processar = list()

class ProcessaDebentureThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(debentures_para_processar) > 0:
                while len(debentures_para_processar) > 0:
                    debenture = debentures_para_processar.pop(0)
                    # Pegar a chave do primeiro registro pois é sempre enviado um dicionário de registro único
                    codigo = debenture.keys()[0]
                    campos = debenture[codigo]
                    
                    print codigo, campos[59]
                    
                    padrao_snd = campos[43]
                    # Por enquanto, apenas tratar os que forem padronizados
                    if padrao_snd == u'Padrão - SND': 
                        try:
                            data_emissao = datetime.datetime.strptime(campos[11], '%d/%m/%Y').date()
                            data_vencimento = None if campos[12] == u'Indeterminado' else datetime.datetime.strptime(campos[12] , '%d/%m/%Y').date()
                            data_inicio_rentabilidade = datetime.datetime.strptime(campos[15], '%d/%m/%Y').date()
                            valor_nominal_emissao = campos[37]
                            indice = campos[41]
                            percentual_indice = campos[47]
                            situacao = campos[5]
                            data_saida = campos[14]
                            incentivada = campos[88]
                      
                            if Debenture.objects.filter(codigo=codigo).exists():
                                debenture = Debenture.objects.get(codigo=codigo)
                            else:
                                debenture = Debenture(codigo=codigo)
                                
                                debenture.data_emissao = data_emissao
                                debenture.valor_emissao = valor_nominal_emissao.replace('.', '').replace(',', '.')
                                debenture.data_vencimento = data_vencimento
                                debenture.incentivada = False if 'N' in incentivada.upper() else True
            
                                if situacao == u'Excluído' and data_saida != '':
                                    debenture.data_fim = datetime.datetime.strptime(data_saida, '%d/%m/%Y').date()
                        except:
                            print codigo, 'não possui dados suficiente'
                
                time.sleep(1)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print codigo, 'processamento', message

class BuscaInfoDebentureThread(Thread):
    def __init__(self, codigo):
        self.codigo = codigo 
        super(BuscaInfoDebentureThread, self).__init__()
 
    def run(self):
        try:
            buscar_info_debenture(self.codigo)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.codigo, "Thread:", message
        # Tenta remover seu código da listagem de threads até conseguir
        while self.codigo in threads_rodando:
            del threads_rodando[self.codigo]

class Command(BaseCommand):
    help = 'Busca as Debêntures'

    def handle(self, *args, **options):
        try:
            inicio = datetime.datetime.now()
            url_debentures = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/caracteristicas_r.asp?tip_deb=publicas&op_exc=Nada'
            
            # Mostra quantas threads de busca de informações
            qtd_threads = 10
            
            # Prepara thread de processamento de informações de debênture
            thread_processa_debenture = ProcessaDebentureThread()
            thread_processa_debenture.start()
            
            # Prepara threads de busca
            codigos = buscar_lista_debentures(url_debentures)
    #         acoes = Acao.objects.filter(ticker__in=['CIEL3'])
            contador = 0
            while contador < len(codigos):
                codigo = codigos[contador]
                t = BuscaInfoDebentureThread(codigo)
                threads_rodando[codigo] = 1
                t.start()
                contador += 1
                while (len(threads_rodando) > qtd_threads):
#                     print 'Debêntures a processar:', len(debentures_para_processar), '... Threads:', len(threads_rodando), contador
                    time.sleep(2)
            while (len(threads_rodando) > 0 or len(debentures_para_processar) > 0):
#                 print 'Debêntures a processar:', len(debentures_para_processar), '... Threads:', len(threads_rodando), contador
                if 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)
            fim = datetime.datetime.now()
            print (fim-inicio)
        except KeyboardInterrupt:
            while (len(threads_rodando) > 0 or len(debentures_para_processar) > 0):
                print 'Debêntures a processar:', len(debentures_para_processar), '... Threads:', len(threads_rodando), contador
                if 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)

def buscar_lista_debentures(url_debentures):
    req = Request(url_debentures)
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
        
        # Buscar pela URL padrão
        registros = re.findall('caracteristicas_d.asp\?tip_deb=publicas&selecao=([^"]+?)?"', data)
        registros = [registro.replace(' ', '') for registro in registros]
        
        return registros
    
def buscar_info_debenture(codigo):
    url_download_arquivo = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/caracteristicas_e.asp?Ativo=%s' % (codigo)
    req = Request(url_download_arquivo)
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

        for linha in data.decode('latin-1').split('\n'):
#             if u'Código do Ativo' in linha:
#                 for indice, campo in enumerate([campo.strip() for campo in linha.split('\t')]):
#                     print indice, campo
            if codigo in linha:
                campos = [campo.strip() for campo in linha.split('\t')]
                
                debentures_para_processar.append({codigo: campos})
