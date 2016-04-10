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
    def __init__(self, ticker):
        self.ticker = ticker 
        super(PreencheHistoricoAcaoThread, self).__init__()

    def run(self):
        try:
            preencher_historico_acao(self.ticker, buscar_historico(self.ticker))
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print self.ticker, "Thread:", message
            pass
        
class PreencheHistoricoFIIThread(Thread):
    def __init__(self, ticker):
        self.ticker = ticker 
        super(PreencheHistoricoFIIThread, self).__init__()

    def run(self):
        try:
            preencher_historico_fii(self.ticker, buscar_historico(self.ticker))
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print self.ticker, "Thread:", message
            pass
                    

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs'

    def handle(self, *args, **options):
#         for ano in range(2010, 2017):
#             ler_serie_historica_anual_bovespa('COTAHIST_A%s.TXT' % (ano))
        #Ação
        # O incremento mostra quantas threads correrão por vez
        incremento = 32
        acoes = Acao.objects.all()
        contador = 0
        while contador <= len(acoes):
            threads = []
            for acao in acoes[contador : min(contador+incremento,len(acoes))]:
                t = PreencheHistoricoAcaoThread(acao.ticker)
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            contador += incremento
             
        # FII
        fiis = FII.objects.filter(ticker='RNGO11')
        contador = 0
        while contador <= len(fiis):
            threads = []
            for fii in fiis[contador : min(contador+incremento,len(fiis))]:
                t = PreencheHistoricoFIIThread(fii.ticker)
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            contador += incremento
#             time.sleep(3)
#         for t in threads:
#             t.join()

