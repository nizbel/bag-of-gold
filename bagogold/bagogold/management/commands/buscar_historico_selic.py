# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.misc import buscar_valores_diarios_selic
from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
import time


class Command(BaseCommand):
    help = 'Preenche valores para a SELIC'

    def handle(self, *args, **options):
        # Data inicial é 01-01-2000
        data_inicial = datetime.date(2000, 1, 1)
        buscar_valores_diarios_selic(datetime.date(2016,11,17), datetime.date(2016,11,17))

