# -*- coding: utf-8 -*-
from bagogold.testTD import baixar_historico_td_ano
from django.core.management.base import BaseCommand
import datetime

class Command(BaseCommand):
    help = 'Preenche histórico para TD no ano atual'

    def handle(self, *args, **options):
        baixar_historico_td_ano(datetime.date.today().year)
