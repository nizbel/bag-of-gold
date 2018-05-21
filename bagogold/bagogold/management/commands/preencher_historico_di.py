# -*- coding: utf-8 -*-
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import traceback

from bagogold import settings
from bagogold.bagogold.utils.taxas_indexacao import buscar_valores_diarios_di


class Command(BaseCommand):
    help = 'Preenche histórico para a taxa DI'

    def handle(self, *args, **options):
        try:
            buscar_valores_diarios_di()
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher histórico do DI', traceback.format_exc().decode('utf-8'))
