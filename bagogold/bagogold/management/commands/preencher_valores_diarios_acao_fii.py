# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, ValorDiarioAcao
from bagogold.bagogold.models.fii import FII, ValorDiarioFII
from bagogold.bagogold.tfs import buscar_ultimos_valores_geral_acao, \
    buscar_ultimos_valores_geral_fii
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from django.core.management.base import BaseCommand
from django.utils import timezone

import datetime
import time


class Command(BaseCommand):
    help = 'Preenche valores diários para as ações e FIIs em mercado'

    def add_arguments(self, parser):
        parser.add_argument('sleep', type=float)

    def handle(self, *args, **options):
        if not options['sleep'] == 0:
            time.sleep(options['sleep'])
        
        # Testa se é dia útil
        if datetime.date.today().weekday() > 4 or verificar_feriado_bovespa(datetime.date.today()):
            return
            
        # Acoes
        valores_diarios = buscar_ultimos_valores_geral_acao()
        for k, v in valores_diarios.iteritems():
            if v is not None:
                acao = Acao.objects.get(ticker=k[:-3])
                valor_diario = ValorDiarioAcao(acao=acao, preco_unitario=v, data_hora=timezone.now())
                valor_diario.save()
            
        # FII
        valores_diarios = buscar_ultimos_valores_geral_fii()
        for k, v in valores_diarios.iteritems():
            if v is not None:
                fii = FII.objects.get(ticker=k[:-3])
                valor_diario = ValorDiarioFII(fii=fii, preco_unitario=v, data_hora=timezone.now())
                valor_diario.save()

