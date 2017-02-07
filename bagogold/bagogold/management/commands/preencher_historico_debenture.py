# -*- coding: utf-8 -*-
from bagogold.bagogold.models.debentures import Debenture, \
    HistoricoValorDebenture
from decimal import Decimal
from django.core.management.base import BaseCommand
from threading import Thread
from urllib2 import Request, urlopen, HTTPError, URLError
import datetime
import time


# A thread 'Principal' indica se ainda está rodando a thread principal
threads_rodando = {'Principal': 1}
historicos_a_processar = list()

class ProcessaHistoricoThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(historicos_a_processar) > 0:
                while len(historicos_a_processar) > 0:
                    campos = historicos_a_processar.pop(0)
                    
                    if not HistoricoValorDebenture.objects.filter(data=campos[1], debenture=campos[0]).exists():
                        historico_debenture = HistoricoValorDebenture.objects.create(data=campos[1], debenture=campos[0], valor_nominal=campos[3],
                                                                      juros=campos[4], premio=campos[5])
                            
                time.sleep(5)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print campos[0].codigo, 'processamento', message

class BuscaHistoricoDebentureThread(Thread):
    def __init__(self, debenture, data_inicio=''):
        self.debenture = debenture 
        self.data_inicio = data_inicio
        super(BuscaHistoricoDebentureThread, self).__init__()
        
    def run(self):
        try:
            buscar_historico_debenture(self.debenture, self.data_inicio)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.debenture.codigo, "Thread:", message
#             pass
        # Tenta remover seu código da listagem de threads até conseguir
        while self.debenture.codigo in threads_rodando:
            del threads_rodando[self.debenture.codigo]

class Command(BaseCommand):
    help = 'Preenche histórico para debêntures'

    def add_arguments(self, parser):
        # Se for qualquer valor diferente de 0, pesquisar todo o histórico da debenture
        parser.add_argument('busca_completa', type=int)

    def handle(self, *args, **options):
        inicio = datetime.datetime.now()
        try:
            limite_historicos_a_processar = 20000
            # Limite de threads de busca
            limite_threads_busca = 16
            
            # Prepara thread de processamento de informações de debênture
            thread_processa_debenture = ProcessaHistoricoThread()
            thread_processa_debenture.start()
            
            if options['busca_completa'] != 0:
                for debenture in Debenture.objects.all():
                    while len(threads_rodando) >= limite_threads_busca + 1 or len(historicos_a_processar) > limite_historicos_a_processar:
                        time.sleep(2)
#                         print debenture.codigo, 'Históricos a processar:', len(historicos_a_processar)
                    if HistoricoValorDebenture.objects.filter(debenture=debenture).exists():
                        ultima_data = HistoricoValorDebenture.objects.filter(debenture=debenture).order_by('-data') \
                                                          .values_list('data', flat=True)[0]
                        if ultima_data != debenture.data_fim:
                            t = BuscaHistoricoDebentureThread(debenture, ultima_data)
                            threads_rodando[debenture.codigo] = 1
                            t.start()
                    else:
                        t = BuscaHistoricoDebentureThread(debenture)
                        threads_rodando[debenture.codigo] = 1
                        t.start()
            else:
                try:
                    buscar_historico_ultimos_30_dias()
                except Exception as e:
                    print e.args
            while (len(threads_rodando) > 0 or len(historicos_a_processar) > 0):
#                 print 'Históricos a processar:', len(historicos_a_processar)
                if 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)
        except KeyboardInterrupt:
            while (len(threads_rodando) > 0 or len(historicos_a_processar) > 0):
#                 print 'Históricos a processar:', len(historicos_a_processar)
                if 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)
        
        fim = datetime.datetime.now()
#         print (fim-inicio)
    
    
def buscar_historico_debenture(debenture, data_inicio=''):
    if isinstance(data_inicio, datetime.date):
        data_inicio = data_inicio.strftime('%d/%m/%Y')
    url_historico = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/puhistorico_e.asp?op_exc=Nada&ativo=%s&dt_ini=%s&dt_fim=' % (debenture.codigo, data_inicio)
    req = Request(url_historico)
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
            if debenture.codigo in linha:
                campos = [debenture] + [campo.strip() for campo in linha.split('\t')]
                # Verifica se os campos de juros e prêmio são calculáveis
                if campos[3] != '-' and campos[4].encode('utf-8').lower() != 'não calculável' \
                and campos[5].encode('utf-8').lower() != 'não calculável':
                    campos[1] = datetime.date(int(campos[1][6:]), int(campos[1][3:5]), int(campos[1][:2]))
                    campos[3] = Decimal(campos[3].replace('.', '').replace(',', '.'))
                    campos[4] = Decimal(0) if campos[4] == '-' else Decimal(campos[4].replace('.', '').replace(',', '.'))
                    campos[5] = Decimal(0) if campos[5] == '-' else Decimal(campos[5].replace('.', '').replace(',', '.'))
                    historicos_a_processar.append(campos)
    
def buscar_historico_ultimos_30_dias():
    data_inicio = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%d/%m/%Y')
    url_historico = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/puhistorico_e.asp?op_exc=Nada&ativo=&dt_ini=%s&dt_fim=' % (data_inicio)
    req = Request(url_historico)
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
    for indice, linha in enumerate(data.decode('latin-1').split('\n')):
        if indice >= 3 and len(linha.split('\t')) == 9:
            campos = [campo.strip() for campo in linha.split('\t')]
            if Debenture.objects.filter(codigo=campos[1]).exists():
                debenture = Debenture.objects.get(codigo=campos[1])
                campos = [debenture] + [campo.strip() for campo in linha.split('\t')]
                # Verifica se os campos de juros e prêmio são calculáveis
                if campos[3] != '-' and campos[4].encode('utf-8').lower() != 'não calculável' \
                and campos[5].encode('utf-8').lower() != 'não calculável':
                    campos[1] = datetime.date(int(campos[1][6:]), int(campos[1][3:5]), int(campos[1][:2]))
                    campos[3] = Decimal(campos[3].replace('.', '').replace(',', '.'))
                    campos[4] = Decimal(0) if campos[4] == '-' else Decimal(campos[4].replace('.', '').replace(',', '.'))
                    campos[5] = Decimal(0) if campos[5] == '-' else Decimal(campos[5].replace('.', '').replace(',', '.'))
                    historicos_a_processar.append(campos)
