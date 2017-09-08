# -*- coding: utf-8 -*-
from bagogold.criptomoeda.models import Criptomoeda, ValorDiarioCriptomoeda
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from urllib2 import urlopen
import datetime
import json
import time


class Command(BaseCommand):
    help = 'Preenche valores diários para criptomoedas no Poloniex'

    def handle(self, *args, **options):
        inicio = datetime.datetime.now()
        
        while (datetime.datetime.now() - inicio) < datetime.timedelta(seconds=50):
            inicio_busca = datetime.datetime.now()
            moedas = list(Criptomoeda.objects.all())
            
            for moeda in [moeda for moeda in moedas if moeda.ticker=='BTC']:
                url = 'https://api.cryptonator.com/api/ticker/%s-usd' % (moeda.ticker)
                resultado = urlopen(url)
                data = json.load(resultado) 
                if data['success']:
                    moeda.valor_atual = Decimal(data['ticker']['price'])
                    btc_para_dolar = moeda.valor_atual
                    moeda.data_hora = timezone.now()
                else:
                    return
                
            # Buscar valores POLONIEX
            url = 'https://poloniex.com/public?command=returnTicker'
            resultado = urlopen(url)
            data_polo = json.load(resultado) 
            
            for moeda in [moeda for moeda in moedas if not hasattr(moeda, 'valor_atual')]:
                if 'BTC_%s' % (moeda.ticker) in data_polo.keys():
                    moeda.valor_atual = Decimal(data_polo['BTC_%s' % (moeda.ticker)]['last']) * btc_para_dolar
                    moeda.data_hora = timezone.now()
            
            # Salvar valores
            for moeda in [moeda for moeda in moedas if hasattr(moeda, 'valor_atual')]:
                ValorDiarioCriptomoeda.objects.create(data_hora=moeda.data_hora, criptomoeda=moeda, valor=moeda.valor_atual)
                if ValorDiarioCriptomoeda.objects.filter(data_hora__lt=moeda.data_hora, criptomoeda=moeda).exists():
                    ValorDiarioCriptomoeda.objects.filter(data_hora__lt=moeda.data_hora, criptomoeda=moeda).delete()
                
            tempo_decorrido = datetime.datetime.now() - inicio_busca
            if tempo_decorrido.seconds < 10:
                time.sleep(10 - tempo_decorrido.seconds)
             