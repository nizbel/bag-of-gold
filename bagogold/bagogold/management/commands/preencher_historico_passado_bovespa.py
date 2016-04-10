# -*- coding: utf-8 -*-
from bagogold.bagogold.tfs import ler_serie_historica_anual_bovespa
from twisted.test.test_amp import BaseCommand

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs'

    def handle(self, *args, **options):
        for ano in range(2007, 2017):
            ler_serie_historica_anual_bovespa('COTAHIST_A%s.TXT' % (ano))