# -*- coding: utf-8 -*-
from bagogold.criptomoeda.models import Criptomoeda, ValorDiarioCriptomoeda
from bagogold.criptomoeda.utils import \
    buscar_valor_criptomoedas_atual_varias_moedas
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Preenche valores diários para criptomoedas'

    def handle(self, *args, **options):
        # Busca em reais e dólares
        valor_atual = buscar_valor_criptomoedas_atual_varias_moedas(Criptomoeda.objects.all().values_list('ticker', flat=True), [ValorDiarioCriptomoeda.MOEDA_DOLAR, 
                                                                                                                   ValorDiarioCriptomoeda.MOEDA_REAL])
        data_hora = timezone.now()
        for ticker, moedas in valor_atual.items():
            try:
                with transaction.atomic():
                    for moeda, valor in moedas.items():
                        ValorDiarioCriptomoeda.objects.filter(criptomoeda__ticker=ticker, moeda=moeda).delete()
                        ValorDiarioCriptomoeda.objects.create(criptomoeda=Criptomoeda.objects.get(ticker=ticker), valor=valor, moeda=moeda, 
                                                          data_hora=data_hora)
            except:
                pass
            
