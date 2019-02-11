# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic
from bagogold.bagogold.utils.misc import buscar_valores_diarios_selic
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import datetime
import traceback


class Command(BaseCommand):
    help = 'Preenche valores para a SELIC'

    def add_arguments(self, parser):
        parser.add_argument('buscar_do_ultimo_registro', type=int, choices=[0, 1])

    def handle(self, *args, **options):
        try:
            # Data inicial é 01-01-2000
            data_inicial = datetime.date(2000, 1, 1)
            # Verificar se já há valores no histórico para aumentar data inicial
            if options['buscar_do_ultimo_registro'] == 1:
                if HistoricoTaxaSelic.objects.filter(data__gte=data_inicial).exists():
                    data_inicial = HistoricoTaxaSelic.objects.all().order_by('-data')[0].data
            
            while data_inicial <= datetime.date.today():
            
                # Data final máxima é a data atual
                data_final = datetime.date(data_inicial.year+10, data_inicial.month, data_inicial.day)
                if data_final > datetime.date.today():
                    data_final = datetime.date.today()
            
                dados = buscar_valores_diarios_selic(data_inicial, data_final)
                for data, valor in dados:
                    HistoricoTaxaSelic.objects.create(data=data, taxa_diaria=valor)
#             print dados[0], dados[len(dados)-1]
                data_inicial = data_final + datetime.timedelta(days=1)

        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher histórico Selic', traceback.format_exc().decode('utf-8'))