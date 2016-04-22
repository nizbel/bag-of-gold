# -*- coding: utf-8 -*-
from bagogold.bagogold.testFII import verificar_fiis_listados
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Teste preencher FIIs listados na bovespa'

    def handle(self, *args, **options):
        verificar_fiis_listados()
