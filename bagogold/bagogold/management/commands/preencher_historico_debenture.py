# -*- coding: utf-8 -*-
from bagogold.bagogold.models.debentures import Debenture,\
    HistoricoValorDebenture
from bagogold.bagogold.utils.debenture import buscar_historico_debenture
from django.core.management.base import BaseCommand
import datetime

class Command(BaseCommand):
    help = 'Preenche histórico para debêntures'

    def add_arguments(self, parser):
        # Se for qualquer valor diferente de 0, não pesquisar se debenture já tem historico cadastrado antes da pesquisa
        parser.add_argument('forcar_busca', type=int)

    def handle(self, *args, **options):
        if options['forcar_busca'] == 0:
            for debenture in Debenture.objects.all():
                if HistoricoValorDebenture.objects.filter(debenture=debenture).exists():
                    buscar_historico_debenture(debenture.codigo, HistoricoValorDebenture.objects.filter(debenture=debenture).order_by('-data')[0])
                else:
                    buscar_historico_debenture(debenture.codigo)
        else:
            for codigo in Debenture.objects.all().values_list('codigo', flat=True):
                buscar_historico_debenture(codigo)
    