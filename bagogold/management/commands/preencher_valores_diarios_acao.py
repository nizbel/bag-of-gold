# -*- coding: utf-8 -*-
from bagogold.models.acoes import Acao, ValorDiarioAcao
from bagogold.tfs import buscar_ultimos_valores_geral
from django.core.management.base import BaseCommand
from django.utils import timezone

import time

class Command(BaseCommand):
    help = 'Preenche valores diários para as ações em mercado'

    def add_arguments(self, parser):
        parser.add_argument('sleep', type=float)

    def handle(self, *args, **options):
        if not options['sleep'] == 0:
            time.sleep(options['sleep'])
        valores_diarios = buscar_ultimos_valores_geral()
        for k, v in valores_diarios.iteritems():
            acao = Acao.objects.get(ticker=k[0:5])
            valor_diario = ValorDiarioAcao(acao=acao, preco_unitario=v, data_hora=timezone.now())
            valor_diario.save()

