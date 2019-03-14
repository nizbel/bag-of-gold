# -*- coding: utf-8 -*-
import datetime
import traceback

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction

from bagogold import settings
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic
from bagogold.bagogold.utils.misc import buscar_valores_diarios_selic


class Command(BaseCommand):
    help = 'Preenche valores para a SELIC'

    def add_arguments(self, parser):
        parser.add_argument('-b', '--buscar_do_ultimo_registro', action='store_true', dest='buscar_do_ultimo_registro')

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Data inicial é 01-01-2000
                data_inicial = datetime.date(2000, 1, 1)
                # Verificar se já há valores no histórico para aumentar data inicial
                if options['buscar_do_ultimo_registro']:
                    if HistoricoTaxaSelic.objects.filter(data__gte=data_inicial).exists():
                        data_inicial = HistoricoTaxaSelic.objects.all().order_by('-data')[0].data
                
                while data_inicial <= datetime.date.today():
                
                    # Data final máxima é a data atual
                    data_final = min(data_inicial + datetime.timedelta(days=3650),
                                     datetime.date.today())
                
                    dados = buscar_valores_diarios_selic(data_inicial, data_final)
                    
                    # Separar em grupos de até 250 para verificar se já existe numa única query
                    lista_verificar = list()
                    while dados:
                        while len(lista_verificar) < 250 and dados:
                            lista_verificar.append(dados.pop())
                          
                        datas_existentes = HistoricoTaxaSelic.objects.filter(data__in=[data for (data, _) in lista_verificar]).values_list('data', flat=True)
                        for data, valor in lista_verificar:
                            if data not in datas_existentes:
                                HistoricoTaxaSelic.objects.create(data=data, taxa_diaria=valor)

                        lista_verificar = list()
                        
                    data_inicial = data_final + datetime.timedelta(days=1)
                    
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher histórico Selic', traceback.format_exc().decode('utf-8'))
                