# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.divisoes import preencher_operacoes_div_principal
from django.core.management.base import BaseCommand
from bagogold.bagogold.models.td import OperacaoTitulo

class Command(BaseCommand):
    help = 'Teste preencher operação divisão principal'

    def handle(self, *args, **options):
        for operacao in OperacaoTitulo.objects.all():
            preencher_operacoes_div_principal(operacao)

