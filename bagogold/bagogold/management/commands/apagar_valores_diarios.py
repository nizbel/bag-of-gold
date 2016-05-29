# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import ValorDiarioAcao, Acao
from bagogold.bagogold.models.fii import ValorDiarioFII, FII
from bagogold.bagogold.models.td import ValorDiarioTitulo
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Apaga valores diários ao fim do dia'

    def handle(self, *args, **options):
        for acao in Acao.objects.all():
            ValorDiarioAcao.objects.filter(acao=acao).delete()
        ValorDiarioTitulo.objects.all().delete()
        for fii in FII.objects.all():
            ValorDiarioFII.objects.filter(fii=fii).delete()

