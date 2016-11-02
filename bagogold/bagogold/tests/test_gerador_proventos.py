# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase

class GeradorProventosTestCase(TestCase):

    def setUp(self):
        # Investidor
        user = User.objects.create(username='tester')

    def test_baixar_arquivo(self):
        arquivo = baixar_demonstrativo_rendimentos()
    
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
    