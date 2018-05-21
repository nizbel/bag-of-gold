# -*- coding: utf-8 -*-
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import traceback

from bagogold import settings
from bagogold.bagogold.utils.taxas_indexacao import buscar_ipca_projetado


class Command(BaseCommand):
    help = 'Busca valores para o IPCA Projetado'

    def handle(self, *args, **options):
        try:
            buscar_ipca_projetado()
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar IPCA projetado', traceback.format_exc().decode('utf-8'))

