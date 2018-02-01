# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.utils.bovespa import buscar_historico_recente_bovespa, \
    processar_historico_recente_bovespa
from bagogold.bagogold.utils.misc import ultimo_dia_util
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import datetime
import os
import traceback


class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs'

    def handle(self, *args, **options):
        try:
            # Pesquisar sempre último dia útil
            data_pesquisa = ultimo_dia_util()
            # Buscar
            nome_arquivo_hist = buscar_historico_recente_bovespa(data_pesquisa)
            # Ler
            processar_historico_recente_bovespa(nome_arquivo_hist)
            # Apagar
            os.remove(nome_arquivo_hist)
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar histórico recente ações/fiis %s' % (datetime.datetime.now().strftime('%d/%m/%Y')), traceback.format_exc().decode('utf-8'))
        if nome_arquivo_hist != None and nome_arquivo_hist != '':
            if os.path.isfile(nome_arquivo_hist):
                os.remove(nome_arquivo_hist)