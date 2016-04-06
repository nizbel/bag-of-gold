# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.testFII import buscar_rendimentos_fii, \
    ler_demonstrativo_rendimentos
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Teste buscar distribuições de rendimentos na bovespa'

    def handle(self, *args, **options):
        for fii in FII.objects.all():
            buscar_rendimentos_fii(fii.ticker)