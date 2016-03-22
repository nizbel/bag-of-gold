# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import ValorDiarioAcao
from bagogold.bagogold.models.fii import ValorDiarioFII
from bagogold.bagogold.models.td import ValorDiarioTitulo
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Apaga valores diários ao fim do dia'

    def handle(self, *args, **options):
        valores_diarios_acao = ValorDiarioAcao.objects.all()
        for valor in valores_diarios_acao:
            valor.delete()
        valores_diarios_td = ValorDiarioTitulo.objects.all()
        for valor in valores_diarios_td:
            valor.delete()
        valores_diarios_fii = ValorDiarioFII.objects.all()
        for valor in valores_diarios_fii:
            valor.delete()

