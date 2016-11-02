# -*- coding: utf-8 -*-
from bagogold.bagogold.testFII import baixar_demonstrativo_rendimentos
from django.contrib.auth.models import User
from django.core.files import File
from django.test import TestCase
from urllib2 import URLError

class GeradorProventosTestCase(TestCase):

    def setUp(self):
        # Investidor
        user = User.objects.create(username='tester')

    def test_baixar_arquivo(self):
        arquivo = File(baixar_demonstrativo_rendimentos('http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protocolo=507317'))
        self.assertTrue(hasattr(arquivo, 'size'))
        self.assertTrue(hasattr(arquivo, 'file'))
        self.assertTrue(hasattr(arquivo, 'read'))
        self.assertTrue(hasattr(arquivo, 'open'))
        
    def test_nao_baixar_se_url_invalida(self):
        with self.assertRaises(URLError):
            baixar_demonstrativo_rendimentos('http://www2.bmfbovespa.com.br/empresas/consbov/ArquivosExibe.asp?site=B&protcolo=507317')
    
    def test_excluir_arquivo_sem_info(self):
        pass
    
    def test_gerar_provento(self):
        pass
    
    def test_gerar_versao_doc_provento(self):
        pass
    
    def test_nao_permitir_gerar_prov_repetido(self):
        pass
    
    def test_puxar_validacao_para_investidor(self):
        pass
    