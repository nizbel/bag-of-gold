# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.testFII import buscar_rendimentos_fii, \
    ler_demonstrativo_rendimentos
from django.core.management.base import BaseCommand
from threading import Thread

class BuscaRendimentosFIIThread(Thread):
    def __init__(self, ticker):
        self.ticker = ticker 
        super(BuscaRendimentosFIIThread, self).__init__()

    def run(self):
        try:
            buscar_rendimentos_fii(self.ticker)
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print self.ticker, "Thread:", message
            pass

class Command(BaseCommand):
    help = 'Teste buscar distribuições de rendimentos na bovespa'

    def handle(self, *args, **options):
        threads = []
        for fii in FII.objects.all():
            t = BuscaRendimentosFIIThread(fii.ticker)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()