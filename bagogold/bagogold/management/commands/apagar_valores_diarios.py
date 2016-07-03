# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import ValorDiarioAcao, Acao, HistoricoAcao
from bagogold.bagogold.models.fii import ValorDiarioFII, FII
from bagogold.bagogold.models.td import ValorDiarioTitulo
from django.core.management.base import BaseCommand
import datetime

class Command(BaseCommand):
    help = 'Apaga valores diários ao fim do dia'

    def handle(self, *args, **options):
        # Buscar ultimo dia util para remover valores diarios anteriores
        ultimo_dia_util = HistoricoAcao.objects.filter(data__lt=datetime.date.today()).latest('data').data
        for acao in Acao.objects.all():
            ValorDiarioAcao.objects.filter(acao=acao, data_hora__date__lt=ultimo_dia_util).delete()
        ValorDiarioTitulo.objects.filter(data_hora__date__lt=ultimo_dia_util).delete()
        for fii in FII.objects.all():
            ValorDiarioFII.objects.filter(fii=fii, data_hora__date__lt=ultimo_dia_util).delete()

