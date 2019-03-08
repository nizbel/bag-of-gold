# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoAcao, Divisao, \
    CheckpointDivisaoProventosAcao, CheckpointDivisaoAcao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.acoes.models import Acao, ProventoAcao, \
    AtualizacaoSelicProvento, OperacaoAcao, EventoDesdobramentoAcao, \
    EventoAgrupamentoAcao, EventoBonusAcao, EventoAlteracaoAcao, \
    CheckpointAcao, ProventoAcao, CheckpointProventosAcao, UsoProventosOperacaoAcao
from bagogold.bagogold.models.investidores import Investidor
from bagogold.acoes.utils import calcular_qtd_acoes_ate_dia, \
    calcular_qtd_acoes_ate_dia_por_ticker, calcular_qtd_acoes_ate_dia_por_divisao, \
    verificar_se_existe_evento_para_acao, calcular_poupanca_prov_acao_ate_dia, \
    calcular_preco_medio_acoes_ate_dia_por_ticker, calcular_preco_medio_acoes_ate_dia, \
    calcular_poupanca_prov_acao_ate_dia_por_divisao, \
    calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao, \
    calcular_preco_medio_acoes_ate_dia_por_divisao
from bagogold.bagogold.utils.investidores import atualizar_checkpoints
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime
 
class CalcularQuantidadesAcaoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(CalcularQuantidadesAcaoTestCase, cls).setUpTestData()
        user = User.objects.create(username='test', password='test')
        # Guardar investidor
        cls.investidor = user.investidor
        # Guardar divisão geral
        cls.divisao_geral = Divisao.objects.get(nome='Geral')
         
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='Acao BA')
        cls.acao_1 = Acao.objects.create(ticker='BABA3', empresa=empresa_1)
        empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='Acao BB')
        cls.acao_2 = Acao.objects.create(ticker='BBBB3', empresa=empresa_2)
        empresa_3 = Empresa.objects.create(nome='BC', nome_pregao='Acao BC')
        cls.acao_3 = Acao.objects.create(ticker='BCBC3', empresa=empresa_3)
        empresa_4 = Empresa.objects.create(nome='BD', nome_pregao='Acao BD')
        cls.acao_4 = Acao.objects.create(ticker='BDBD3', empresa=empresa_4)
        empresa_5 = Empresa.objects.create(nome='BE', nome_pregao='Acao BE')
        cls.acao_5 = Acao.objects.create(ticker='BEBE3', empresa=empresa_5)
        empresa_6 = Empresa.objects.create(nome='BF', nome_pregao='Acao BF')
        cls.acao_6 = Acao.objects.create(ticker='BFBF3', empresa=empresa_6)
         
        # Desdobramento
        OperacaoAcao.objects.create(acao=cls.acao_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=43, 
                                    preco_unitario=Decimal('100'), corretagem=100, emolumentos=100, destinacao=OperacaoAcao.DESTINACAO_BH)
        # Agrupamento
        OperacaoAcao.objects.create(acao=cls.acao_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=430, 
                                    preco_unitario=Decimal('100'), corretagem=100, emolumentos=100, destinacao=OperacaoAcao.DESTINACAO_BH)
        # Desdobramento + Incorporação
        OperacaoAcao.objects.create(acao=cls.acao_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=37, 
                                    preco_unitario=Decimal('100'), corretagem=100, emolumentos=100, destinacao=OperacaoAcao.DESTINACAO_BH)
        OperacaoAcao.objects.create(acao=cls.acao_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=271, 
                                    preco_unitario=Decimal('100'), corretagem=100, emolumentos=100, destinacao=OperacaoAcao.DESTINACAO_BH)
         
        OperacaoAcao.objects.create(acao=cls.acao_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 11, 11), quantidade=40, 
                                    preco_unitario=Decimal('100'), corretagem=100, emolumentos=100, destinacao=OperacaoAcao.DESTINACAO_BH)
        OperacaoAcao.objects.create(acao=cls.acao_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 11, 12), quantidade=50, 
                                    preco_unitario=Decimal('100'), corretagem=100, emolumentos=100, destinacao=OperacaoAcao.DESTINACAO_BH)
         
        # Operação de venda
        OperacaoAcao.objects.create(acao=cls.acao_6, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=20, 
                                    preco_unitario=Decimal('90'), corretagem=100, emolumentos=100, destinacao=OperacaoAcao.DESTINACAO_BH)
        OperacaoAcao.objects.create(acao=cls.acao_6, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 11, 12), quantidade=20, 
                                    preco_unitario=Decimal('100'), corretagem=100, emolumentos=100, destinacao=OperacaoAcao.DESTINACAO_BH)
         
        for operacao in OperacaoAcao.objects.all():
            DivisaoOperacaoAcao.objects.create(divisao=Divisao.objects.get(investidor=user.investidor), operacao=operacao, quantidade=operacao.quantidade)
         
        # Operação extra para testes de divisão
        operacao_divisao = OperacaoAcao.objects.create(acao=cls.acao_5, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=50, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        cls.divisao_teste = Divisao.objects.create(investidor=user.investidor, nome=u'Divisão de teste')
        DivisaoOperacaoAcao.objects.create(divisao=cls.divisao_teste, operacao=operacao_divisao, quantidade=operacao_divisao.quantidade)
         
        EventoDesdobramentoAcao.objects.create(acao=cls.acao_1, data=datetime.date(2017, 6, 3), proporcao=10)
        EventoAgrupamentoAcao.objects.create(acao=cls.acao_2, data=datetime.date(2017, 6, 3), proporcao=Decimal('0.1'))
        EventoDesdobramentoAcao.objects.create(acao=cls.acao_3, data=datetime.date(2017, 6, 3), proporcao=Decimal('9.3674360842'))
        EventoAlteracaoAcao.objects.create(acao=cls.acao_3, data=datetime.date(2017, 6, 3), novo_acao=cls.acao_4)
         
        EventoDesdobramentoAcao.objects.create(acao=cls.acao_5, data=datetime.date(2017, 6, 3), proporcao=10)
         
        # Proventos
        ProventoAcao.objects.create(acao=cls.acao_1, data_ex=datetime.date(2016, 12, 31), data_pagamento=datetime.date(2017, 1, 14), valor_unitario=Decimal('0.98'),
                                   tipo_provento=ProventoAcao.TIPO_PROVENTO_DIVIDENDO, oficial_bovespa=True)
        ProventoAcao.objects.create(acao=cls.acao_1, data_ex=datetime.date(2017, 1, 31), data_pagamento=datetime.date(2017, 2, 14), valor_unitario=Decimal('9.1'),
                                   tipo_provento=ProventoAcao.TIPO_PROVENTO_JSCP, oficial_bovespa=True)
        ProventoAcao.objects.create(acao=cls.acao_2, data_ex=datetime.date(2017, 1, 31), data_pagamento=datetime.date(2017, 2, 14), valor_unitario=Decimal('9.8'),
                                   tipo_provento=ProventoAcao.TIPO_PROVENTO_DIVIDENDO, oficial_bovespa=True)
          
        ProventoAcao.objects.create(acao=cls.acao_1, data_ex=datetime.date(2017, 7, 31), data_pagamento=datetime.date(2017, 8, 14), valor_unitario=Decimal('0.98'),
                                   tipo_provento=ProventoAcao.TIPO_PROVENTO_DIVIDENDO, oficial_bovespa=True)
        ProventoAcao.objects.create(acao=cls.acao_1, data_ex=datetime.date(2017, 8, 31), data_pagamento=datetime.date(2017, 9, 14), valor_unitario=Decimal('9.1'),
                                   tipo_provento=ProventoAcao.TIPO_PROVENTO_JSCP, oficial_bovespa=True)
        ProventoAcao.objects.create(acao=cls.acao_2, data_ex=datetime.date(2017, 8, 31), data_pagamento=datetime.date(2017, 9, 14), valor_unitario=Decimal('9.8'),
                                   tipo_provento=ProventoAcao.TIPO_PROVENTO_DIVIDENDO, oficial_bovespa=True)
         
         
    def test_calculo_qtd_acao_por_ticker(self):
        """Calcula quantidade de Acaos do usuário individualmente"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_1.ticker), 43)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_2.ticker), 430)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_3.ticker), 37)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_4.ticker), 271)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_5.ticker), 50)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_6.ticker), 20)
         
    def test_calculo_qtd_acoes(self):
        """Calcula quantidade de Acaos do usuário"""
        self.assertDictEqual(calcular_qtd_acoes_ate_dia(self.investidor, datetime.date(2017, 5, 12)), 
                            {self.acao_1.ticker: 43, self.acao_2.ticker: 430, self.acao_3.ticker: 37, self.acao_4.ticker: 271, self.acao_5.ticker: 50, self.acao_6.ticker: 20}) 
        self.assertDictEqual(calcular_qtd_acoes_ate_dia(self.investidor, datetime.date(2017, 11, 13)),
                            {self.acao_1.ticker: 430, self.acao_2.ticker: 43, self.acao_4.ticker: 707, self.acao_5.ticker: 500})
     
    def test_calculo_qtd_apos_agrupamento(self):
        """Verifica se a função que recebe uma quantidade calcula o resultado correto para agrupamento"""
        self.assertEqual(EventoAgrupamentoAcao.objects.get(acao=self.acao_2).qtd_apos(100), 10)
         
    def test_calculo_qtd_apos_desdobramento(self):    
        """Verifica se a função que recebe uma quantidade calcula o resultado correto para desdobramento"""
        self.assertEqual(EventoDesdobramentoAcao.objects.get(acao=self.acao_1).qtd_apos(100), 1000)
     
    def test_verificar_qtd_apos_agrupamento_acao_1(self):
        """Testa se a quantidade de cotas do usuário está correta após o agrupamento do Acao 1"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), self.acao_1.ticker), 430)
     
    def test_verificar_qtd_apos_desdobramento_acao_2(self):
        """Testa se a quantidade de cotas do usuário está correta após o desdobramento do Acao 2"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), self.acao_2.ticker), 43)
             
    def test_verificar_qtd_apos_incorporacao(self):
        """Testa se a quantidade de cotas do usuário está correta após o desdobramento e incorporação do Acao 3"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), self.acao_3.ticker), 0)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), self.acao_4.ticker), 617)
 
    def test_verificar_qtd_divisao_antes_eventos(self):
        """Testa se a quantidade de cotas por divisão está correta antes dos eventos"""
        self.assertDictEqual(calcular_qtd_acoes_ate_dia_por_divisao(datetime.date(2017, 5, 12), self.divisao_geral.id), 
                             {self.acao_1.ticker: 43, self.acao_2.ticker: 430, self.acao_3.ticker: 37, self.acao_4.ticker: 271, self.acao_6.ticker: 20})
        self.assertDictEqual(calcular_qtd_acoes_ate_dia_por_divisao(datetime.date(2017, 5, 12), self.divisao_teste.id), 
                             {self.acao_5.ticker: 50})
         
    def test_verificar_qtd_divisao_apos_eventos(self):
        """Testa se a quantidade de cotas por divisão está correta após os eventos"""
        self.assertDictEqual(calcular_qtd_acoes_ate_dia_por_divisao(datetime.date(2017, 11, 13), self.divisao_geral.id), 
                             {self.acao_1.ticker: 430, self.acao_2.ticker: 43, self.acao_4.ticker: 707})
        self.assertDictEqual(calcular_qtd_acoes_ate_dia_por_divisao(datetime.date(2017, 11, 13), self.divisao_teste.id), 
                             {self.acao_5.ticker: 500})
         
    def test_verificar_checkpoints_apagados(self):
        """Testa se checkpoints são apagados caso quantidades de Acao do usuário se torne zero"""
        self.assertTrue(len(CheckpointAcao.objects.filter(investidor=self.investidor)) > 0)
        for operacao in OperacaoAcao.objects.filter(investidor=self.investidor):
            operacao.delete()
        self.assertFalse(CheckpointAcao.objects.filter(investidor=self.investidor).exists())
         
    def test_verificar_poupanca_proventos(self):
        """Testa se poupança de proventos está com valores corretos"""
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia(self.investidor, datetime.date(2017, 3, 1)), 0)
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia(self.investidor, datetime.date(2017, 10, 1)), Decimal('4755.80'))
        self.assertEqual(CheckpointProventosAcao.objects.get(investidor=self.investidor, ano=2017).valor, Decimal('4755.80'))
         
        # Testar situação alterando uma operação
        operacao = OperacaoAcao.objects.get(acao__ticker=self.acao_1.ticker)
        operacao.quantidade = 45
        operacao.save()
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia(self.investidor, datetime.date(2017, 10, 1)), Decimal('4957.40'))
        self.assertEqual(CheckpointProventosAcao.objects.get(investidor=self.investidor, ano=2017).valor, Decimal('4957.40'))
#         calcular_poupanca_prov_acao_ate_dia(self.investidor, datetime.date(2018, 8, 12))
         
        # Testar situação adicionando uso de proventos
        UsoProventosOperacaoAcao.objects.create(operacao=operacao, divisao_operacao=DivisaoOperacaoAcao.objects.get(operacao=operacao), qtd_utilizada=100)
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia(self.investidor, datetime.date(2017, 10, 1)), Decimal('4857.40'))
        self.assertEqual(CheckpointProventosAcao.objects.get(investidor=self.investidor, ano=2017).valor, Decimal('4857.40'))
         
         
    def test_verificar_poupanca_proventos_por_divisao(self):
        """Testa se poupança de proventos está com os valores corretos para cada divisão"""
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1)), 0)
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia_por_divisao(self.divisao_teste, datetime.date(2017, 3, 1)), 0)
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia_por_divisao(self.divisao_geral, datetime.date(2017, 10, 1)), Decimal('4755.80'))
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia_por_divisao(self.divisao_teste, datetime.date(2017, 10, 1)), 0)
        self.assertEqual(CheckpointDivisaoProventosAcao.objects.get(divisao=self.divisao_geral, ano=2017).valor, Decimal('4755.80'))
        self.assertFalse(CheckpointDivisaoProventosAcao.objects.filter(divisao=self.divisao_teste, ano=2017).exists())
         
        # Testar situação alterando uma operação
        operacao = OperacaoAcao.objects.get(acao__ticker=self.acao_1.ticker)
        operacao.quantidade = 45
        operacao.save()
        # Alterar divisao operação
        divisao_operacao = DivisaoOperacaoAcao.objects.get(operacao=operacao)
        divisao_operacao.quantidade = 45
        divisao_operacao.save()
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia_por_divisao(self.divisao_geral, datetime.date(2017, 10, 1)), Decimal('4957.40'))
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia_por_divisao(self.divisao_teste, datetime.date(2017, 10, 1)), 0)
        self.assertEqual(CheckpointDivisaoProventosAcao.objects.get(divisao=self.divisao_geral, ano=2017).valor, Decimal('4957.40'))
         
        # Testar situação adicionando uso de proventos
        UsoProventosOperacaoAcao.objects.create(operacao=operacao, divisao_operacao=divisao_operacao, qtd_utilizada=100)
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia_por_divisao(self.divisao_geral, datetime.date(2017, 10, 1)), Decimal('4857.40'))
        self.assertEqual(calcular_poupanca_prov_acao_ate_dia_por_divisao(self.divisao_teste, datetime.date(2017, 10, 1)), 0)
        self.assertEqual(CheckpointDivisaoProventosAcao.objects.get(divisao=self.divisao_geral, ano=2017).valor, Decimal('4857.40'))
         
    def test_verificar_preco_medio(self):
        """Testa cálculos de preço médio"""
        # Testar funções individuais
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 3, 1), self.acao_1.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_1.ticker), Decimal(4500) / 43, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), self.acao_1.ticker), Decimal(4500) / 430, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 11, 20), self.acao_1.ticker), Decimal(4500) / 430 - Decimal('9.1'), places=3)
         
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 3, 1), self.acao_2.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_2.ticker), Decimal(43200) / 430, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), self.acao_2.ticker), Decimal(43200) / 43, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 11, 20), self.acao_2.ticker), Decimal(43200) / 43, places=3)
         
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 3, 1), self.acao_3.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_3.ticker), Decimal(3900) / 37, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), self.acao_3.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 11, 20), self.acao_3.ticker), 0, places=3)
         
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 3, 1), self.acao_4.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), self.acao_4.ticker), Decimal(27300) / 271, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), self.acao_4.ticker), Decimal(27300 + 3900) / 617, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 11, 20), self.acao_4.ticker), Decimal(27300 + 3900 + 9400) / 707, places=3)
         
        # Testar função geral
        for data in [datetime.date(2017, 3, 1), datetime.date(2017, 5, 12), datetime.date(2017, 6, 4), datetime.date(2017, 11, 20)]:
            precos_medios = calcular_preco_medio_acoes_ate_dia(self.investidor, data)
            for ticker in Acao.objects.all().values_list('ticker', flat=True):
                qtd_individual = calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, data, ticker)
                if qtd_individual > 0:
                    self.assertAlmostEqual(precos_medios[ticker], qtd_individual, places=3)
                else:
                    self.assertNotIn(ticker, precos_medios.keys())
         
        # Testar checkpoints
        self.assertFalse(CheckpointAcao.objects.filter(investidor=self.investidor, ano=2016).exists())
        for acao in Acao.objects.all().exclude(ticker__in=[self.acao_3.ticker, self.acao_6.ticker]):
            self.assertAlmostEqual(CheckpointAcao.objects.get(investidor=self.investidor, ano=2017, acao=acao).preco_medio, 
                                   calcular_preco_medio_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2017, 12, 31), acao.ticker), places=3)
        # Garantir que o checkpoint do BCPO11 e BFPO11 não foi criado pois não há um ano anterior com quantidade diferente de 0, e
        #a quantidade atual é 0
        self.assertFalse(CheckpointAcao.objects.filter(investidor=self.investidor, ano=2017, acao=self.acao_3).exists())
        self.assertFalse(CheckpointAcao.objects.filter(investidor=self.investidor, ano=2017, acao=self.acao_6).exists())
             
    def test_verificar_preco_medio_por_divisao(self):
        """Testa cálculos de preço médio por divisão"""
        # Testar funções individuais
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1), self.acao_1.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 5, 12), self.acao_1.ticker), Decimal(4500) / 43, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 6, 4), self.acao_1.ticker), Decimal(4500) / 430, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 11, 20), self.acao_1.ticker), Decimal(4500) / 430 - Decimal('9.1'), places=3)
         
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1), self.acao_2.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 5, 12), self.acao_2.ticker), Decimal(43200) / 430, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 6, 4), self.acao_2.ticker), Decimal(43200) / 43, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 11, 20), self.acao_2.ticker), Decimal(43200) / 43, places=3)
         
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1), self.acao_3.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 5, 12), self.acao_3.ticker), Decimal(3900) / 37, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 6, 4), self.acao_3.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 11, 20), self.acao_3.ticker), 0, places=3)
         
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1), self.acao_4.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 5, 12), self.acao_4.ticker), Decimal(27300) / 271, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 6, 4), self.acao_4.ticker), Decimal(27300 + 3900) / 617, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 11, 20), self.acao_4.ticker), Decimal(27300 + 3900 + 9400) / 707, places=3)
         
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_teste, datetime.date(2017, 3, 1), self.acao_5.ticker), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_teste, datetime.date(2017, 5, 12), self.acao_5.ticker), Decimal(5200) / 50, places=3)
         
        # Testar função geral
        for data in [datetime.date(2017, 3, 1), datetime.date(2017, 5, 12), datetime.date(2017, 6, 4), datetime.date(2017, 11, 20)]:
            precos_medios = calcular_preco_medio_acoes_ate_dia_por_divisao(self.divisao_geral, data)
            for ticker in Acao.objects.all().values_list('ticker', flat=True):
                qtd_individual = calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, data, ticker)
                if qtd_individual > 0:
                    self.assertAlmostEqual(precos_medios[ticker], qtd_individual, places=3)
                else:
                    self.assertNotIn(ticker, precos_medios.keys())
         
        # Testar checkpoints
        self.assertFalse(CheckpointDivisaoAcao.objects.filter(divisao=self.divisao_geral, ano=2016).exists())
        for acao in Acao.objects.all().exclude(ticker__in=[self.acao_3.ticker, self.acao_5.ticker, self.acao_6.ticker]):
            self.assertAlmostEqual(CheckpointDivisaoAcao.objects.get(divisao=self.divisao_geral, ano=2017, acao=acao).preco_medio, 
                                   calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 12, 31), acao.ticker), places=3)
        # Garantir que o checkpoint do BCPO11 e BFPO11 não foi criado pois não há um ano anterior com quantidade diferente de 0, e
        #a quantidade atual é 0
        self.assertFalse(CheckpointDivisaoAcao.objects.filter(divisao=self.divisao_geral, ano=2017, acao=self.acao_3).exists())
        self.assertFalse(CheckpointDivisaoAcao.objects.filter(divisao=self.divisao_geral, ano=2017, acao=self.acao_6).exists())
        self.assertAlmostEqual(CheckpointDivisaoAcao.objects.get(divisao=self.divisao_teste, ano=2017, acao=self.acao_5).preco_medio, 
                               calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(self.divisao_teste, datetime.date(2017, 12, 31), self.acao_5.ticker), places=3)
             
# class PerformanceCheckpointAcaoTestCase(TestCase):
#     def setUp(self):
#         user = User.objects.create(username='test', password='test')
#          
#         empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='Acao BA')
#         acao_1 = Acao.objects.create(ticker='BAPO11', empresa=empresa_1)
#         empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='Acao BB')
#         acao_2 = Acao.objects.create(ticker='BBPO11', empresa=empresa_2)
#         empresa_3 = Empresa.objects.create(nome='BC', nome_pregao='Acao BC')
#         acao_3 = Acao.objects.create(ticker='BCPO11', empresa=empresa_3)
#         empresa_4 = Empresa.objects.create(nome='BD', nome_pregao='Acao BD')
#         acao_4 = Acao.objects.create(ticker='BDPO11', empresa=empresa_4)
#          
#         # Gerar operações mensalmente de 2012 a 2016
#         for ano in range(2012, 2018):
#             for mes in range(1, 13):
#                 # Desdobramento
#                 OperacaoAcao.objects.create(acao=acao_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
#                 # Agrupamento
#                 OperacaoAcao.objects.create(acao=acao_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
#                 # Desdobramento + Incorporação
#                 OperacaoAcao.objects.create(acao=acao_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
#                 OperacaoAcao.objects.create(acao=acao_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
#          
#         EventoDesdobramentoAcao.objects.create(acao=acao_4, data=datetime.date(2016, 6, 3), proporcao=Decimal('0.933'))
#          
#         EventoDesdobramentoAcao.objects.create(acao=acao_1, data=datetime.date(2017, 6, 3), proporcao=10)
#         EventoAgrupamentoAcao.objects.create(acao=acao_2, data=datetime.date(2017, 6, 3), proporcao=Decimal('0.1'))
#         EventoDesdobramentoAcao.objects.create(acao=acao_3, data=datetime.date(2017, 6, 3), proporcao=10)
#         EventoIncorporacaoAcao.objects.create(acao=acao_3, data=datetime.date(2017, 6, 3), novo_acao=acao_4)
#          
#     def calculo_forma_antiga(self, investidor, dia):
#         if not all([verificar_se_existe_evento_para_acao(acao_ticker, dia) for acao_ticker in OperacaoAcao.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
#                                                                                                 .order_by('acao__id').distinct('acao__id').values_list('acao__ticker', flat=True)]):
#             qtd_acao = dict(OperacaoAcao.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).annotate(ticker=F('acao__ticker')).values('ticker') \
#                 .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
#                                     When(tipo_operacao='V', then=F('quantidade')*-1),
#                                     output_field=DecimalField()))).values_list('ticker', 'total').exclude(total=0))
#      
#         else:
#             qtd_acao = {}
#             for acao in Acao.objects.filter(id__in=OperacaoAcao.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
#                                                                                                 .order_by('acao__id').distinct('acao__id').values_list('acao', flat=True)):
#                 qtd_acao_na_data = self.calculo_forma_antiga_por_ticker(investidor, dia, acao.ticker)
#                 if qtd_acao_na_data > 0:
#                     qtd_acao[acao.ticker] = qtd_acao_na_data
#         return qtd_acao
#      
#     def calculo_forma_antiga_por_ticker(self, investidor, dia, ticker, ignorar_incorporacao_id=None):
#         if not verificar_se_existe_evento_para_acao(ticker, dia):
#             qtd_acao = OperacaoAcao.objects.filter(acao__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True) \
#                 .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
#                                           When(tipo_operacao='V', then=F('quantidade')*-1),
#                                           output_field=DecimalField())))['total'] or 0
#         else:
#             qtd_acao = 0
#          
#             operacoes = OperacaoAcao.objects.filter(acao__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True) \
#                 .annotate(qtd_final=(Case(When(tipo_operacao='C', then=F('quantidade')),
#                                           When(tipo_operacao='V', then=F('quantidade')*-1),
#                                           output_field=DecimalField()))).annotate(tipo=Value(u'Operação', output_field=CharField()))
#                                        
#                                        
#             # Verificar agrupamentos e desdobramentos
#             agrupamentos = EventoAgrupamentoAcao.objects.filter(acao__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))
#  
#             desdobramentos = EventoDesdobramentoAcao.objects.filter(acao__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
#          
#             incorporacoes = EventoIncorporacaoAcao.objects.filter(Q(acao__ticker=ticker, data__lte=dia) | Q(novo_acao__ticker=ticker, data__lte=dia)).exclude(id=ignorar_incorporacao_id) \
#                 .annotate(tipo=Value(u'Incorporação', output_field=CharField()))
#          
#             lista_conjunta = sorted(chain(agrupamentos, desdobramentos, incorporacoes, operacoes), key=attrgetter('data'))
#          
#             for elemento in lista_conjunta:
#                 if elemento.tipo == 'Operação':
#                     qtd_acao += elemento.qtd_final
#                 elif elemento.tipo == 'Agrupamento':
#                     qtd_acao = elemento.qtd_apos(qtd_acao)
#                 elif elemento.tipo == 'Desdobramento':
#                     qtd_acao = elemento.qtd_apos(qtd_acao)
#                 elif elemento.tipo == 'Incorporação':
#                     if elemento.acao.ticker == ticker:
#                         qtd_acao = 0
#                     elif elemento.novo_acao.ticker == ticker:
#                         qtd_acao += self.calculo_forma_antiga_por_ticker(investidor, elemento.data, elemento.acao.ticker, elemento.id)
#          
#         return qtd_acao
#      
#     def test_verificar_performance(self):
#         """Verifica se a forma de calcular quantidades a partir de checkpoints melhora a performance"""
#         investidor = Investidor.objects.get(user__username='test')
#          
#         data_final = datetime.date(2018, 1, 1)
#         # Verificar no ano de 2017 após eventos
#         inicio = datetime.datetime.now()
#         qtd_antigo = self.calculo_forma_antiga(investidor, data_final)
#         fim_antigo = datetime.datetime.now() - inicio
#              
#         inicio = datetime.datetime.now()
#         qtd_novo = calcular_qtd_acoes_ate_dia(investidor, data_final)
#         fim_novo = datetime.datetime.now() - inicio
#          
# #         print '%s: ' % (data_final.year), fim_antigo, fim_novo, (Decimal((fim_novo - fim_antigo).total_seconds() / fim_antigo.total_seconds() * 100)).quantize(Decimal('0.01'))
#          
#         self.assertDictEqual(qtd_antigo, qtd_novo)
#         self.assertTrue(fim_novo < fim_antigo)
         
class CheckpointEventoAposOperacaoTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
        user.investidor.data_ultimo_acesso = datetime.date(2016, 5, 11)
        user.investidor.save()
        # Guardar investidor
        self.investidor = user.investidor
         
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='Acao BA')
        acao_1 = Acao.objects.create(ticker='BAPO11', empresa=empresa_1)
        empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='Acao BB')
        acao_2 = Acao.objects.create(ticker='BBPO11', empresa=empresa_1)
        OperacaoAcao.objects.create(acao=acao_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 1, 10), quantidade=24, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoAcao.objects.create(acao=acao_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 3, 13), quantidade=13, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
         
         
        OperacaoAcao.objects.create(acao=acao_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 9, 1), quantidade=45, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoAcao.objects.create(acao=acao_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 8, 15), quantidade=82, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoAcao.objects.create(acao=acao_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 10, 20), quantidade=102, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoAcao.objects.create(acao=acao_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 10, 31), quantidade=42, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
         
        EventoAlteracaoAcao.objects.create(acao=acao_1, data=datetime.date(2017, 5, 17), novo_acao=acao_2)
        EventoDesdobramentoAcao.objects.create(acao=acao_2, data=datetime.date(2017, 5, 17), proporcao=Decimal('10'))
        EventoDesdobramentoAcao.objects.create(acao=acao_1, data=datetime.date(2017, 5, 17), proporcao=Decimal('9.3674360842'))
         
    def test_qtd(self):
        """Testa se algoritmo calculou quantidade atual corretamente"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, datetime.date(2018, 2, 13), 'BBPO11'), 617)
 
class AtualizarCheckpointAnualTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(AtualizarCheckpointAnualTestCase, cls).setUpTestData()
        user = User.objects.create(username='test', password='test')
        user.investidor.data_ultimo_acesso = datetime.date(2016, 5, 11)
        user.investidor.save()
         
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='Acao BA')
        acao_1 = Acao.objects.create(ticker='BAPO11', empresa=empresa_1)
         
        OperacaoAcao.objects.create(acao=acao_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2016, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        # Gera operação no futuro para depois trazer para ano atual
        OperacaoAcao.objects.create(acao=acao_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(datetime.date.today().year+1, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        # Apagar checkpoint gerado
        CheckpointAcao.objects.filter(ano__gt=datetime.date.today().year).delete()
          
    def test_atualizacao_ao_logar_prox_ano(self):
        """Verifica se é feita atualização ao logar em pŕoximo ano"""
        investidor = Investidor.objects.get(user__username='test')
        acao = Acao.objects.get(ticker='BAPO11')
         
        # Verifica que existe checkpoint até ano atual
        ano_atual = datetime.date.today().year
        self.assertTrue(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).exists())
         
        # Apaga ano atual
        CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).delete()
        self.assertFalse(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).exists())
         
        # Chamar o teste do middleware de ultimo acesso
        if investidor.data_ultimo_acesso.year < ano_atual:
            atualizar_checkpoints(investidor)
 
        # Verifica se ao logar foi gerado novamente checkpoint
        self.assertTrue(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).exists())
         
    def test_atualizacao_ao_logar_apos_varios_anos(self):
        """Verifica se é feita atualização ao logar depois de vários anos"""
        investidor = Investidor.objects.get(user__username='test')
        acao = Acao.objects.get(ticker='BAPO11')
         
        # Verifica que existe checkpoint até ano atual
        ano_atual = datetime.date.today().year
        self.assertTrue(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).exists())
         
        # Apaga ano atual e ano passado
        CheckpointAcao.objects.filter(investidor=investidor, ano__gte=ano_atual-1, acao=acao).delete()
        self.assertFalse(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).exists())
        self.assertFalse(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual-1, acao=acao).exists())
         
        # Chamar o teste do middleware de ultimo acesso
        if investidor.data_ultimo_acesso.year < ano_atual:
            atualizar_checkpoints(investidor)
 
        # Verifica se ao logar foi gerado novamente checkpoint
        self.assertTrue(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).exists())
        self.assertTrue(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual-1, acao=acao).exists())
         
    def test_nao_atualizar_caso_mesmo_ano(self):
        """Verificar se em caso de já haver checkpoint no ano, função não altera nada"""
        investidor = Investidor.objects.get(user__username='test')
        acao = Acao.objects.get(ticker='BAPO11')
        checkpoint = CheckpointAcao.objects.get(investidor=investidor, ano=datetime.date.today().year, acao=acao)
         
        # Chamar atualizar ano
        atualizar_checkpoints(investidor)
         
        # Verificar se houve alteração no checkpoint
        self.assertEqual(checkpoint, CheckpointAcao.objects.get(investidor=investidor, ano=datetime.date.today().year, acao=acao))
         
    def test_verificar_checkpoint_operacao_ano_futuro(self):
        """Verificar se checkpoint de operação no futuro funciona ao chegar no ano da operação"""
        investidor = Investidor.objects.get(user__username='test')
        acao = Acao.objects.get(ticker='BAPO11')
         
        # Apagar ano atual para fingir que acabamos de chegar a esse ano
        ano_atual = datetime.date.today().year
        self.assertTrue(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).exists())
        CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).delete()
        self.assertFalse(CheckpointAcao.objects.filter(investidor=investidor, ano=ano_atual, acao=acao).exists())
         
        # Trazer operação do futuro para ano atual
        OperacaoAcao.objects.filter(investidor=investidor, data__gt=datetime.date.today()).update(data=datetime.date.today())
         
        # Atualizar da forma como é feito pelo middleware de ultimo acesso
        if investidor.data_ultimo_acesso.year < ano_atual:
            atualizar_checkpoints(investidor)
             
        # Verificar se quantidade de cotas está correta
        self.assertEqual(CheckpointAcao.objects.get(investidor=investidor, ano=ano_atual, acao=acao).quantidade, 86)
         
    def test_checkpoints_venda_cotas(self):
        """Verificar se checkpoints são apagados quando cota é vendida"""
        investidor = Investidor.objects.get(user__username='test')
        acao = Acao.objects.get(ticker='BAPO11')
         
        ano_atual = datetime.date.today().year
        OperacaoAcao.objects.create(acao=acao, investidor=investidor, tipo_operacao='V', data=datetime.date(2016, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        self.assertFalse(CheckpointAcao.objects.filter(investidor=investidor, acao=acao).exists())
