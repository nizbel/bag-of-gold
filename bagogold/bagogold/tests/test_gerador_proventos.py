# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa,\
    PendenciaDocumentoProvento
from bagogold.bagogold.testFII import baixar_demonstrativo_rendimentos
from django.contrib.auth.models import User
from django.core.files import File
from django.test import TestCase
from urllib2 import URLError
import datetime
import os

class GeradorProventosTestCase(TestCase):

    def setUp(self):
        # Investidor
        user = User.objects.create(username='tester')
        
        # Empresa existente
        empresa = Empresa.objects.create(nome='Banco do Brasil', nome_pregao='BBAS', codigo_cvm='1023')
        acao = Acao.objects.create(empresa=empresa, ticker="BBAS3")
        
        # Empresa inexistente
        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TTTT', codigo_cvm='1024')
        acao = Acao.objects.create(empresa=empresa, ticker="TTTT3")

    def test_baixar_arquivo(self):
        """Testa se o arquivo baixado realmente é um arquivo"""
        conteudo = baixar_demonstrativo_rendimentos('http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=507317')
        self.assertFalse(conteudo == ())
        arquivo = File(conteudo)
        self.assertTrue(hasattr(arquivo, 'size'))
        self.assertTrue(hasattr(arquivo, 'file'))
        self.assertTrue(hasattr(arquivo, 'read'))
        self.assertTrue(hasattr(arquivo, 'open'))
        
    def test_nao_baixar_se_url_invalida(self):
        """Testa se é jogado URLError quando enviada uma URL da bovespa inválida"""
        with self.assertRaises(URLError):
            baixar_demonstrativo_rendimentos('http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protcolo=507317')
    
    def test_nao_baixar_se_ja_existir_arquivo_em_media(self):
        """Testa se criação do documento na base recusa download devido a documento já existir em Media"""
        documento = DocumentoProventoBovespa()
        documento.empresa = Empresa.objects.get(codigo_cvm='1023')
        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=%507317'
        documento.tipo = 'A'
        documento.protocolo = '507317'
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        self.assertFalse(documento.baixar_e_salvar_documento())
        
    def test_baixar_se_nao_existir_arquivo_em_media(self):
        """Testa se criação do documento na base faz download devido a documento não existir em Media"""
        empresa = Empresa.objects.get(codigo_cvm='1024')
        documento = DocumentoProventoBovespa()
        documento.empresa = empresa
        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=%507317'
        documento.tipo = 'A'
        documento.protocolo = '507317'
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        self.assertTrue(documento.baixar_e_salvar_documento())
        # Apagar documento criado após teste
        documento.apagar_documento()
        # Apagar pasta após teste
        if os.listdir('%sdoc proventos/%s' % (settings.MEDIA_ROOT, empresa.nome_pregao)) == []:
            os.rmdir('%sdoc proventos/%s' % (settings.MEDIA_ROOT, empresa.nome_pregao))
        
    def test_pendencia_gerada_ao_criar_documento_provento_bovespa(self):
        """Testa se foi gerada pendência ao criar um documento de proventos da Bovespa"""
        empresa = Empresa.objects.get(codigo_cvm='1023')
        documento = DocumentoProventoBovespa()
        documento.empresa = empresa
        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=%507317'
        documento.tipo = 'A'
        documento.protocolo = '507317'
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        documento.baixar_e_salvar_documento()
        self.assertTrue(documento.pendente())
        # Quantidade de pendências deve ser 1
        self.assertTrue(len(PendenciaDocumentoProvento.objects.filter(documento=documento)) == 1)
        # Tipo de pendência deve ser 'L'
        self.assertTrue(PendenciaDocumentoProvento.objects.filter(documento=documento)[0].tipo == 'L')
    
    def test_excluir_arquivo_sem_info(self):
        """Testa exclusão de arquivo por um investidor do site"""
        pass
    
    def test_gerar_provento(self):
        """Testa criação do provento por um investidor"""
        pass
    
    def test_gerar_versao_doc_provento(self):
        """Testa criação automática de versão a partir de um documento de provento"""
        pass
    
    def test_nao_permitir_gerar_prov_repetido(self):
        """Testa erro caso um provento seja gerado novamente"""
        pass
    
    def test_evitar_puxar_pendencia_com_responsavel_para_investidor(self):
        """Testa situação de falha com investidor puxando para si uma pendência que já tenha responsável"""
        pass
    
    def test_evitar_mesmo_investidor_ler_e_validar(self):
        """Testa situação de falha com investidor puxando para si uma pendência de validação que tenha lido"""
        pass
    
    def test_puxar_pendencia_para_investidor(self):
        """Testa situação de sucesso com investidor puxando para si uma pendência"""
        pass
    