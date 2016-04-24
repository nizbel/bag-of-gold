# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.tfs import preencher_historico_acao, buscar_historico, \
    preencher_historico_fii, ler_serie_historica_anual_bovespa
from django.core.management.base import BaseCommand
from threading import Thread
import sys
import time


class PreencheHistoricoAcaoThread(Thread):
    def __init__(self, tickers):
        self.tickers = tickers 
        super(PreencheHistoricoAcaoThread, self).__init__()

    def run(self):
        try:
            for index, ticker in enumerate(self.tickers):
#                 print 'Starting', ticker, float(index)/len(self.tickers)*100
                preencher_historico_acao(ticker, buscar_historico(ticker))
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print ticker, "Thread:", message
            pass
        
class PreencheHistoricoFIIThread(Thread):
    def __init__(self, tickers):
        self.tickers = tickers 
        super(PreencheHistoricoFIIThread, self).__init__()

    def run(self):
        try:
            for index, ticker in enumerate(self.tickers):
#                 print 'Starting', ticker, float(index)/len(self.tickers)*100
                preencher_historico_fii(ticker, buscar_historico(ticker))
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print ticker, "Thread:", message
            pass
                    

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs'

    def handle(self, *args, **options):
        #Ação
        acoes = Acao.objects.all()
        qtd_threads = 8
        qtd_por_thread = int(len(acoes)/qtd_threads)+1
        contador = 0
        threads = []
        while contador <= len(acoes):
            t = PreencheHistoricoAcaoThread(acoes[contador : min(contador+qtd_por_thread,len(acoes))])
            threads.append(t)
            t.start()
            contador += qtd_por_thread
        for t in threads:
            t.join()
             
        # FII
        fiis = FII.objects.all()
        qtd_por_thread = int(len(fiis)/qtd_threads)+1
        contador = 0
        threads = []
        while contador <= len(fiis):
            t = PreencheHistoricoFIIThread(fiis[contador : min(contador+qtd_por_thread,len(fiis))])
            threads.append(t)
            t.start()
            contador += qtd_por_thread
        for t in threads:
            t.join()
#             time.sleep(3)
#         for t in threads:
#             t.join()

