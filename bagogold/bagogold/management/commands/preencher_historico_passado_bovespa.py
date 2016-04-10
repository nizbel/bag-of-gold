# -*- coding: utf-8 -*-
from bagogold.bagogold.tfs import ler_serie_historica_anual_bovespa
from django.core.management.base import BaseCommand
from threading import Thread

class BuscaHistoricoBovespaThread(Thread):
    def __init__(self, ano):
        self.ano = ano 
        super(BuscaHistoricoBovespaThread, self).__init__()

    def run(self):
        try:
            ler_serie_historica_anual_bovespa('COTAHIST_A%s.TXT' % (self.ano))
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.ticker, "Thread:", message
            pass

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs com dados da bovespa'

    def handle(self, *args, **options):
        # O incremento mostra quantas threads correrão por vez
        incremento = 2
        anos = range(2016, 2017)
        contador = 0
        while contador <= len(anos):
            threads = []
            for ano in anos[contador : min(contador+incremento,len(anos))]:
                t = BuscaHistoricoBovespaThread(ano)
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            contador += incremento
        
            