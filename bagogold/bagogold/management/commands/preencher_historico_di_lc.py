# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.testLC import buscar_valores_diarios
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import traceback


class Command(BaseCommand):
    help = 'Preenche histórico para a taxa DI'

    def handle(self, *args, **options):
        try:
            buscar_valores_diarios()
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher histórico do DI', traceback.format_exc().decode('utf-8'))
