# -*- coding: utf-8 -*-
from django.test import TestCase

class BuscarFundoInvestimentoTestCase(TestCase):
    """
    Testa os utilitários usados na busca de fundos de investimento
    """
    def setUp(self):
        # Definir quais passos todos os utilitários têm em comum 
        pass
        
    def test_buscar_documento_cvm_sucesso(self):
        """Testa busca de documento de cadastro de fundos na CVM, com sucesso"""
        retorno = buscar_arquivo_csv_cadastro(datetime.date(2018, 10, 26))
        self.assertEquals(len(retorno), 3)
        self.assertEquals(retorno[0], 'http://dados.cvm.gov.br/dados/FI/CAD/DADOS/inf_cadastral_fi_20181026.csv')
        self.assertEquals(retorno[1], 'inf_cadastral_fi_20181026.csv')
        self.assertTrue(retorno[2].isfile())
        
    def test_buscar_documento_cvm_data_nao_util(self):
        """Testa busca de documento de cadastro de fundos em data não útil"""
        with self.assertRaises(ValueError):
            buscar_arquivo_csv_cadastro(datetime.date(2018, 10, 27))
            
    def test_processar_documento_cvm_sucesso(self):
        """Testa processar documento de cadastro de fundos, com sucesso"""
        # Gerar fundos pré-existentes para teste
        
        # Abrir arquivo de teste
        with open('test_documento_cadastro.csv') as f:
            processar_arquivo_csv(novo_documento, f, data_pesquisa)
                
        # Processar
        pass