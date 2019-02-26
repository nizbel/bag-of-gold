# -*- coding: utf-8 -*-
import traceback

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand

from bagogold import settings
from bagogold.bagogold.testTD import buscar_valores_diarios
from bagogold.tesouro_direto.models import ValorDiarioTitulo


class Command(BaseCommand):
    help = 'Preenche valores diários para o Tesouro Direto'

    def handle(self, *args, **options):
        try:
            valores_diarios = buscar_valores_diarios()
            
            # Filtrar valores diários ainda não existentes
            if len(valores_diarios) > 0:
                valores_existentes = ValorDiarioTitulo.objects.filter(data_hora=valores_diarios[0].data_hora) \
                    .values_list('titulo', flat=True)
                print valores_existentes
                valores_diarios = [valor_diario for valor_diario in valores_diarios if valor_diario.titulo.id not in valores_existentes]
            
            for valor_diario in valores_diarios:
                # Salva apenas valores que não estejam zerados na venda
                if valor_diario.preco_venda > 0:
                    valor_diario.save()
        except:
            if settings.ENV == 'DEV':
                if options['test']:
                    raise
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher valores diários de Tesouro Direto', traceback.format_exc().decode('utf-8'))
