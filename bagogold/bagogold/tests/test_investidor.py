# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao, Acao, HistoricoAcao
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLCI_LCA, \
    DivisaoOperacaoFII, DivisaoOperacaoAcao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.investidores import buscar_ultimas_operacoes, \
    buscar_totais_atuais_investimentos
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from bagogold.fii.models import OperacaoFII, FII, HistoricoFII
from bagogold.lci_lca.models import LetraCredito, OperacaoLetraCredito, \
    HistoricoPorcentagemLetraCredito, HistoricoVencimentoLetraCredito
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from random import uniform
import datetime

class TelaInicioTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        super(TelaInicioTestCase, cls).setUpTestData()
        # Investidor
        user = User.objects.create(username='tester')
        cls.investidor = user.investidor
        
        # Divisão
        divisao1 = Divisao.objects.create(investidor=user.investidor, nome='Teste 1')
        divisao2 = Divisao.objects.create(investidor=user.investidor, nome='Teste 2')
        
        # Data do dia
        data_atual = datetime.date(2016, 10, 26)
        
        # Operações
        # Ação
        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
        acao = Acao.objects.create(ticker='TEST3', empresa=empresa)
        operacao_acoes1 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(20), corretagem=Decimal(10), quantidade=200,
                                       data=data_atual - datetime.timedelta(days=0), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        divisao_operacao_acoes1 = DivisaoOperacaoAcao.objects.create(divisao=divisao1, operacao=operacao_acoes1, quantidade=operacao_acoes1.quantidade)
        operacao_acoes2 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(20), corretagem=Decimal(5), quantidade=100, 
                                       data=data_atual - datetime.timedelta(days=1), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        divisao_operacao_acoes2 = DivisaoOperacaoAcao.objects.create(divisao=divisao2, operacao=operacao_acoes2, quantidade=operacao_acoes2.quantidade)
        operacao_acoes3 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(10), corretagem=Decimal(10), quantidade=300, 
                                       data=data_atual - datetime.timedelta(days=2), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        divisao_operacao_acoes3 = DivisaoOperacaoAcao.objects.create(divisao=divisao2, operacao=operacao_acoes3, quantidade=operacao_acoes3.quantidade)
        
        # FII
        fii = FII.objects.create(ticker='TEST11')
        operacao_fii1 = OperacaoFII.objects.create(investidor=user.investidor, preco_unitario=Decimal(15), corretagem=Decimal(10), quantidade=400, 
                                    data=data_atual - datetime.timedelta(days=1), tipo_operacao='C', fii=fii, emolumentos=Decimal(0))
        divisao_operacao_fii1 = DivisaoOperacaoFII.objects.create(divisao=divisao1, operacao=operacao_fii1, quantidade=operacao_fii1.quantidade)
        operacao_fii2 = OperacaoFII.objects.create(investidor=user.investidor, preco_unitario=Decimal(100), corretagem=Decimal(10), quantidade=10, 
                                    data=data_atual - datetime.timedelta(days=2), tipo_operacao='C', fii=fii, emolumentos=Decimal(0))
        divisao_operacao_fii2 = DivisaoOperacaoFII.objects.create(divisao=divisao1, operacao=operacao_fii2, quantidade=operacao_fii2.quantidade)
        
        # Letra de Crédito
        lci_lca = LetraCredito.objects.create(nome='Letra de teste', investidor=user.investidor, tipo_rendimento=LetraCredito.LCI_LCA_DI)
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci_lca, vencimento=1080)
        lci_lca_porcentagem = HistoricoPorcentagemLetraCredito.objects.create(letra_credito=lci_lca, porcentagem=Decimal(90))
        operacao_lci_lca1 = OperacaoLetraCredito.objects.create(investidor=user.investidor, letra_credito=lci_lca, data=data_atual - datetime.timedelta(days=0), tipo_operacao='C',
                                            quantidade=Decimal(1000))
        divisao_operacao_lci_lca1 = DivisaoOperacaoLCI_LCA.objects.create(divisao=divisao1, operacao=operacao_lci_lca1, quantidade=operacao_lci_lca1.quantidade)
        operacao_lci_lca2 = OperacaoLetraCredito.objects.create(investidor=user.investidor, letra_credito=lci_lca, data=data_atual - datetime.timedelta(days=1), tipo_operacao='C',
                                            quantidade=Decimal(2000))
        divisao_operacao_lci_lca2 = DivisaoOperacaoLCI_LCA.objects.create(divisao=divisao2, operacao=operacao_lci_lca2, quantidade=operacao_lci_lca2.quantidade)
        
        # Gerar valores históricos
        date_list = [data_atual - datetime.timedelta(days=x) for x in range(0, (data_atual - datetime.date(2016, 1, 1)).days+1)]
        date_list = [data for data in date_list if data.weekday() < 5 and not verificar_feriado_bovespa(data)]
        
        for data in date_list:
            HistoricoAcao.objects.create(data=data, acao=acao, preco_unitario=Decimal(uniform(10, 20)))
            HistoricoFII.objects.create(data=data, fii=fii, preco_unitario=Decimal(uniform(10, 20)))
            HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(uniform(12, 15)))
        
    #####################################################################
    # Testes com a busca de últimas operações
    #####################################################################
    def test_buscar_ultimas_cinco_operacoes_deve_trazer_cinco(self):
        """Busca últimas 5 operações"""
        self.assertTrue(len(buscar_ultimas_operacoes(self.investidor, 5)) == 5)
        
    def test_buscar_ultimas_dez_operacoes_deve_trazer_sete(self):
        """Testar se buscar últimas 10 operações traz apenas as 7"""
        self.assertTrue(len(buscar_ultimas_operacoes(self.investidor, 10)) == 7)
    
    def test_buscar_ultimas_cinco_operacoes_nao_deve_trazer_duas(self):
        """Verificar se últimas operações não incluem operações com data de 2 dias atrás"""
        ultimas_operacoes = buscar_ultimas_operacoes(self.investidor, 5)
        
        self.assertNotIn(OperacaoAcao.objects.get(data=datetime.date(2016, 10, 26) - datetime.timedelta(days=2)), ultimas_operacoes)
        self.assertNotIn(OperacaoFII.objects.get(data=datetime.date(2016, 10, 26) - datetime.timedelta(days=2)), ultimas_operacoes)
        
    def test_buscar_ultimas_operacoes_deve_ser_ordenado_decrescente_por_data(self):
        """Verificar se últimas operações está ordenado de maneira decrescente por data"""
        ultimas_operacoes = buscar_ultimas_operacoes(self.investidor, 5)
        
        data = ultimas_operacoes[0].data
        for operacao in ultimas_operacoes[1:]:
            self.assertTrue(operacao.data <= data)
            data = operacao.data
            
    #####################################################################
    # Testes com a busca de valores atuais dos investimentos
    #####################################################################
    def test_buscar_valores_atuais_deve_conter_todos_tipos_de_investimento(self):
        """Testar se traz todos os tipos de investimentos"""
        valores_atuais = buscar_totais_atuais_investimentos(self.investidor)
        
        self.assertIn('Ações', valores_atuais.keys())
        self.assertIn('CDB/RDB', valores_atuais.keys())
        self.assertIn('FII', valores_atuais.keys())
        self.assertIn('Fundos de Inv.', valores_atuais.keys())
        self.assertIn('LCI/LCA', valores_atuais.keys())
        self.assertIn('Tesouro Direto', valores_atuais.keys())
        
    def test_buscar_valores_atuais_deve_ter_valores_nao_zerados(self):
        """Testar se traz valores diferentes de zero para os investimentos que o investidor possui"""
        valores_atuais = buscar_totais_atuais_investimentos(self.investidor)
        
        self.assertNotEqual(valores_atuais['Ações'], Decimal(0))
        self.assertNotEqual(valores_atuais['FII'], Decimal(0))
        self.assertNotEqual(valores_atuais['LCI/LCA'], Decimal(0))  
        
    def test_buscar_valores_atuais_deve_ter_valores_zerados(self):
        """Testar se traz 0 para os investimentos que o investidor não possui"""
        valores_atuais = buscar_totais_atuais_investimentos(self.investidor)
        
        self.assertEqual(valores_atuais['CDB/RDB'], Decimal(0))
        self.assertEqual(valores_atuais['Fundos de Inv.'], Decimal(0))
        self.assertEqual(valores_atuais['Tesouro Direto'], Decimal(0))
        