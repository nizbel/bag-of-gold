# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import HistoricoFII, FII
from bagogold.bagogold.tfs import ler_serie_historica_anual_bovespa
from django.core.management.base import BaseCommand
from django.db.models.aggregates import Count
from threading import Thread
import datetime

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
            print self.ano, "Thread:", message
            pass

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs com dados da bovespa'

    def handle(self, *args, **options):
#         historicos_repetidos = list()
#         for fii_id in HistoricoFII.objects.all().values_list('fii', flat=True).distinct():
#             historicos_repetidos = HistoricoFII.objects.filter(fii__id=fii_id).values('data').annotate(num_datas=Count('id')).filter(num_datas__gt=1)
#             for data_repetida in historicos_repetidos:
#                 print FII.objects.get(id=fii_id), historicos_repetidos
#                 historicos_apagar = HistoricoFII.objects.filter(fii__id=fii_id, data=data_repetida['data'])
#                 for indice in range(1, data_repetida['num_datas']):
#                     print 'apagar', historicos_apagar[0]
#                     historicos_apagar[0].delete()
                    
        # O incremento mostra quantas threads correrão por vez
        incremento = 2
        anos = range(2002, datetime.date.today().year+1)
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
        
            