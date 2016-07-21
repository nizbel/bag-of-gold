# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.utils.acoes import buscar_proventos_acao, \
    preencher_codigos_cvm
from django.core.management.base import BaseCommand
from threading import Thread
import datetime

class BuscaProventosAcaoThread(Thread):
    def __init__(self, codigo_cvm, ticker):
        self.codigo_cvm = codigo_cvm 
        self.ticker = ticker
        super(BuscaProventosAcaoThread, self).__init__()
 
    def run(self):
        try:
            for ano in range(2000, datetime.date.today().year+1):
                buscar_proventos_acao(self.codigo_cvm, self.ticker, ano, 0)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.codigo_cvm, "Thread:", message
            pass

class Command(BaseCommand):
    help = 'Busca proventos de ações na Bovespa'

    def handle(self, *args, **options):
        # O incremento mostra quantas threads correrão por vez
        incremento = 1
#         acoes = Acao.objects.filter(empresa__codigo_cvm__isnull=False).order_by('empresa__codigo_cvm').distinct('empresa__codigo_cvm')
        acoes = Acao.objects.filter(ticker__in=['BBAS3'])
        contador = 0
        while contador <= len(acoes):
            threads = []
            for acao in acoes[contador : min(contador+incremento,len(acoes))]:
                t = BuscaProventosAcaoThread(acao.empresa.codigo_cvm, acao.ticker)
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            contador += incremento
        
        
        
