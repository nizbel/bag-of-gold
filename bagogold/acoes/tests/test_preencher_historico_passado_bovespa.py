# -*- coding: utf-8 -*-
import boto3
from django.test.testcases import TestCase

from bagogold.bagogold.management.commands.preencher_historico_passado_bovespa import listar_documentos_historico_acoes_fiis, \
    processar_historico_acao_fii
from bagogold.acoes.models import Acao, HistoricoAcao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.fii.models import FII, HistoricoFII
from bagogold.settings import CAMINHO_HISTORICO_ACOES_FIIS
from conf.settings_local import AWS_STORAGE_BUCKET_NAME


class PreencherHistoricoPassadoBovespaTestCase (TestCase):
    """Caso de teste para comando de preencher histórico passado da Bovespa (Ações e FIIs)"""
    def tearDown(self):
        for nome in listar_documentos_historico_acoes_fiis():
            boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome)
    
    def test_listar_documentos_historico_acoes_fiis(self):
        """Testa a função de listagem de documentos"""
        # Preencher documentos
        caminho_arquivo_1 = CAMINHO_HISTORICO_ACOES_FIIS + 'COTAHIST_A2005.TXT'
        boto3.client('s3').put_object(Body='Teste 1', Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo_1)
        caminho_arquivo_2 = CAMINHO_HISTORICO_ACOES_FIIS + 'COTAHIST_A2015.TXT'
        boto3.client('s3').put_object(Body='Teste 2', Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo_2)
        
        nomes_documentos = listar_documentos_historico_acoes_fiis()
        
        for nome_documento in nomes_documentos:
            boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_documento)
        
        self.assertEqual(len(nomes_documentos), 2)
        self.assertIn(caminho_arquivo_1, nomes_documentos)
        self.assertIn(caminho_arquivo_2, nomes_documentos)
 
    def test_processar_historico_acao_fii(self):
        """Testa a função de processamento de documentos"""
        # Preparar documento
        with open('bagogold/bagogold/tests/COTAHIST_A2015.TXT', 'r') as documento:
            caminho_arquivo_1 = CAMINHO_HISTORICO_ACOES_FIIS + documento.name.split('/')[-1]
            boto3.client('s3').put_object(Body=documento.read(), Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo_1)
        # Preparar FII de teste
        FII.objects.create(ticker='BBPO11')
        
        self.assertFalse(Acao.objects.exists())
        self.assertFalse(HistoricoAcao.objects.exists())
        self.assertFalse(Empresa.objects.exists())
        self.assertFalse(HistoricoFII.objects.exists())
        
        processar_historico_acao_fii(caminho_arquivo_1, False)
        
        self.assertTrue(Acao.objects.exists())
        self.assertTrue(HistoricoAcao.objects.exists())
        self.assertTrue(Empresa.objects.exists())
        self.assertTrue(HistoricoFII.objects.exists())
        