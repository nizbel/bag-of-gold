# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.td import HistoricoTitulo, Titulo
from bagogold.bagogold.testTD import baixar_historico_td_ano, \
    baixar_historico_td_total
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import datetime
import traceback

class Command(BaseCommand):
    help = 'Preenche histórico para TD no ano atual'

    def add_arguments(self, parser):
        parser.add_argument('--total', action='store_true')
        parser.add_argument('--ano', default=datetime.date.today().year)

    def handle(self, *args, **options):
        try:
            if options['total']:
                baixar_historico_td_total()
            else:
                ano = options['ano']
                baixar_historico_td_ano(ano)
            # Corrigir títulos que tenham sido adicionados (data_vencimento == data_inicio)
            for titulo in Titulo.objects.all():
                if titulo.data_vencimento == titulo.data_inicio:
                    titulo.data_inicio = HistoricoTitulo.objects.filter(titulo=titulo).order_by('data')[0].data
                    titulo.save()
        except Exception as e:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins('Erro em Preencher histórico para TD no ano atual', traceback.format_exc())
