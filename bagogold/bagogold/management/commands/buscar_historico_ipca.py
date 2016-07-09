# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.misc import buscar_historico_ipca
from django.core.management.base import BaseCommand
from django.utils import timezone
import time


class Command(BaseCommand):
    help = 'Preenche valores para o IPCA'

    def handle(self, *args, **options):
        buscar_historico_ipca()

