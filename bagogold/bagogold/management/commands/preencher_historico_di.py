# -*- coding: utf-8 -*-
import datetime
import traceback

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand

from bagogold import settings
from bagogold.bagogold.utils.taxas_indexacao import buscar_valores_diarios_di


class Command(BaseCommand):
    help = 'Preenche histórico para a taxa DI'

    def add_arguments(self, parser):
        parser.add_argument('-g', '--geral', action='store_true', dest='geral')
        
    def handle(self, *args, **options):
        try:
            # Busca todas as datas se geral, se não, busca último ano
            if options['geral']:
                buscar_valores_diarios_di()
            else:
                buscar_valores_diarios_di(datetime.date.today() - datetime.timedelta(days=365))
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher histórico do DI', traceback.format_exc().decode('utf-8'))
