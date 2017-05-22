# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'TEMPORÁRIO adiciona tipo de ação corretamente com base no numero do ticker'

    def handle(self, *args, **options):
        for acao in Acao.objects.all():
            num_ticker = int(''.join([s for s in acao.ticker if s.isdigit()]))
            if num_ticker in Acao.TIPOS_ACAO_NUMERO.keys():
                acao.tipo = Acao.TIPOS_ACAO_NUMERO[num_ticker]
                acao.save()