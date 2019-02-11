# -*- coding: utf-8 -*-
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import traceback

from bagogold import settings
from bagogold.bagogold.testTD import buscar_valores_diarios


class Command(BaseCommand):
    help = 'Preenche valores diários para o Tesouro Direto'

    def handle(self, *args, **options):
        try:
            valores_diarios = buscar_valores_diarios()
            for valor_diario in valores_diarios:
                # Salva apenas valores que não estejam zerados na venda
                if valor_diario.preco_venda > 0:
                    valor_diario.save()
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher valores diários de Tesouro Direto', traceback.format_exc().decode('utf-8'))
