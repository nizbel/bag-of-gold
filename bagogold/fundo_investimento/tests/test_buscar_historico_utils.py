# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.test import TestCase

from bagogold.fundo_investimento.management.commands.preencher_historico_fundo_investimento import buscar_arquivo_csv_historico, \
    processar_arquivo_csv
from bagogold.fundo_investimento.models import DocumentoCadastro, \
    FundoInvestimento, Administrador, Auditor, Gestor, LinkDocumentoCadastro, \
    GestorFundoInvestimento, HistoricoValorCotas
from bagogold.fundo_investimento.utils import criar_slug_fundo_investimento_valido


class BuscarFundoInvestimentoTestCase(TestCase):
    """
    Testa os utilitários usados na busca de valores de fundos de investimento
    """
    def setUp(self):
        self.fundo = FundoInvestimento.objects.create(nome='Fundo teste', cnpj='00.017.024/0001-53', data_constituicao=datetime.date(2018, 1, 1),
                                                 data_registro=datetime.date(2018, 1 ,1), situacao=FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL,
                                                 tipo_prazo=FundoInvestimento.PRAZO_LONGO, classe=FundoInvestimento.CLASSE_FUNDO_MULTIMERCADO,
                                                 exclusivo_qualificados=False, slug=criar_slug_fundo_investimento_valido('Fundo teste'))
        
    def test_buscar_documento_cvm_sucesso(self):
        """Testa busca de documento de valor de fundos na CVM, com sucesso"""
        retorno = buscar_arquivo_csv_historico(datetime.date(2018, 10, 26))
        self.assertEquals(len(retorno), 3)
        self.assertEquals(retorno[0], 'http://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_201810.csv')
        self.assertEquals(retorno[1], 'inf_diario_fi_201810.csv')
        self.assertTrue(hasattr(retorno[2], 'read'))
        
    def test_buscar_documento_cvm_data_futura(self):
        """Testa busca de documento de cadastro de fundos em data futura"""
        with self.assertRaises(ValueError):
            buscar_arquivo_csv_historico(datetime.date.today() + datetime.timedelta(days=60))
            
    def test_processar_registro_sucesso(self):
        """Testa processar uma linha no documento com sucesso"""
        #00.017.024/0001-53;2019-01-02;1134502.30;26.653279500000;1130684.21;0.00;0.00;1
        self.assertTrue(HistoricoValorCotas.objects.all().count() == 0)
        with open('bagogold/fundo_investimento/tests/documentos_historico_valor/historico_registro_novo.csv') as f:
            processar_arquivo_csv(f, 'utf-8')
            
        # Verificações
        self.assertTrue(HistoricoValorCotas.objects.all().count() == 1)

        historico_criado = HistoricoValorCotas.objects.get(fundo_investimento=self.fundo)
        self.assertEquals(historico_criado.data, datetime.date(2019, 1, 2))
        self.assertEquals(historico_criado.valor_cota, Decimal('26.6532795'))
        
    def test_processar_registro_repetido(self):
        """Testa processar uma linha do documento que descreve um fundo ainda não existente, porém sem administrador"""
        #00.017.024/0001-53;2019-01-02;1134502.30;26.653279500000;1130684.21;0.00;0.00;1
        self.assertTrue(HistoricoValorCotas.objects.all().count() == 1)
        with open('bagogold/fundo_investimento/tests/documentos_historico_valor/historico_registro_novo.csv') as f:
            processar_arquivo_csv(f, 'utf-8')
            
        # Verificações
        self.assertTrue(HistoricoValorCotas.objects.all().count() == 2)

        historico_criado = HistoricoValorCotas.objects.get(fundo_investimento=self.fundo)
        self.assertEquals(historico_criado.data, datetime.date(2019, 1, 2))
        self.assertEquals(historico_criado.valor_cota, Decimal('26.6532795'))
        
    def test_processar_registro_fundo_existente(self):
        """Testa processar uma linha no documento que descreve um fundo já existente"""
        #00.017.024/0001-53;2019-01-02;1134502.30;26.653279500000;1130684.21;0.00;0.00;1
        self.assertTrue(HistoricoValorCotas.objects.all().count() == 0)
        with open('bagogold/fundo_investimento/tests/documentos_historico_valor/historico_registro_novo.csv') as f:
            processar_arquivo_csv(f, 'utf-8')
            
        # Verificações
        self.assertTrue(HistoricoValorCotas.objects.all().count() == 0)
        
    def test_processar_arquivo_completo(self):
        """Testa processar um arquivo com cada caso de linha testado"""
        pass
