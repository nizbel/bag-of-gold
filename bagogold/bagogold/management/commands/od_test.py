# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.divisoes import preencher_operacoes_div_principal
from django.core.management.base import BaseCommand
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.bagogold.models.fii import OperacaoFII
from bagogold.bagogold.models.lc import OperacaoLetraCredito

class Command(BaseCommand):
    help = 'Teste preencher operação divisão principal'

    def handle(self, *args, **options):
        print 'Descomente por sua conta e risco'
#         for operacao in OperacaoFII.objects.all():
#             preencher_operacoes_div_principal(operacao)
#         for operacao in OperacaoLetraCredito.objects.all():
#             preencher_operacoes_div_principal(operacao)
#         for operacao in OperacaoTitulo.objects.all():
#             preencher_operacoes_div_principal(operacao)

