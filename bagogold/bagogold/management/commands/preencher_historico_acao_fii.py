# -*- coding: utf-8 -*-
import datetime
import traceback

import boto3
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand

from bagogold import settings
from bagogold.bagogold.utils.bovespa import buscar_historico_recente_bovespa, \
    processar_historico_recente_bovespa
from bagogold.bagogold.utils.misc import ultimo_dia_util
from conf.settings_local import AWS_STORAGE_BUCKET_NAME, AWS_MEDIA_LOCATION


class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs'

    def handle(self, *args, **options):
        nome_arquivo_hist = ''
        try:
            # Pesquisar sempre último dia útil
            data_pesquisa = ultimo_dia_util()
            # Buscar
            nome_arquivo_hist = buscar_historico_recente_bovespa(data_pesquisa)
            # Abrir
            arquivo = boto3.client('s3').get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_arquivo_hist)
            # Ler
            processar_historico_recente_bovespa(arquivo)
            # Apagar
            boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_arquivo_hist)
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar histórico recente ações/fiis %s' % (datetime.datetime.now().strftime('%d/%m/%Y')), traceback.format_exc().decode('utf-8'))
        if nome_arquivo_hist != None and nome_arquivo_hist != '':
            # Verifica se o objeto existe
            resposta = boto3.client('s3').list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=nome_arquivo_hist)
            if (resposta.get('KeyCount', 0) > 0):
                boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_arquivo_hist)