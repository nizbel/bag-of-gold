# -*- coding: utf-8 -*-
from bagogold.models.acoes import Acao
from bagogold.models.fii import FII
from bagogold.tfs import preencher_historico
from django.core.management.base import BaseCommand
import sys
from threading import Thread

class PreencheHistoricoThread(Thread):
    def __init__(self, ticker):
        self.ticker = ticker 
        super(PreencheHistoricoThread, self).__init__()

    def run(self):
        try:
            preencher_historico(self.ticker)
        except:
            print sys.exc_info()[0]

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs'

    def handle(self, *args, **options):
        threads = []
        #Ação
        for acao in Acao.objects.all():
            t = PreencheHistoricoThread(acao.ticker)
            threads.append(t)
            t.start()
        # FII
        for fii in FII.objects.all():
            t = PreencheHistoricoThread(fii.ticker)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

