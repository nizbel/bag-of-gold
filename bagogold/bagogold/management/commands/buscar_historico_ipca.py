# -*- coding: utf-8 -*-
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import traceback

from bagogold import settings
from bagogold.bagogold.utils.taxas_indexacao import buscar_valores_mensal_ipca


class Command(BaseCommand):
    help = 'Preenche valores para o IPCA'

    def handle(self, *args, **options):
        try:
            buscar_valores_mensal_ipca()
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher histórico do IPCA', traceback.format_exc().decode('utf-8'))

