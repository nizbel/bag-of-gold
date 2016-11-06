# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, InvestidorLeituraDocumento
from bagogold.bagogold.testFII import baixar_demonstrativo_rendimentos
from bagogold.bagogold.utils.gerador_proventos import \
    alocar_pendencia_para_investidor, salvar_investidor_responsavel_por_leitura
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
        
        user = User.objects.create(username='validator')
        
        # Empresa existente
        empresa1 = Empresa.objects.create(nome='Banco do Brasil', nome_pregao='BBAS', codigo_cvm='1023')
        acao1 = Acao.objects.create(empresa=empresa1, ticker="BBAS3")
        
        # Documento da empresa, já existe em media
        documento = DocumentoProventoBovespa()
        documento.empresa = Empresa.objects.get(codigo_cvm=empresa1.codigo_cvm)
        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=%508232'
        documento.tipo = 'A'
        documento.protocolo = '508232'
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        documento.baixar_e_salvar_documento()
        
        # Empresa inexistente
        empresa2 = Empresa.objects.create(nome='Teste', nome_pregao='TTTT', codigo_cvm='1024')
        acao2 = Acao.objects.create(empresa=empresa2, ticker="TTTT3")

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
    
    def test_salvar_investidor_responsavel_por_leitura(self):
        """Testa se é possível salvar o investidor responsável pela leitura do documento"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        pendencia = PendenciaDocumentoProvento.objects.get(documento=documento)
        self.assertIsInstance(salvar_investidor_responsavel_por_leitura(pendencia, User.objects.get(username='tester').investidor, 'C'), InvestidorLeituraDocumento)
        self.assertEqual(PendenciaDocumentoProvento.objects.get(documento=documento).tipo, 'V')
        
    def test_nao_salvar_investidor_responsavel_por_leitura(self):
        """Testa se criar vínculo de responsabilidade de leitura no documento falha ao entrar com valores errados"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        pendencia = PendenciaDocumentoProvento.objects.get(documento=documento)
        # Testa erro para decisão não permitida
        with self.assertRaises(ValueError):
            salvar_investidor_responsavel_por_leitura(pendencia, User.objects.get(username='tester').investidor, 'G')
        # Testa erro para pendência que não seja de leitura
        pendencia.tipo = 'V'
        pendencia.save()
        with self.assertRaises(ValueError):
            salvar_investidor_responsavel_por_leitura(pendencia, User.objects.get(username='tester').investidor, 'C')
    
    def test_excluir_arquivo_sem_info(self):
        """Testa exclusão de arquivo por um investidor do site"""
        pass
    
    def test_gerar_provento(self):
        """Testa criação do provento por um investidor"""
        
        pass
    
    def test_nao_permitir_gerar_prov_repetido(self):
        """Testa erro caso um provento seja gerado novamente"""
        pass
    
    def test_converter_dividendos_acoes_para_provento_real(self):
        pass
    
    def test_converter_jscp_acoes_para_provento_real(self):
        pass
    
    def test_converter_proventos_em_acoes_para_provento_real(self):
        pass
    
    def test_converter_rendimentos_fii_para_provento_real(self):
        pass
    
    def test_gerar_versao_doc_provento(self):
        """Testa criação automática de versão a partir de um documento de provento"""
        pass
    
    def test_evitar_puxar_pendencia_com_responsavel_para_investidor(self):
        """Testa situação de falha com investidor puxando para si uma pendência que já tenha responsável"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='tester').investidor)
        resultado, mensagem = alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='validator').investidor)
        self.assertFalse(resultado)
        self.assertEqual(mensagem, u'Pendência já possui responsável')
    
    def test_evitar_mesmo_investidor_ler_e_validar(self):
        """Testa situação de falha com investidor puxando para si uma pendência de validação que tenha lido"""
        pass
    
    def test_puxar_pendencia_para_investidor(self):
        """Testa situação de sucesso com investidor puxando para si uma pendência"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        resultado, mensagem = alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='tester').investidor)
        self.assertTrue(resultado)