# -*- coding: utf-8 -*-
from bagogold.bagogold.testLC import buscar_valores_diarios
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Preenche histórico para a taxa DI'

    def handle(self, *args, **options):
        buscar_valores_diarios()

