# -*- coding: utf-8 -*-
import traceback

import boto3
from django.core.management.base import BaseCommand
from django.db import transaction

from bagogold.bagogold.utils.bovespa import ler_serie_historica_anual_bovespa
from bagogold.settings import CAMINHO_HISTORICO_ACOES_FIIS
from conf.settings_local import AWS_STORAGE_BUCKET_NAME
from bagogold.bagogold.models.acoes import HistoricoAcao
from bagogold.fii.models import HistoricoFII

class Command(BaseCommand):
    help = 'Preenche histórico para ações e FIIs com dados da bovespa'

    def handle(self, *args, **options):
        # Listar documentos no S3
        nomes_documentos = listar_documentos_historico_acoes_fiis()
        
        # Para cada documento, lançar um try atomic com a leitura de série histórica
        for nome_documento in nomes_documentos:
            processar_historico_acao_fii(nome_documento)
        
def listar_documentos_historico_acoes_fiis():
    """Lista documentos de histórico de ações/FIIs da bovespa"""
    resposta = boto3.client('s3').list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=CAMINHO_HISTORICO_ACOES_FIIS)
    if resposta['KeyCount'] > 0:
        nomes = [content['Key'] for content in resposta['Contents']]
        return nomes
    
    return []
    
def processar_historico_acao_fii(nome_documento, mostrar_log=True):
    """
    Processa um documento de histórico da Bovespa para ações e FIIs
    
    Parâmetros: Nome do documento no S3
                Deve mostrar log?
    """
    try:
        with transaction.atomic():
            documento = boto3.client('s3').get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_documento)
            ler_serie_historica_anual_bovespa(documento['Body']._raw_stream, mostrar_log)
            
        # Ao final, sem erro, apagar documento no S3
        boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_documento)
    except:
        print traceback.format_exc()
    