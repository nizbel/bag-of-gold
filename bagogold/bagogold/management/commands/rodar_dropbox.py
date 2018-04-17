# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import datetime
import subprocess32 as subprocess
import time


class Command(BaseCommand):
    help = 'Roda Dropbox para testes com a aparencia do Metronic'

    def handle(self, *args, **options):
        inicio = datetime.datetime.now()
        fim = datetime.datetime.now()
        
        while (fim - inicio).total_seconds() < 55:
            try:
                test_metronic = CarregamentoMetronic.objects.get(id=1)
            except CarregamentoMetronic.DoesNotExist:
                test_metronic = CarregamentoMetronic()
                test_metronic.save()
            
            if test_metronic.carregar_dados:
                subprocess.call(['/home/bagofgold/bin/dropbox.py', 'start'])
                while 'Up to date' not in subprocess.check_output(['/home/bagofgold/bin/dropbox.py', 'status']):
                    time.sleep(5)
                subprocess.call(['/home/bagofgold/bin/dropbox.py', 'stop'])
                test_metronic.carregar_dados = False
                test_metronic.save()

            time.sleep(5)
            fim = datetime.datetime.now()   
