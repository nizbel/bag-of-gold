# -*- coding: utf-8 -*-
from bagogold.lci_lca.models import LetraCredito, HistoricoCarenciaLetraCredito,\
    HistoricoVencimentoLetraCredito
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db.models.aggregates import Max
from math import floor


class Command(BaseCommand):
    help = 'TEMPORÁRIO adiciona datas de vencimento às letras de crédito existentes'

    def handle(self, *args, **options):
        for letra_credito in LetraCredito.objects.all():
            # Verificar os períodos de carência cadastrados
            periodos_carencia = HistoricoCarenciaLetraCredito.objects.filter(letra_credito=letra_credito)
            # Pegar o maior período
            maior_carencia = periodos_carencia.aggregate(maior=Max('carencia'))['maior']
            # Gerar vencimento com 2 anos de diferença (arredondando para cima)
            vencimento = int((floor((Decimal(maior_carencia) / 360)) + 2) * 360)
            
            # Adicionar vencimento a letra de crédito
            vencimento_lci_lca = HistoricoVencimentoLetraCredito(letra_credito=letra_credito, data=None, vencimento=vencimento)
            vencimento_lci_lca.save()