# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.tfs import preencher_historico_acao, buscar_historico, \
    preencher_historico_fii
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
        except:
            print sys.exc_info()[1]
            pass
        
class PreencheHistoricoFIIThread(Thread):
    def __init__(self, ticker):
        self.ticker = ticker 
        super(PreencheHistoricoFIIThread, self).__init__()

    def run(self):
        try:
            preencher_historico_fii(self.ticker, buscar_historico(self.ticker))
        except:
            print sys.exc_info()[1]
            pass
                    

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs'

    def handle(self, *args, **options):
        threads = []
        #Ação
        for acao in Acao.objects.all():
            t = PreencheHistoricoAcaoThread(acao.ticker)
            threads.append(t)
            t.start()
        # FII
        for fii in FII.objects.all():
            t = PreencheHistoricoFIIThread(fii.ticker)
            threads.append(t)
            t.start()
            time.sleep(3)
        for t in threads:
            t.join()

