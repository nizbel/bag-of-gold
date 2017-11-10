# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.acoes import Acao, Provento, AcaoProvento, \
    AtualizacaoSelicProvento
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import FII, ProventoFII
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, InvestidorLeituraDocumento, \
    InvestidorResponsavelPendencia, ProventoAcaoDescritoDocumentoBovespa, \
    AcaoProventoAcaoDescritoDocumentoBovespa, ProventoAcaoDocumento, \
    ProventoFIIDescritoDocumentoBovespa, ProventoFIIDocumento, \
    SelicProventoAcaoDescritoDocBovespa
from bagogold.bagogold.testFII import baixar_demonstrativo_rendimentos
from bagogold.bagogold.utils.gerador_proventos import \
    alocar_pendencia_para_investidor, salvar_investidor_responsavel_por_leitura, \
    desalocar_pendencia_de_investidor, buscar_proventos_proximos_acao, \
    converter_descricao_provento_para_provento_acoes, copiar_proventos_acoes, \
    converter_descricao_provento_para_provento_fiis, \
    versionar_descricoes_relacionadas_acoes, versionar_descricoes_relacionadas_fiis, \
    ler_provento_estruturado_fii, criar_descricoes_provento_acoes, \
    relacionar_proventos_lidos_sistema
from cStringIO import StringIO
from decimal import Decimal
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
        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=508232'
        documento.tipo = 'A'
        documento.protocolo = '508232'
        documento.tipo_documento = DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_ACIONISTAS
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        documento.baixar_e_salvar_documento()
        
        # Criando proventos para teste
        Provento.objects.create(acao=acao1, data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(8), oficial_bovespa=True)
        Provento.objects.create(acao=acao1, data_ex=datetime.date(2016, 11, 10), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(7), oficial_bovespa=True)
        Provento.objects.create(acao=acao1, data_ex=datetime.date(2016, 11, 14), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(6), oficial_bovespa=True)
        Provento.objects.create(acao=acao1, data_ex=datetime.date(2016, 11, 8), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(5), oficial_bovespa=True)
        Provento.objects.create(acao=acao1, data_ex=datetime.date(2016, 11, 6), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(4), oficial_bovespa=True)
        Provento.objects.create(acao=acao1, data_ex=datetime.date(2016, 11, 16), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(3), oficial_bovespa=True)
        Provento.objects.create(acao=acao1, data_ex=datetime.date(2016, 11, 13), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(2), oficial_bovespa=True)
        Provento.objects.create(acao=acao1, data_ex=datetime.date(2016, 11, 11), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(1), oficial_bovespa=True)
        
        # Empresa inexistente
        empresa2 = Empresa.objects.create(nome='Teste', nome_pregao='TTTT', codigo_cvm='1024')
        acao2 = Acao.objects.create(empresa=empresa2, ticker="TTTT3")
        
        # Empresa para FII
        empresa3 = Empresa.objects.create(nome='Fundo BBPO', nome_pregao='BBPO')
        fii1 = FII.objects.create(empresa=empresa3, ticker='BBPO11')

    def test_baixar_arquivo(self):
        """Testa se o arquivo baixado realmente é um arquivo"""
        conteudo = baixar_demonstrativo_rendimentos('http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=507317')
        self.assertFalse(conteudo == ())
        arquivo = File(conteudo)
        self.assertTrue(hasattr(arquivo, 'file'))
        self.assertTrue(hasattr(arquivo, 'open'))
        
    def test_nao_baixar_se_url_invalida(self):
        """Testa se é jogado URLError quando enviada uma URL da bovespa inválida"""
        with self.assertRaises(URLError):
            baixar_demonstrativo_rendimentos('http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protcolo=507317')
    
    def test_nao_baixar_se_ja_existir_arquivo_em_media(self):
        """Testa se criação do documento na base recusa download devido a documento já existir em Media"""
        documento = DocumentoProventoBovespa()
        documento.empresa = Empresa.objects.get(codigo_cvm='1023')
        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=507317'
        documento.tipo = 'A'
        documento.protocolo = '507317'
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        self.assertFalse(documento.baixar_e_salvar_documento())
        
    def test_baixar_se_nao_existir_arquivo_em_media(self):
        """Testa se criação do documento na base faz download devido a documento não existir em Media"""
        empresa = Empresa.objects.get(codigo_cvm='1024')
        documento = DocumentoProventoBovespa()
        documento.empresa = empresa
        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=507317'
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
        documento.url = 'http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=507317'
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
        alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='tester').investidor)
        self.assertIsInstance(salvar_investidor_responsavel_por_leitura(pendencia, User.objects.get(username='tester').investidor, 'C'), InvestidorLeituraDocumento)
        self.assertEqual(PendenciaDocumentoProvento.objects.get(documento=documento).tipo, 'V')
        
    def test_nao_salvar_investidor_responsavel_por_leitura_sem_alocacao(self):
        """Testa se é recusado o salvamento da decisão caso o investidor não tenha sido alocado para a pendência"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        pendencia = PendenciaDocumentoProvento.objects.get(documento=documento)
        with self.assertRaises(ValueError):
            salvar_investidor_responsavel_por_leitura(pendencia, User.objects.get(username='tester').investidor, 'C')
        
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
    
    def test_buscar_proventos_proximos_acao(self):
        """Testa busca de proventos com data EX próxima"""
        descricao_provento = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20),
                                                                                 tipo_provento='D', valor_unitario=Decimal(10))
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        provento = converter_descricao_provento_para_provento_acoes(descricao_provento)[0]
        provento.save()
        documento_provento = ProventoAcaoDocumento.objects.create(documento=documento, descricao_provento=descricao_provento, provento=provento, versao=1)
        
        proventos_proximos = buscar_proventos_proximos_acao(descricao_provento)
        self.assertEqual(len(proventos_proximos), 8)
        for provento in proventos_proximos:
            self.assertLessEqual(abs((provento.data_ex - descricao_provento.data_ex).days), 6)
    
    def test_excluir_arquivo_sem_info(self):
        """Testa exclusão de arquivo por um investidor do site"""
        pass
    
    def test_gerar_provento(self):
        """Testa criação do provento por um investidor"""
        
        pass
    
    def test_nao_permitir_gerar_prov_repetido(self):
        """Testa erro caso um provento seja gerado novamente"""
        pass
    
    def test_converter_descricao_jscp_atualizado_selic_acoes_para_provento(self):
        """Testa criação de provento de JSCP atualizado pela Selic a partir de descrição de provento em documento"""
        # Criar descrição de provento em JSCP
        descricao_provento = ProventoAcaoDescritoDocumentoBovespa(acao=Acao.objects.get(ticker='BBAS3'), \
                                                                  data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='J', valor_unitario=Decimal(8))
        descricao_provento.selicproventoacaodescritodocbovespa = SelicProventoAcaoDescritoDocBovespa(data_inicio=datetime.date(2016, 10, 1), data_fim=datetime.date(2016, 11, 20), provento=descricao_provento)
        provento_convertido = converter_descricao_provento_para_provento_acoes(descricao_provento)[0]
        provento = Provento(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20),
                                           tipo_provento='J', valor_unitario=Decimal(8))
        # Verificar valores
        self.assertEqual(provento_convertido.acao, provento.acao)
        self.assertEqual(provento_convertido.data_ex, provento.data_ex)
        self.assertEqual(provento_convertido.data_pagamento, provento.data_pagamento)
        self.assertEqual(provento_convertido.tipo_provento, provento.tipo_provento)
        self.assertEqual(provento_convertido.valor_unitario, provento.valor_unitario)
        
        # Verificar atualização Selic
        self.assertTrue(hasattr(provento_convertido, 'atualizacaoselicprovento'))
        self.assertEqual(provento_convertido.atualizacaoselicprovento.data_inicio, descricao_provento.selicproventoacaodescritodocbovespa.data_inicio)
        self.assertEqual(provento_convertido.atualizacaoselicprovento.data_fim, descricao_provento.selicproventoacaodescritodocbovespa.data_fim)
        self.assertEqual(provento_convertido.atualizacaoselicprovento.provento, provento_convertido)
    
    def test_converter_descricao_dividendos_acoes_para_provento(self):
        """Testa criação de provento de dividendos a partir de descrição de provento em documento"""
        # Criar descrição de provento em dividendos
        provento_convertido = converter_descricao_provento_para_provento_acoes(ProventoAcaoDescritoDocumentoBovespa(acao=Acao.objects.get(ticker='BBAS3'), \
                                                                            data_ex=datetime.date(2016, 10, 12), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='D', valor_unitario=Decimal(8)))[0]
        provento = Provento(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 10, 12), data_pagamento=datetime.date(2016, 11, 20),
                                           tipo_provento='D', valor_unitario=Decimal(8))
        self.assertEqual(provento_convertido.acao, provento.acao)
        self.assertEqual(provento_convertido.data_ex, provento.data_ex)
        self.assertEqual(provento_convertido.data_pagamento, provento.data_pagamento)
        self.assertEqual(provento_convertido.tipo_provento, provento.tipo_provento)
        self.assertEqual(provento_convertido.valor_unitario, provento.valor_unitario)
        
    
    def test_converter_descricao_jscp_acoes_para_provento(self):
        """Testa criação de provento de JSCP a partir de descrição de provento em documento"""
        # Criar descrição de provento em JSCP
        provento_convertido = converter_descricao_provento_para_provento_acoes(ProventoAcaoDescritoDocumentoBovespa(acao=Acao.objects.get(ticker='BBAS3'), \
                                                                            data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20), tipo_provento='J', valor_unitario=Decimal(8)))[0]
        provento = Provento(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20),
                                           tipo_provento='J', valor_unitario=Decimal(8))
        self.assertEqual(provento_convertido.acao, provento.acao)
        self.assertEqual(provento_convertido.data_ex, provento.data_ex)
        self.assertEqual(provento_convertido.data_pagamento, provento.data_pagamento)
        self.assertEqual(provento_convertido.tipo_provento, provento.tipo_provento)
        self.assertEqual(provento_convertido.valor_unitario, provento.valor_unitario)
    
    def test_converter_descricao_proventos_em_acoes_para_provento(self):
        """Testa criação de provento em ações a partir de descrição de provento em documento"""
        # Criar descrição de provento em ações
        descricao = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20),
                                                            tipo_provento='A', valor_unitario=Decimal(100))
        AcaoProventoAcaoDescritoDocumentoBovespa.objects.create(provento=descricao, data_pagamento_frac=None, valor_calculo_frac=Decimal(0),
                                                            acao_recebida=Acao.objects.get(ticker='BBAS3'))
        
        # Converter
        provento_convertido, acoes_provento_convertido = converter_descricao_provento_para_provento_acoes(descricao)
        provento = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20),
                                           tipo_provento='A', valor_unitario=Decimal(100))
        AcaoProvento.objects.create(provento=provento, data_pagamento_frac=None, valor_calculo_frac=Decimal(0),
                                                            acao_recebida=Acao.objects.get(ticker='BBAS3'))
        
        # Comparar provento
        self.assertEqual(provento_convertido.acao, provento.acao)
        self.assertEqual(provento_convertido.data_ex, provento.data_ex)
        self.assertEqual(provento_convertido.data_pagamento, provento.data_pagamento)
        self.assertEqual(provento_convertido.tipo_provento, provento.tipo_provento)
        self.assertEqual(provento_convertido.valor_unitario, provento.valor_unitario)
        # Comparar pagamento de ações
        self.assertEqual(len(acoes_provento_convertido), len(AcaoProvento.objects.filter(provento=provento)))
        for acao_provento_convertido in acoes_provento_convertido:
            provento_cadastrado = AcaoProvento.objects.get(provento=provento, acao_recebida=acao_provento_convertido.acao_recebida, 
                                                           valor_calculo_frac=acao_provento_convertido.valor_calculo_frac, data_pagamento_frac=acao_provento_convertido.data_pagamento_frac)
            self.assertEqual(acao_provento_convertido.acao_recebida, provento_cadastrado.acao_recebida)
            self.assertEqual(acao_provento_convertido.valor_calculo_frac, provento_cadastrado.valor_calculo_frac)
            self.assertEqual(acao_provento_convertido.data_pagamento_frac, provento_cadastrado.data_pagamento_frac)
    
    def test_converter_descricao_rendimentos_fii_para_provento(self):
        """Testa criação de provento de FII a partir de descrição de rendimento em documento"""
        # Criar descrição de provento em ações
        descricao = ProventoFIIDescritoDocumentoBovespa.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20),
                                                            tipo_provento='A', valor_unitario=Decimal(100))
        
        # Converter
        provento_convertido = converter_descricao_provento_para_provento_fiis(descricao)
        provento = ProventoFII.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 11, 12), data_pagamento=datetime.date(2016, 11, 20),
                                           tipo_provento='A', valor_unitario=Decimal(100))
        
        # Comparar provento
        self.assertEqual(provento_convertido.fii, provento.fii)
        self.assertEqual(provento_convertido.data_ex, provento.data_ex)
        self.assertEqual(provento_convertido.data_pagamento, provento.data_pagamento)
        self.assertEqual(provento_convertido.tipo_provento, provento.tipo_provento)
        self.assertEqual(provento_convertido.valor_unitario, provento.valor_unitario)
        
    def test_criacao_descricao_provento_acoes_atualizado_selic(self):
        """Testa criação de descrição de JSCP atualizado pela Selic"""
        descricao = ProventoAcaoDescritoDocumentoBovespa(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2007, 3, 22), data_pagamento=datetime.date(2007, 5, 29),
                                           tipo_provento='J', valor_unitario=Decimal('0.389026'))
        atualizacao = SelicProventoAcaoDescritoDocBovespa(provento=descricao, data_inicio=datetime.date(2007, 2, 1), data_fim=datetime.date(2007, 5, 29))
        
        documento = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='113962', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=199999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        
        criar_descricoes_provento_acoes([descricao], [], [atualizacao], documento)
        
        self.assertTrue(ProventoAcaoDocumento.objects.filter(documento=documento, versao=1, descricao_provento=descricao).exists())
        provento_documento = ProventoAcaoDocumento.objects.get(documento=documento, versao=1, descricao_provento=descricao)
        self.assertTrue(AtualizacaoSelicProvento.objects.filter(provento=provento_documento.provento,
                                                                data_inicio=datetime.date(2007, 2, 1), data_fim=datetime.date(2007, 5, 29)))
        
    def test_criacao_descricao_igual_provento_oficial(self):
        """Testa criação de descrição que seja igual a provento oficial que já tenha descrição"""
        acao_bbas = Acao.objects.get(ticker='BBAS3')
        # Caso real, 1 documento validado com 1 provento, outro com 2 sendo um apenas menção ao do primeiro documento
        # Documento 1, provento 1
        descricao_provento_1 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=acao_bbas, data_ex=datetime.date(2007, 3, 22), data_pagamento=datetime.date(2007, 5, 29),
                                           tipo_provento='J', valor_unitario=Decimal('0.389026'))
        provento_1 = Provento.objects.create(acao=acao_bbas, data_ex=datetime.date(2007, 3, 22), data_pagamento=datetime.date(2007, 5, 29),
                                           tipo_provento='J', valor_unitario=Decimal('0.389026'), oficial_bovespa=True)
        documento_1 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='113962', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=199999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_1 = ProventoAcaoDocumento.objects.create(provento=provento_1, documento=documento_1, versao=1, descricao_provento=descricao_provento_1)
        
        # Documento 2, provento 2
        descricao_provento_2 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=acao_bbas, data_ex=datetime.date(2007, 5, 16), data_pagamento=datetime.date(2007, 5, 29),
                                           tipo_provento='D', valor_unitario=Decimal('0.293761'))
#         provento_2 = Provento.objects.create(acao=acao_bbas, data_ex=datetime.date(2007, 5, 16), data_pagamento=datetime.date(2007, 5, 29),
#                                            tipo_provento='D', valor_unitario=Decimal('0.293761'), oficial_bovespa=True)
        documento_2 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='122170', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=199999', \
                                                            data_referencia=datetime.datetime.strptime('04/03/2016', '%d/%m/%Y'))
#         documento_provento_2 = ProventoAcaoDocumento.objects.create(provento=provento_2, documento=documento_2, versao=1, descricao_provento=descricao_provento_2)
        
        # Documento 2, provento 1
        descricao_provento_3 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=acao_bbas, data_ex=datetime.date(2007, 3, 22), data_pagamento=datetime.date(2007, 5, 29),
                                           tipo_provento='J', valor_unitario=Decimal('0.389026'))
        
        criar_descricoes_provento_acoes([descricao_provento_2, descricao_provento_3], [], [], documento_2)
        
        # Testar criação de novo provento não oficial com base na descrição 3
        self.assertTrue(ProventoAcaoDocumento.objects.filter(descricao_provento=descricao_provento_3, versao=1, documento=documento_2).exists())
    
    def test_versionamento_automatico_versao_nao_final_acoes(self):
        """Testa criação automática de versão a partir de um documento de provento de ações, sendo uma versão que não é a final"""
        acao_bbas = Acao.objects.get(ticker='BBAS3')
        descricao_provento_1 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=acao_bbas, data_ex=datetime.date(2016, 1, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        provento_1 = Provento.objects.create(acao=acao_bbas, data_ex=datetime.date(2016, 1, 14), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10), oficial_bovespa=True)
        documento_1 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='199999', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=199999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_1 = ProventoAcaoDocumento.objects.create(provento=provento_1, documento=documento_1, versao=1, descricao_provento=descricao_provento_1)
        
        descricao_provento_2 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=acao_bbas, data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        provento_2 = Provento.objects.create(acao=acao_bbas, data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        id_provento_2 = provento_2.id
        documento_2 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='299999', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=299999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_2 = ProventoAcaoDocumento.objects.create(provento=provento_2, documento=documento_2, versao=1, descricao_provento=descricao_provento_2)
        
        descricao_provento_3 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=acao_bbas, data_ex=datetime.date(2016, 1, 14), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        documento_3 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='399999', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=399999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_3 = ProventoAcaoDocumento.objects.create(provento=provento_1, documento=documento_3, versao=2, descricao_provento=descricao_provento_3)
        documento_provento_3_id = documento_provento_3.id
        
        # Versionar
        versionar_descricoes_relacionadas_acoes(descricao_provento_2, provento_1)
        
        self.assertEqual(documento_provento_2.provento.id, provento_1.id)
        self.assertEqual(provento_1.data_ex, datetime.date(2016, 1, 14))
        with self.assertRaises(Provento.DoesNotExist):
            Provento.objects.get(id=id_provento_2)
        self.assertEqual(documento_provento_1.versao, 1)
        self.assertEqual(documento_provento_2.versao, 2)
        self.assertEqual(ProventoAcaoDocumento.objects.get(id=documento_provento_3_id).versao, 3)
        
    def test_versionamento_automatico_versao_final_acoes(self):
        """Testa criação automática de versão a partir de um documento de provento de ações, sendo a versão final"""
        descricao_provento_1 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        provento_1 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10), oficial_bovespa=True)
        documento_1 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='199999', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=199999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_1 = ProventoAcaoDocumento.objects.create(provento=provento_1, documento=documento_1, versao=1, descricao_provento=descricao_provento_1)
        
        descricao_provento_2 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        
        documento_2 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='299999', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=299999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_2 = ProventoAcaoDocumento.objects.create(provento=provento_1, documento=documento_2, versao=2, descricao_provento=descricao_provento_2)
        
        descricao_provento_3 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 14), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        provento_3 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 14), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        id_provento_3 = provento_3.id
        documento_3 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='399999', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=399999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_3 = ProventoAcaoDocumento.objects.create(provento=provento_3, documento=documento_3, versao=1, descricao_provento=descricao_provento_3)
        
        # Versionar
        versionar_descricoes_relacionadas_acoes(descricao_provento_3, provento_1)
        
        self.assertEqual(documento_provento_3.provento.id, provento_1.id)
        self.assertEqual(provento_1.data_ex, datetime.date(2016, 1, 14))
        with self.assertRaises(Provento.DoesNotExist):
            Provento.objects.get(id=id_provento_3)
        self.assertEqual(documento_provento_1.versao, 1)
        self.assertEqual(documento_provento_2.versao, 2)
        self.assertEqual(documento_provento_3.versao, 3)
        
    def test_versionamento_automatico_versao_nao_final_fiis(self):
        """Testa criação automática de versão a partir de um documento de provento de FIIs, sendo uma versão que não é a final"""
        descricao_provento_1 = ProventoFIIDescritoDocumentoBovespa.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10))
        provento_1 = ProventoFII.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 14), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10), oficial_bovespa=True)
        documento_1 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(nome_pregao='BBPO'), protocolo='199999', tipo='F', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=199999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_1 = ProventoFIIDocumento.objects.create(provento=provento_1, documento=documento_1, versao=1, descricao_provento=descricao_provento_1)
        
        descricao_provento_2 = ProventoFIIDescritoDocumentoBovespa.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10))
        provento_2 = ProventoFII.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10))
        id_provento_2 = provento_2.id
        documento_2 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(nome_pregao='BBPO'), protocolo='299999', tipo='F', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=299999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_2 = ProventoFIIDocumento.objects.create(provento=provento_2, documento=documento_2, versao=1, descricao_provento=descricao_provento_2)
        
        descricao_provento_3 = ProventoFIIDescritoDocumentoBovespa.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 14), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10))
        documento_3 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(nome_pregao='BBPO'), protocolo='399999', tipo='F', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=399999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_3 = ProventoFIIDocumento.objects.create(provento=provento_1, documento=documento_3, versao=2, descricao_provento=descricao_provento_3)
        documento_provento_3_id = documento_provento_3.id
        
        # Versionar
        versionar_descricoes_relacionadas_fiis(descricao_provento_2, provento_1)
        
        self.assertEqual(documento_provento_2.provento.id, provento_1.id)
        self.assertEqual(provento_1.data_ex, datetime.date(2016, 1, 14))
        with self.assertRaises(ProventoFII.DoesNotExist):
            ProventoFII.objects.get(id=id_provento_2)
        self.assertEqual(documento_provento_1.versao, 1)
        self.assertEqual(documento_provento_2.versao, 2)
        self.assertEqual(ProventoFIIDocumento.objects.get(id=documento_provento_3_id).versao, 3)
        
    def test_versionamento_automatico_versao_final_fiis(self):
        """Testa criação automática de versão a partir de um documento de provento de FIIs, sendo a versão final"""
        descricao_provento_1 = ProventoFIIDescritoDocumentoBovespa.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10))
        provento_1 = ProventoFII.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10), oficial_bovespa=True)
        documento_1 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(nome_pregao='BBPO'), protocolo='199999', tipo='F', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=199999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_1 = ProventoFIIDocumento.objects.create(provento=provento_1, documento=documento_1, versao=1, descricao_provento=descricao_provento_1)
        
        descricao_provento_2 = ProventoFIIDescritoDocumentoBovespa.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10))
        
        documento_2 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(nome_pregao='BBPO'), protocolo='299999', tipo='F', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=299999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_2 = ProventoFIIDocumento.objects.create(provento=provento_1, documento=documento_2, versao=2, descricao_provento=descricao_provento_2)
        
        descricao_provento_3 = ProventoFIIDescritoDocumentoBovespa.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 14), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10))
        provento_3 = ProventoFII.objects.create(fii=FII.objects.get(ticker='BBPO11'), data_ex=datetime.date(2016, 1, 14), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='A', valor_unitario=Decimal(10))
        id_provento_3 = provento_3.id
        documento_3 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(nome_pregao='BBPO'), protocolo='399999', tipo='F', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=399999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_3 = ProventoFIIDocumento.objects.create(provento=provento_3, documento=documento_3, versao=1, descricao_provento=descricao_provento_3)
        
        # Versionar
        versionar_descricoes_relacionadas_fiis(descricao_provento_3, provento_1)
        
        self.assertEqual(documento_provento_3.provento.id, provento_1.id)
        self.assertEqual(provento_1.data_ex, datetime.date(2016, 1, 14))
        with self.assertRaises(ProventoFII.DoesNotExist):
            ProventoFII.objects.get(id=id_provento_3)
        self.assertEqual(documento_provento_1.versao, 1)
        self.assertEqual(documento_provento_2.versao, 2)
        self.assertEqual(documento_provento_3.versao, 3)
    
    def test_evitar_puxar_pendencia_com_responsavel_para_investidor(self):
        """Testa situação de falha com investidor puxando para si uma pendência que já tenha responsável"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='tester').investidor)
        resultado, mensagem = alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='validator').investidor)
        self.assertFalse(resultado)
        self.assertEqual(mensagem, u'Pendência já possui responsável')
    
    def test_evitar_mesmo_investidor_ler_e_validar(self):
        """Testa situação de falha com investidor puxando para si uma pendência de validação que tenha lido"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        pendencia = PendenciaDocumentoProvento.objects.get(documento=documento)
        # Alocar leitura
        alocar_pendencia_para_investidor(pendencia, User.objects.get(username='tester').investidor)
        # Decidir
        salvar_investidor_responsavel_por_leitura(pendencia, User.objects.get(username='tester').investidor, 'C')
        # Recarregar pendência
        pendencia = PendenciaDocumentoProvento.objects.get(documento=documento)
        # Tentar alocar validação
        resultado, mensagem = alocar_pendencia_para_investidor(pendencia, User.objects.get(username='tester').investidor)
        self.assertFalse(resultado)
        self.assertEqual(mensagem, u'Investidor já fez a leitura do documento, não pode validar')
    
    def test_alocar_pendencia_para_investidor(self):
        """Testa situação de sucesso com investidor puxando para si uma pendência"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        resultado, mensagem = alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='tester').investidor)
        self.assertTrue(resultado)
        
    def test_desalocar_pendencia_de_investidor(self):
        """Testa situação de sucesso para desalocar pendência de investidor"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='tester').investidor)
        resultado, mensagem = desalocar_pendencia_de_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='tester').investidor)
        self.assertTrue(resultado)
        
    def test_nao_desalocar_pendencia_nao_alocada_para_investidor(self):
        """Testa situação em que é tentado desalocar sem prévia alocação de pendência"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='508232')
        resultado, mensagem = desalocar_pendencia_de_investidor(PendenciaDocumentoProvento.objects.get(documento=documento), User.objects.get(username='tester').investidor)
        self.assertFalse(resultado)
        self.assertEqual(mensagem, u'A pendência não estava alocada para o investidor')
        
    def test_copiar_proventos_atualizados_pela_selic(self):
        """Testa cópia de um provento de JSCP atualizado pela Selic"""
        provento_1 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 12, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(9))
        id_provento_1 = provento_1.id
        provento_2 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 12, 13), data_pagamento=datetime.date(2016, 12, 23),
                                           tipo_provento='D', valor_unitario=Decimal(10), oficial_bovespa=True)
        id_provento_2 = provento_2.id
        atualizacao_selic = AtualizacaoSelicProvento.objects.create(provento=provento_2, data_inicio=datetime.date(2016, 11, 1), data_fim=provento_2.data_pagamento)
        
        copiar_proventos_acoes(provento_1, provento_2)
        
        # Testar se provento 1 agora possui atualizacao pela Selic
        self.assertTrue(AtualizacaoSelicProvento.objects.filter(provento=provento_1).exists())
        self.assertEqual(provento_1.atualizacaoselicprovento.data_inicio, atualizacao_selic.data_inicio)
        self.assertEqual(provento_1.atualizacaoselicprovento.data_fim, atualizacao_selic.data_fim)
        
    def test_copiar_provento_atualizado_pela_selic_sobre_atualizado(self):
        """Testa cópia de um provento de JSCP atualizado pela Selic sobre um outro provento atualizado"""
        provento_1 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 12, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(9))
        id_provento_1 = provento_1.id
        atualizacao_selic_1 = AtualizacaoSelicProvento.objects.create(provento=provento_1, data_inicio=datetime.date(2016, 11, 1), data_fim=provento_1.data_pagamento)
        
        provento_2 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 12, 13), data_pagamento=datetime.date(2016, 12, 23),
                                           tipo_provento='D', valor_unitario=Decimal(10), oficial_bovespa=True)
        id_provento_2 = provento_2.id
        atualizacao_selic_2 = AtualizacaoSelicProvento.objects.create(provento=provento_2, data_inicio=datetime.date(2016, 11, 5), data_fim=provento_2.data_pagamento)
        
        copiar_proventos_acoes(provento_1, provento_2)
        
        # Testar se provento 1 agora possui atualizacao pela Selic
        self.assertTrue(AtualizacaoSelicProvento.objects.filter(provento=provento_1).exists())
        self.assertEqual(provento_1.atualizacaoselicprovento.data_inicio, atualizacao_selic_2.data_inicio)
        self.assertEqual(provento_1.atualizacaoselicprovento.data_fim, atualizacao_selic_2.data_fim)
        
        
    def test_copiar_proventos_apagando_atualizacao_pela_selic(self):
        """Testa copiar um provento sem atualização sobre um que possua atualização pela Selic"""
        provento_1 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 12, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(9))
        id_provento_1 = provento_1.id
        atualizacao_selic = AtualizacaoSelicProvento.objects.create(provento=provento_1, data_inicio=datetime.date(2016, 11, 1), data_fim=provento_1.data_pagamento)
        provento_2 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 12, 13), data_pagamento=datetime.date(2016, 12, 23),
                                           tipo_provento='D', valor_unitario=Decimal(10), oficial_bovespa=True)
        id_provento_2 = provento_2.id
        
        copiar_proventos_acoes(provento_1, provento_2)
        
        # Testar se provento 1 agora possui atualizacao pela Selic
        self.assertFalse(AtualizacaoSelicProvento.objects.filter(provento=provento_1).exists())
        
        # Testar se provento 1 tem agora os dados do provento 2
        self.assertEqual(Provento.gerador_objects.get(id=id_provento_1).data_ex, provento_2.data_ex)
        self.assertEqual(Provento.gerador_objects.get(id=id_provento_1).data_pagamento, provento_2.data_pagamento)
        self.assertEqual(Provento.gerador_objects.get(id=id_provento_1).valor_unitario, provento_2.valor_unitario)
        
    def test_copiar_proventos_de_dividendos_acoes(self):
        """Testa cópia de um provento de ações, do tipo dividendos"""
        provento_1 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 12, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(9))
        id_provento_1 = provento_1.id
        provento_2 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 12, 13), data_pagamento=datetime.date(2016, 12, 23),
                                           tipo_provento='D', valor_unitario=Decimal(10), oficial_bovespa=True)
        id_provento_2 = provento_2.id
        
        copiar_proventos_acoes(provento_1, provento_2)
        
        # Testar se provento 1 tem agora os dados do provento 2
        self.assertEqual(Provento.gerador_objects.get(id=id_provento_1).data_ex, provento_2.data_ex)
        self.assertEqual(Provento.gerador_objects.get(id=id_provento_1).data_pagamento, provento_2.data_pagamento)
        self.assertEqual(Provento.gerador_objects.get(id=id_provento_1).valor_unitario, provento_2.valor_unitario)
            
    def test_copiar_proventos_relacionados_a_documentos(self):
        """Testa a cópia de um provento que tenha um documento relacionado"""
        descricao_provento_1 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        provento_1 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 12), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        id_provento_1 = provento_1.id
        documento_1 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='199999', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=199999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_1 = ProventoAcaoDocumento.objects.create(provento=provento_1, documento=documento_1, versao=1, descricao_provento=descricao_provento_1)
        
        descricao_provento_2 = ProventoAcaoDescritoDocumentoBovespa.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10))
        provento_2 = Provento.objects.create(acao=Acao.objects.get(ticker='BBAS3'), data_ex=datetime.date(2016, 1, 13), data_pagamento=datetime.date(2016, 12, 20),
                                           tipo_provento='D', valor_unitario=Decimal(10), oficial_bovespa=True)
        id_provento_2 = provento_2.id
        documento_2 = DocumentoProventoBovespa.objects.create(empresa=Empresa.objects.get(codigo_cvm='1023'), protocolo='299999', tipo='A', \
                                                            url='http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=299999', \
                                                            data_referencia=datetime.datetime.strptime('03/03/2016', '%d/%m/%Y'))
        documento_provento_2 = ProventoAcaoDocumento.objects.create(provento=provento_2, documento=documento_2, versao=1, descricao_provento=descricao_provento_2)
        
        copiar_proventos_acoes(provento_1, provento_2)
        # Testar se provento 1 tem agora os dados do provento 2
        self.assertEqual(Provento.gerador_objects.get(id=id_provento_1).data_ex, datetime.date(2016, 1, 13))

class LeitorProventosEstruturadosTestCase(TestCase):

    def setUp(self):
        # Investidor
        user = User.objects.create(username='tester')
        
        # Empresa para FII
        empresa1 = Empresa.objects.create(nome='Fundo BBPO', nome_pregao='BBPO')
        fii1 = FII.objects.create(empresa=empresa1, ticker='BBPO11')
        
        # Documento da empresa, já existe em media
        documento = DocumentoProventoBovespa()
        documento.empresa = Empresa.objects.get(codigo_cvm=empresa1.codigo_cvm)
        documento.url = 'https://fnet.bmfbovespa.com.br/fnet/publico/visualizarDocumento?id=8679'
        documento.tipo = 'F'
        documento.tipo_documento = DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO
        documento.protocolo = '8679'
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        conteudo = StringIO('<?xml version="1.0" encoding="UTF-8" standalone="yes"?> \
<DadosEconomicoFinanceiros xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> \
    <DadosGerais> \
        <NomeFundo>BB PROGRESSIVO II FUNDO DE INVESTIMENTO IMOBILIÁRIO – FII</NomeFundo> \
        <CNPJFundo>14410722000129</CNPJFundo> \
        <NomeAdministrador>VOTORANTIM ASSET MANAGEMENT DTVM LTDA.</NomeAdministrador> \
        <CNPJAdministrador>03384738000198</CNPJAdministrador> \
        <ResponsavelInformacao>Reinaldo Holanda de Lacerda</ResponsavelInformacao> \
        <TelefoneContato>(11) 5171-5038</TelefoneContato> \
        <CodISINCota>BRBBPOCTF003</CodISINCota> \
        <CodNegociacaoCota>BBPO11</CodNegociacaoCota> \
    </DadosGerais> \
    <InformeRendimentos> \
        <Rendimento> \
            <DataAprovacao>2017-02-24</DataAprovacao> \
            <DataBase>2017-02-24</DataBase> \
            <DataPagamento>2017-03-14</DataPagamento> \
            <ValorProventoCota>0.9550423</ValorProventoCota> \
            <PeriodoReferencia>fevereiro</PeriodoReferencia> \
            <Ano>2017</Ano> \
            <RendimentoIsentoIR>true</RendimentoIsentoIR> \
        </Rendimento> \
        <Amortizacao tipo=""/> \
    </InformeRendimentos> \
</DadosEconomicoFinanceiros>')
        documento.documento.save('%s-%s.%s' % (documento.ticker_empresa(), documento.protocolo, 'xml'), File(conteudo))
        

    def test_falhar_por_tipo_fii(self):
        """Testa se a função joga erro para arquivo que não seja de FII"""
        with self.assertRaises(ValueError):
            documento = DocumentoProventoBovespa.objects.get(protocolo='8679')
            documento.tipo = 'A'
            ler_provento_estruturado_fii(documento)
            
    def test_falhar_por_tipo_documento_fii(self):
        """Testa se a função joga erro para arquivo que não seja de FII"""
        with self.assertRaises(ValueError):
            documento = DocumentoProventoBovespa.objects.get(protocolo='8679')
            documento.tipo_documento = DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS
            ler_provento_estruturado_fii(documento)
            
    def test_leitura_com_sucesso_fii(self):
        """Testa se provento e descrição de provento são criados"""
        documento = DocumentoProventoBovespa.objects.get(protocolo='8679')
        ler_provento_estruturado_fii(documento)
        provento_fii_documento = ProventoFIIDocumento.objects.get(documento=documento)
        self.assertEqual(provento_fii_documento.descricao_provento.valor_unitario, provento_fii_documento.provento.valor_unitario)
        self.assertEqual(provento_fii_documento.descricao_provento.data_ex, provento_fii_documento.provento.data_ex)
        self.assertEqual(provento_fii_documento.descricao_provento.data_pagamento, provento_fii_documento.provento.data_pagamento)
        self.assertEqual(provento_fii_documento.descricao_provento.tipo_provento, provento_fii_documento.provento.tipo_provento)
        self.assertEqual(ProventoFII.objects.filter(id=provento_fii_documento.provento.id).count(), 1)
        self.assertEqual(ProventoFIIDescritoDocumentoBovespa.objects.filter(id=provento_fii_documento.descricao_provento.id).count(), 1)
        self.assertFalse(documento.pendente())
        

    def test_relacionar_a_outro_provento(self):
        """Testa operação de relacionar proventos gerados pelo sistema"""
        # Ler documento original
        documento = DocumentoProventoBovespa.objects.get(protocolo='8679')
        ler_provento_estruturado_fii(documento)
        
        # Preparar documento
        documento = DocumentoProventoBovespa()
        documento.empresa = Empresa.objects.get(codigo_cvm=Empresa.objects.all()[0].codigo_cvm)
        documento.url = 'https://fnet.bmfbovespa.com.br/fnet/publico/visualizarDocumento?id=8699'
        documento.tipo = 'F'
        documento.tipo_documento = DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO
        documento.protocolo = '8689'
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        conteudo = StringIO('<?xml version="1.0" encoding="UTF-8" standalone="yes"?> \
<DadosEconomicoFinanceiros xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> \
    <DadosGerais> \
        <NomeFundo>BB PROGRESSIVO II FUNDO DE INVESTIMENTO IMOBILIÁRIO – FII</NomeFundo> \
        <CNPJFundo>14410722000129</CNPJFundo> \
        <NomeAdministrador>VOTORANTIM ASSET MANAGEMENT DTVM LTDA.</NomeAdministrador> \
        <CNPJAdministrador>03384738000198</CNPJAdministrador> \
        <ResponsavelInformacao>Reinaldo Holanda de Lacerda</ResponsavelInformacao> \
        <TelefoneContato>(11) 5171-5038</TelefoneContato> \
        <CodISINCota>BRBBPOCTF003</CodISINCota> \
        <CodNegociacaoCota>BBPO11</CodNegociacaoCota> \
    </DadosGerais> \
    <InformeRendimentos> \
        <Rendimento> \
            <DataAprovacao>2017-02-24</DataAprovacao> \
            <DataBase>2017-02-24</DataBase> \
            <DataPagamento>2017-03-15</DataPagamento> \
            <ValorProventoCota>0.9550423</ValorProventoCota> \
            <PeriodoReferencia>fevereiro</PeriodoReferencia> \
            <Ano>2017</Ano> \
            <RendimentoIsentoIR>true</RendimentoIsentoIR> \
        </Rendimento> \
        <Amortizacao tipo=""/> \
    </InformeRendimentos> \
</DadosEconomicoFinanceiros>')
        documento.documento.save('%s-%s.%s' % (documento.ticker_empresa(), documento.protocolo, 'xml'), File(conteudo))
        
        # Ler documento
        ler_provento_estruturado_fii(documento)
        
        # Verificar se agora há 2 proventos criados
        self.assertEqual(ProventoFII.objects.all().count(), 2)
        
        # Relacionar
        relacionar_proventos_lidos_sistema(ProventoFIIDocumento.objects.get(documento__protocolo='8689').provento, 
                                           ProventoFIIDocumento.objects.get(documento__protocolo='8679').provento)
        
        # Verificar pós-validação
        # Apenas um provento
        self.assertEqual(ProventoFII.objects.all().count(), 1)
        # 2 descrições
        self.assertEqual(ProventoFIIDescritoDocumentoBovespa.objects.all().count(), 2)
        # 2 versões
        self.assertEqual(ProventoFII.objects.get(fii=FII.objects.get(ticker='BBPO11')).proventofiidocumento_set.count(), 2)
        # Data de pagamento 15/03/2017
        self.assertEqual(ProventoFII.objects.all()[0].data_pagamento, datetime.date(2017, 3, 15))
        
    def test_erro_ao_relacionar_por_tipo_documento(self):
        """Testa se função joga erro ao tentar relacionar documentos que não foram adicionados pelo sistema"""
        # Ler documento original
        documento = DocumentoProventoBovespa.objects.get(protocolo='8679')
        ler_provento_estruturado_fii(documento)
        
        # Preparar documento
        documento = DocumentoProventoBovespa()
        documento.empresa = Empresa.objects.get(codigo_cvm=Empresa.objects.all()[0].codigo_cvm)
        documento.url = 'https://fnet.bmfbovespa.com.br/fnet/publico/visualizarDocumento?id=8699'
        documento.tipo = 'F'
        documento.tipo_documento = DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO
        documento.protocolo = '8688'
        documento.data_referencia = datetime.datetime.strptime('03/03/2016', '%d/%m/%Y')
        conteudo = StringIO('<?xml version="1.0" encoding="UTF-8" standalone="yes"?> \
<DadosEconomicoFinanceiros xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"> \
    <DadosGerais> \
        <NomeFundo>BB PROGRESSIVO II FUNDO DE INVESTIMENTO IMOBILIÁRIO – FII</NomeFundo> \
        <CNPJFundo>14410722000129</CNPJFundo> \
        <NomeAdministrador>VOTORANTIM ASSET MANAGEMENT DTVM LTDA.</NomeAdministrador> \
        <CNPJAdministrador>03384738000198</CNPJAdministrador> \
        <ResponsavelInformacao>Reinaldo Holanda de Lacerda</ResponsavelInformacao> \
        <TelefoneContato>(11) 5171-5038</TelefoneContato> \
        <CodISINCota>BRBBPOCTF003</CodISINCota> \
        <CodNegociacaoCota>BBPO11</CodNegociacaoCota> \
    </DadosGerais> \
    <InformeRendimentos> \
        <Rendimento> \
            <DataAprovacao>2017-02-24</DataAprovacao> \
            <DataBase>2017-02-24</DataBase> \
            <DataPagamento>2017-03-15</DataPagamento> \
            <ValorProventoCota>0.0550423</ValorProventoCota> \
            <PeriodoReferencia>fevereiro</PeriodoReferencia> \
            <Ano>2017</Ano> \
            <RendimentoIsentoIR>true</RendimentoIsentoIR> \
        </Rendimento> \
        <Amortizacao tipo=""/> \
    </InformeRendimentos> \
</DadosEconomicoFinanceiros>')
        documento.documento.save('%s-%s.%s' % (documento.ticker_empresa(), documento.protocolo, 'xml'), File(conteudo))
        
        # Ler documento
        ler_provento_estruturado_fii(documento)
        
        provento_teste = ProventoFIIDocumento.objects.get(documento__protocolo='8688')
        provento_teste.documento.tipo_documento = DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS
        provento_teste.documento.save()
        with self.assertRaises(ValueError):
            relacionar_proventos_lidos_sistema(provento_teste.provento, ProventoFIIDocumento.objects.get(documento__protocolo='8688').provento)