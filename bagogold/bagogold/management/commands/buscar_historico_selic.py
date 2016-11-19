# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.misc import buscar_valores_diarios_selic
from django.core.management.base import BaseCommand
import datetime


class Command(BaseCommand):
    help = 'Preenche valores para a SELIC'

    def handle(self, *args, **options):
        # Data inicial é 01-01-2000
        data_inicial = datetime.date(2000, 1, 1)
        while data_inicial <= datetime.date.today():
            # TODO verificar se já há valores no histórico para aumentar data inicial
            
            # Data final máxima é a data atual
            data_final = datetime.date(data_inicial.year+10, data_inicial.month, data_inicial.day)
            if data_final > datetime.date.today():
                data_final = datetime.date.today()
            
            print 'Data inicial:', data_inicial
            print 'Data final:', data_final
            
            dados = buscar_valores_diarios_selic(data_inicial, data_final)
            print dados[0], dados[len(dados)-1]
            # TESTE
            data_inicial = data_final + datetime.timedelta(days=1)

