# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.testFII import buscar_rendimentos_fii, \
    ler_demonstrativo_rendimentos
from django.core.management.base import BaseCommand
from threading import Thread

resultados = {}

class BuscaRendimentosFIIThread(Thread):
    def __init__(self, ticker):
        self.ticker = ticker 
        super(BuscaRendimentosFIIThread, self).__init__()

    def run(self):
        try:
            resultado = buscar_rendimentos_fii(self.ticker)
            print 'Resultado', self.ticker, resultado
            resultados[self.ticker] = resultado
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print self.ticker, "Thread:", message
            pass

class Command(BaseCommand):
    help = 'Teste buscar distribuições de rendimentos na bovespa'

    def handle(self, *args, **options):
        # O incremento mostra quantas threads correrão por vez
        incremento = 400
        fiis = FII.objects.filter(ticker='PABY11')
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
        
        print '-----------------------------------RESULTADOS----------------------------------'
        total_processado = 0
        total = 0
        for ticker, resultado in resultados.items():
            print ticker, resultado
            total_processado += resultado[0]
            total += resultado[1]
        print total_processado, total, float(total_processado) / total * 100