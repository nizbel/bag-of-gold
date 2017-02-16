# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.testFII import buscar_rendimentos_fii
from django.core.management.base import BaseCommand
from threading import Thread
import datetime

class BuscaRendimentosFIIThread(Thread):
    def __init__(self, ticker):
        self.ticker = ticker 
        super(BuscaRendimentosFIIThread, self).__init__()

    def run(self):
        try:
            buscar_rendimentos_fii(self.ticker)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.ticker, "Thread:", message
            pass

class Command(BaseCommand):
    help = 'Teste buscar distribuições de rendimentos na bovespa para FII'
    
    def add_arguments(self, parser):
        parser.add_argument('--ano', default=datetime.date.today().year)
        parser.add_argument('--total', action='store_true')

    def handle(self, *args, **options):
        # O incremento mostra quantas threads correrão por vez
        incremento = 16
        fiis = FII.objects.filter(ticker__in=['BRCR11'])
        contador = 0
        while contador <= len(fiis):
            threads = []
            for fii in fiis[contador : min(contador+incremento,len(fiis))]:
                t = BuscaRendimentosFIIThread(fii.ticker)
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            contador += incremento
