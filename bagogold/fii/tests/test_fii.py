# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII, Divisao, \
    CheckpointDivisaoProventosFII, CheckpointDivisaoFII
from bagogold.bagogold.models.empresa import Empresa
from bagogold.fii.models import FII, OperacaoFII, \
    EventoDesdobramentoFII, EventoAgrupamentoFII, EventoIncorporacaoFII, \
    CheckpointFII, ProventoFII, CheckpointProventosFII
from bagogold.bagogold.models.investidores import Investidor
from bagogold.fii.utils import calcular_qtd_fiis_ate_dia, \
    calcular_qtd_fiis_ate_dia_por_ticker, calcular_qtd_fiis_ate_dia_por_divisao, \
    verificar_se_existe_evento_para_fii, calcular_poupanca_prov_fii_ate_dia, \
    calcular_preco_medio_fiis_ate_dia_por_ticker, calcular_preco_medio_fiis_ate_dia, \
    calcular_poupanca_prov_fii_ate_dia_por_divisao, \
    calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao, \
    calcular_preco_medio_fiis_ate_dia_por_divisao
from bagogold.bagogold.utils.investidores import atualizar_checkpoints
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When, Value
from django.db.models.fields import DecimalField, CharField
from django.db.models.query_utils import Q
from django.test import TestCase
from itertools import chain
from operator import attrgetter
import datetime

class CalcularQuantidadesFIITestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
        # Guardar investidor
        self.investidor = user.investidor
        # Guardar divisão geral
        self.divisao_geral = Divisao.objects.get(nome='Geral')
        
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
        self.fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
        empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='FII BB')
        self.fii_2 = FII.objects.create(ticker='BBPO11', empresa=empresa_2)
        empresa_3 = Empresa.objects.create(nome='BC', nome_pregao='FII BC')
        self.fii_3 = FII.objects.create(ticker='BCPO11', empresa=empresa_3)
        empresa_4 = Empresa.objects.create(nome='BD', nome_pregao='FII BD')
        self.fii_4 = FII.objects.create(ticker='BDPO11', empresa=empresa_4)
        empresa_5 = Empresa.objects.create(nome='BE', nome_pregao='FII BE')
        self.fii_5 = FII.objects.create(ticker='BEPO11', empresa=empresa_5)
        empresa_6 = Empresa.objects.create(nome='BF', nome_pregao='FII BF')
        self.fii_6 = FII.objects.create(ticker='BFPO11', empresa=empresa_6)
        
        # Desdobramento
        OperacaoFII.objects.create(fii=self.fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        # Agrupamento
        OperacaoFII.objects.create(fii=self.fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=430, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        # Desdobramento + Incorporação
        OperacaoFII.objects.create(fii=self.fii_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=37, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoFII.objects.create(fii=self.fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=271, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        
        OperacaoFII.objects.create(fii=self.fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 11, 11), quantidade=40, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoFII.objects.create(fii=self.fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 11, 12), quantidade=50, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        
        # Operação de venda
        OperacaoFII.objects.create(fii=self.fii_6, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=20, preco_unitario=Decimal('90'), corretagem=100, emolumentos=100)
        OperacaoFII.objects.create(fii=self.fii_6, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 11, 12), quantidade=20, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        
        for operacao in OperacaoFII.objects.all():
            DivisaoOperacaoFII.objects.create(divisao=Divisao.objects.get(investidor=user.investidor), operacao=operacao, quantidade=operacao.quantidade)
        
        # Operação extra para testes de divisão
        operacao_divisao = OperacaoFII.objects.create(fii=self.fii_5, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=50, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        self.divisao_teste = Divisao.objects.create(investidor=user.investidor, nome=u'Divisão de teste')
        DivisaoOperacaoFII.objects.create(divisao=self.divisao_teste, operacao=operacao_divisao, quantidade=operacao_divisao.quantidade)
        
        EventoDesdobramentoFII.objects.create(fii=self.fii_1, data=datetime.date(2017, 6, 3), proporcao=10)
        EventoAgrupamentoFII.objects.create(fii=self.fii_2, data=datetime.date(2017, 6, 3), proporcao=Decimal('0.1'))
        EventoDesdobramentoFII.objects.create(fii=self.fii_3, data=datetime.date(2017, 6, 3), proporcao=Decimal('9.3674360842'))
        EventoIncorporacaoFII.objects.create(fii=self.fii_3, data=datetime.date(2017, 6, 3), novo_fii=self.fii_4)
        
        EventoDesdobramentoFII.objects.create(fii=self.fii_5, data=datetime.date(2017, 6, 3), proporcao=10)
        
        # Proventos
        ProventoFII.objects.create(fii=self.fii_1, data_ex=datetime.date(2016, 12, 31), data_pagamento=datetime.date(2017, 1, 14), valor_unitario=Decimal('0.98'),
                                   tipo_provento='R', oficial_bovespa=True)
        ProventoFII.objects.create(fii=self.fii_1, data_ex=datetime.date(2017, 1, 31), data_pagamento=datetime.date(2017, 2, 14), valor_unitario=Decimal('9.1'),
                                   tipo_provento='A', oficial_bovespa=True)
        ProventoFII.objects.create(fii=self.fii_2, data_ex=datetime.date(2017, 1, 31), data_pagamento=datetime.date(2017, 2, 14), valor_unitario=Decimal('9.8'),
                                   tipo_provento='R', oficial_bovespa=True)
        
        ProventoFII.objects.create(fii=self.fii_1, data_ex=datetime.date(2017, 7, 31), data_pagamento=datetime.date(2017, 8, 14), valor_unitario=Decimal('0.98'),
                                   tipo_provento='R', oficial_bovespa=True)
        ProventoFII.objects.create(fii=self.fii_1, data_ex=datetime.date(2017, 8, 31), data_pagamento=datetime.date(2017, 9, 14), valor_unitario=Decimal('9.1'),
                                   tipo_provento='A', oficial_bovespa=True)
        ProventoFII.objects.create(fii=self.fii_2, data_ex=datetime.date(2017, 8, 31), data_pagamento=datetime.date(2017, 9, 14), valor_unitario=Decimal('9.8'),
                                   tipo_provento='R', oficial_bovespa=True)
        
        
    def test_calculo_qtd_fii_por_ticker(self):
        """Calcula quantidade de FIIs do usuário individualmente"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BAPO11'), 43)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BBPO11'), 430)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BCPO11'), 37)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BDPO11'), 271)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BEPO11'), 50)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BFPO11'), 20)
        
    def test_calculo_qtd_fiis(self):
       """Calcula quantidade de FIIs do usuário"""
       self.assertDictEqual(calcular_qtd_fiis_ate_dia(self.investidor, datetime.date(2017, 5, 12)), 
                            {'BAPO11': 43, 'BBPO11': 430, 'BCPO11': 37, 'BDPO11': 271, 'BEPO11': 50, 'BFPO11': 20}) 
       self.assertDictEqual(calcular_qtd_fiis_ate_dia(self.investidor, datetime.date(2017, 11, 13)),
                            {'BAPO11': 430, 'BBPO11': 43, 'BDPO11': 707, 'BEPO11': 500})
    
    def test_calculo_qtd_apos_agrupamento(self):
        """Verifica se a função que recebe uma quantidade calcula o resultado correto para agrupamento"""
        self.assertEqual(EventoAgrupamentoFII.objects.get(fii=self.fii_2).qtd_apos(100), 10)
        
    def test_calculo_qtd_apos_desdobramento(self):    
        """Verifica se a função que recebe uma quantidade calcula o resultado correto para desdobramento"""
        self.assertEqual(EventoDesdobramentoFII.objects.get(fii=self.fii_1).qtd_apos(100), 1000)
    
    def test_verificar_qtd_apos_agrupamento_fii_1(self):
        """Testa se a quantidade de cotas do usuário está correta após o agrupamento do FII 1"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), 'BAPO11'), 430)
    
    def test_verificar_qtd_apos_desdobramento_fii_2(self):
        """Testa se a quantidade de cotas do usuário está correta após o desdobramento do FII 2"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), 'BBPO11'), 43)
            
    def test_verificar_qtd_apos_incorporacao(self):
        """Testa se a quantidade de cotas do usuário está correta após o desdobramento e incorporação do FII 3"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), 'BCPO11'), 0)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), 'BDPO11'), 617)

    def test_verificar_qtd_divisao_antes_eventos(self):
        """Testa se a quantidade de cotas por divisão está correta antes dos eventos"""
        investidor = Investidor.objects.get(user__username='test')
        self.assertDictEqual(calcular_qtd_fiis_ate_dia_por_divisao(datetime.date(2017, 5, 12), self.divisao_geral.id), 
                             {'BAPO11': 43, 'BBPO11': 430, 'BCPO11': 37, 'BDPO11': 271, 'BFPO11': 20})
        self.assertDictEqual(calcular_qtd_fiis_ate_dia_por_divisao(datetime.date(2017, 5, 12), self.divisao_teste.id), 
                             {'BEPO11': 50})
        
    def test_verificar_qtd_divisao_apos_eventos(self):
        """Testa se a quantidade de cotas por divisão está correta após os eventos"""
        self.assertDictEqual(calcular_qtd_fiis_ate_dia_por_divisao(datetime.date(2017, 11, 13), self.divisao_geral.id), 
                             {'BAPO11': 430, 'BBPO11': 43, 'BDPO11': 707})
        self.assertDictEqual(calcular_qtd_fiis_ate_dia_por_divisao(datetime.date(2017, 11, 13), self.divisao_teste.id), 
                             {'BEPO11': 500})
        
    def test_verificar_checkpoints_apagados(self):
        """Testa se checkpoints são apagados caso quantidades de FII do usuário se torne zero"""
        self.assertTrue(len(CheckpointFII.objects.filter(investidor=self.investidor)) > 0)
        for operacao in OperacaoFII.objects.filter(investidor=self.investidor):
            operacao.delete()
        self.assertFalse(CheckpointFII.objects.filter(investidor=self.investidor).exists())
        
    def test_verificar_poupanca_proventos(self):
        """Testa se poupança de proventos está com valores corretos"""
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia(self.investidor, datetime.date(2017, 3, 1)), 0)
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia(self.investidor, datetime.date(2017, 10, 1)), Decimal('4755.80'))
        self.assertEqual(CheckpointProventosFII.objects.get(investidor=self.investidor, ano=2017).valor, Decimal('4755.80'))
        
        # Testar situação alterando uma operação
        operacao = OperacaoFII.objects.get(fii__ticker='BAPO11')
        operacao.quantidade = 45
        operacao.save()
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia(self.investidor, datetime.date(2017, 10, 1)), Decimal('4957.40'))
        self.assertEqual(CheckpointProventosFII.objects.get(investidor=self.investidor, ano=2017).valor, Decimal('4957.40'))
        calcular_poupanca_prov_fii_ate_dia(self.investidor, datetime.date(2018, 8, 12))
        
    def test_verificar_poupanca_proventos_por_divisao(self):
        """Testa se poupança de proventos está com os valores corretos para cada divisão"""
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1)), 0)
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia_por_divisao(self.divisao_teste, datetime.date(2017, 3, 1)), 0)
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia_por_divisao(self.divisao_geral, datetime.date(2017, 10, 1)), Decimal('4755.80'))
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia_por_divisao(self.divisao_teste, datetime.date(2017, 10, 1)), 0)
        self.assertEqual(CheckpointDivisaoProventosFII.objects.get(divisao=self.divisao_geral, ano=2017).valor, Decimal('4755.80'))
        self.assertFalse(CheckpointDivisaoProventosFII.objects.filter(divisao=self.divisao_teste, ano=2017).exists())
        
        # Testar situação alterando uma operação
        operacao = OperacaoFII.objects.get(fii__ticker='BAPO11')
        operacao.quantidade = 45
        operacao.save()
        # Alterar divisao operação
        divisao_operacao = DivisaoOperacaoFII.objects.get(operacao=operacao)
        divisao_operacao.quantidade = 45
        divisao_operacao.save()
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia_por_divisao(self.divisao_geral, datetime.date(2017, 10, 1)), Decimal('4957.40'))
        self.assertEqual(calcular_poupanca_prov_fii_ate_dia_por_divisao(self.divisao_teste, datetime.date(2017, 10, 1)), 0)
        self.assertEqual(CheckpointDivisaoProventosFII.objects.get(divisao=self.divisao_geral, ano=2017).valor, Decimal('4957.40'))
        
    def test_verificar_preco_medio(self):
        """Testa cálculos de preço médio"""
        # Testar funções individuais
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 3, 1), 'BAPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BAPO11'), Decimal(4500) / 43, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), 'BAPO11'), Decimal(4500) / 430, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 11, 20), 'BAPO11'), Decimal(4500) / 430 - Decimal('9.1'), places=3)
        
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 3, 1), 'BBPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BBPO11'), Decimal(43200) / 430, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), 'BBPO11'), Decimal(43200) / 43, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 11, 20), 'BBPO11'), Decimal(43200) / 43, places=3)
        
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 3, 1), 'BCPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BCPO11'), Decimal(3900) / 37, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), 'BCPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 11, 20), 'BCPO11'), 0, places=3)
        
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 3, 1), 'BDPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 5, 12), 'BDPO11'), Decimal(27300) / 271, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 6, 4), 'BDPO11'), Decimal(27300 + 3900) / 617, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 11, 20), 'BDPO11'), Decimal(27300 + 3900 + 9400) / 707, places=3)
        
        # Testar função geral
        for data in [datetime.date(2017, 3, 1), datetime.date(2017, 5, 12), datetime.date(2017, 6, 4), datetime.date(2017, 11, 20)]:
            precos_medios = calcular_preco_medio_fiis_ate_dia(self.investidor, data)
            for ticker in FII.objects.all().values_list('ticker', flat=True):
                qtd_individual = calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, data, ticker)
                if qtd_individual > 0:
                    self.assertAlmostEqual(precos_medios[ticker], qtd_individual, places=3)
                else:
                    self.assertNotIn(ticker, precos_medios.keys())
        
        # Testar checkpoints
        self.assertFalse(CheckpointFII.objects.filter(investidor=self.investidor, ano=2016).exists())
        for fii in FII.objects.all().exclude(ticker__in=['BCPO11', 'BFPO11']):
            self.assertAlmostEqual(CheckpointFII.objects.get(investidor=self.investidor, ano=2017, fii=fii).preco_medio, 
                                   calcular_preco_medio_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2017, 12, 31), fii.ticker), places=3)
        # Garantir que o checkpoint do BCPO11 e BFPO11 não foi criado pois não há um ano anterior com quantidade diferente de 0, e
        #a quantidade atual é 0
        self.assertFalse(CheckpointFII.objects.filter(investidor=self.investidor, ano=2017, fii=self.fii_3).exists())
        self.assertFalse(CheckpointFII.objects.filter(investidor=self.investidor, ano=2017, fii=self.fii_6).exists())
            
    def test_verificar_preco_medio_por_divisao(self):
        """Testa cálculos de preço médio por divisão"""
        # Testar funções individuais
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1), 'BAPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 5, 12), 'BAPO11'), Decimal(4500) / 43, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 6, 4), 'BAPO11'), Decimal(4500) / 430, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 11, 20), 'BAPO11'), Decimal(4500) / 430 - Decimal('9.1'), places=3)
        
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1), 'BBPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 5, 12), 'BBPO11'), Decimal(43200) / 430, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 6, 4), 'BBPO11'), Decimal(43200) / 43, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 11, 20), 'BBPO11'), Decimal(43200) / 43, places=3)
        
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1), 'BCPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 5, 12), 'BCPO11'), Decimal(3900) / 37, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 6, 4), 'BCPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 11, 20), 'BCPO11'), 0, places=3)
        
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 3, 1), 'BDPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 5, 12), 'BDPO11'), Decimal(27300) / 271, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 6, 4), 'BDPO11'), Decimal(27300 + 3900) / 617, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 11, 20), 'BDPO11'), Decimal(27300 + 3900 + 9400) / 707, places=3)
        
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_teste, datetime.date(2017, 3, 1), 'BEPO11'), 0, places=3)
        self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_teste, datetime.date(2017, 5, 12), 'BEPO11'), Decimal(5200) / 50, places=3)
        
        # Testar função geral
        for data in [datetime.date(2017, 3, 1), datetime.date(2017, 5, 12), datetime.date(2017, 6, 4), datetime.date(2017, 11, 20)]:
            precos_medios = calcular_preco_medio_fiis_ate_dia_por_divisao(self.divisao_geral, data)
            for ticker in FII.objects.all().values_list('ticker', flat=True):
                qtd_individual = calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, data, ticker)
                if qtd_individual > 0:
                    self.assertAlmostEqual(precos_medios[ticker], qtd_individual, places=3)
                else:
                    self.assertNotIn(ticker, precos_medios.keys())
        
        # Testar checkpoints
        self.assertFalse(CheckpointDivisaoFII.objects.filter(divisao=self.divisao_geral, ano=2016).exists())
        for fii in FII.objects.all().exclude(ticker__in=['BCPO11', 'BEPO11', 'BFPO11']):
            self.assertAlmostEqual(CheckpointDivisaoFII.objects.get(divisao=self.divisao_geral, ano=2017, fii=fii).preco_medio, 
                                   calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_geral, datetime.date(2017, 12, 31), fii.ticker), places=3)
        # Garantir que o checkpoint do BCPO11 e BFPO11 não foi criado pois não há um ano anterior com quantidade diferente de 0, e
        #a quantidade atual é 0
        self.assertFalse(CheckpointDivisaoFII.objects.filter(divisao=self.divisao_geral, ano=2017, fii=self.fii_3).exists())
        self.assertFalse(CheckpointDivisaoFII.objects.filter(divisao=self.divisao_geral, ano=2017, fii=self.fii_6).exists())
        self.assertAlmostEqual(CheckpointDivisaoFII.objects.get(divisao=self.divisao_teste, ano=2017, fii=self.fii_5).preco_medio, 
                               calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(self.divisao_teste, datetime.date(2017, 12, 31), 'BEPO11'), places=3)
            
# class PerformanceCheckpointFIITestCase(TestCase):
#     def setUp(self):
#         user = User.objects.create(username='test', password='test')
#          
#         empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
#         fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
#         empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='FII BB')
#         fii_2 = FII.objects.create(ticker='BBPO11', empresa=empresa_2)
#         empresa_3 = Empresa.objects.create(nome='BC', nome_pregao='FII BC')
#         fii_3 = FII.objects.create(ticker='BCPO11', empresa=empresa_3)
#         empresa_4 = Empresa.objects.create(nome='BD', nome_pregao='FII BD')
#         fii_4 = FII.objects.create(ticker='BDPO11', empresa=empresa_4)
#          
#         # Gerar operações mensalmente de 2012 a 2016
#         for ano in range(2012, 2018):
#             for mes in range(1, 13):
#                 # Desdobramento
#                 OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
#                 # Agrupamento
#                 OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
#                 # Desdobramento + Incorporação
#                 OperacaoFII.objects.create(fii=fii_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
#                 OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
#          
#         EventoDesdobramentoFII.objects.create(fii=fii_4, data=datetime.date(2016, 6, 3), proporcao=Decimal('0.933'))
#          
#         EventoDesdobramentoFII.objects.create(fii=fii_1, data=datetime.date(2017, 6, 3), proporcao=10)
#         EventoAgrupamentoFII.objects.create(fii=fii_2, data=datetime.date(2017, 6, 3), proporcao=Decimal('0.1'))
#         EventoDesdobramentoFII.objects.create(fii=fii_3, data=datetime.date(2017, 6, 3), proporcao=10)
#         EventoIncorporacaoFII.objects.create(fii=fii_3, data=datetime.date(2017, 6, 3), novo_fii=fii_4)
#          
#     def calculo_forma_antiga(self, investidor, dia):
#         if not all([verificar_se_existe_evento_para_fii(fii_ticker, dia) for fii_ticker in OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
#                                                                                                 .order_by('fii__id').distinct('fii__id').values_list('fii__ticker', flat=True)]):
#             qtd_fii = dict(OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).annotate(ticker=F('fii__ticker')).values('ticker') \
#                 .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
#                                     When(tipo_operacao='V', then=F('quantidade')*-1),
#                                     output_field=DecimalField()))).values_list('ticker', 'total').exclude(total=0))
#      
#         else:
#             qtd_fii = {}
#             for fii in FII.objects.filter(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
#                                                                                                 .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)):
#                 qtd_fii_na_data = self.calculo_forma_antiga_por_ticker(investidor, dia, fii.ticker)
#                 if qtd_fii_na_data > 0:
#                     qtd_fii[fii.ticker] = qtd_fii_na_data
#         return qtd_fii
#      
#     def calculo_forma_antiga_por_ticker(self, investidor, dia, ticker, ignorar_incorporacao_id=None):
#         if not verificar_se_existe_evento_para_fii(ticker, dia):
#             qtd_fii = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True) \
#                 .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
#                                           When(tipo_operacao='V', then=F('quantidade')*-1),
#                                           output_field=DecimalField())))['total'] or 0
#         else:
#             qtd_fii = 0
#          
#             operacoes = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True) \
#                 .annotate(qtd_final=(Case(When(tipo_operacao='C', then=F('quantidade')),
#                                           When(tipo_operacao='V', then=F('quantidade')*-1),
#                                           output_field=DecimalField()))).annotate(tipo=Value(u'Operação', output_field=CharField()))
#                                        
#                                        
#             # Verificar agrupamentos e desdobramentos
#             agrupamentos = EventoAgrupamentoFII.objects.filter(fii__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))
#  
#             desdobramentos = EventoDesdobramentoFII.objects.filter(fii__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
#          
#             incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__ticker=ticker, data__lte=dia) | Q(novo_fii__ticker=ticker, data__lte=dia)).exclude(id=ignorar_incorporacao_id) \
#                 .annotate(tipo=Value(u'Incorporação', output_field=CharField()))
#          
#             lista_conjunta = sorted(chain(agrupamentos, desdobramentos, incorporacoes, operacoes), key=attrgetter('data'))
#          
#             for elemento in lista_conjunta:
#                 if elemento.tipo == 'Operação':
#                     qtd_fii += elemento.qtd_final
#                 elif elemento.tipo == 'Agrupamento':
#                     qtd_fii = elemento.qtd_apos(qtd_fii)
#                 elif elemento.tipo == 'Desdobramento':
#                     qtd_fii = elemento.qtd_apos(qtd_fii)
#                 elif elemento.tipo == 'Incorporação':
#                     if elemento.fii.ticker == ticker:
#                         qtd_fii = 0
#                     elif elemento.novo_fii.ticker == ticker:
#                         qtd_fii += self.calculo_forma_antiga_por_ticker(investidor, elemento.data, elemento.fii.ticker, elemento.id)
#          
#         return qtd_fii
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
#         qtd_novo = calcular_qtd_fiis_ate_dia(investidor, data_final)
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
        
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
        fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
        empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='FII BB')
        fii_2 = FII.objects.create(ticker='BBPO11', empresa=empresa_1)
        OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 1, 10), quantidade=24, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 3, 13), quantidade=13, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        
        
        OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 9, 1), quantidade=45, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 8, 15), quantidade=82, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 10, 20), quantidade=102, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 10, 31), quantidade=42, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        
        EventoIncorporacaoFII.objects.create(fii=fii_1, data=datetime.date(2017, 5, 17), novo_fii=fii_2)
        EventoDesdobramentoFII.objects.create(fii=fii_2, data=datetime.date(2017, 5, 17), proporcao=Decimal('10'))
        EventoDesdobramentoFII.objects.create(fii=fii_1, data=datetime.date(2017, 5, 17), proporcao=Decimal('9.3674360842'))
        
    def test_qtd(self):
        """Testa se algoritmo calculou quantidade atual corretamente"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(self.investidor, datetime.date(2018, 2, 13), 'BBPO11'), 617)

class AtualizarCheckpointAnualTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
        user.investidor.data_ultimo_acesso = datetime.date(2016, 5, 11)
        user.investidor.save()
        
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
        fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
        
        OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2016, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        # Gera operação no futuro para depois trazer para ano atual
        OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(datetime.date.today().year+1, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        # Apagar checkpoint gerado
        CheckpointFII.objects.filter(ano__gt=datetime.date.today().year).delete()
         
    def test_atualizacao_ao_logar_prox_ano(self):
        """Verifica se é feita atualização ao logar em pŕoximo ano"""
        investidor = Investidor.objects.get(user__username='test')
        fii = FII.objects.get(ticker='BAPO11')
        
        # Verifica que existe checkpoint até ano atual
        ano_atual = datetime.date.today().year
        self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).exists())
        
        # Apaga ano atual
        CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).delete()
        self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).exists())
        
        # Chamar o teste do middleware de ultimo acesso
        if investidor.data_ultimo_acesso.year < ano_atual:
            atualizar_checkpoints(investidor)

        # Verifica se ao logar foi gerado novamente checkpoint
        self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).exists())
        
    def test_atualizacao_ao_logar_apos_varios_anos(self):
        """Verifica se é feita atualização ao logar depois de vários anos"""
        investidor = Investidor.objects.get(user__username='test')
        fii = FII.objects.get(ticker='BAPO11')
        
        # Verifica que existe checkpoint até ano atual
        ano_atual = datetime.date.today().year
        self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).exists())
        
        # Apaga ano atual e ano passado
        CheckpointFII.objects.filter(investidor=investidor, ano__gte=ano_atual-1, fii=fii).delete()
        self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).exists())
        self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual-1, fii=fii).exists())
        
        # Chamar o teste do middleware de ultimo acesso
        if investidor.data_ultimo_acesso.year < ano_atual:
            atualizar_checkpoints(investidor)

        # Verifica se ao logar foi gerado novamente checkpoint
        self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).exists())
        self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual-1, fii=fii).exists())
        
    def test_nao_atualizar_caso_mesmo_ano(self):
        """Verificar se em caso de já haver checkpoint no ano, função não altera nada"""
        investidor = Investidor.objects.get(user__username='test')
        fii = FII.objects.get(ticker='BAPO11')
        checkpoint = CheckpointFII.objects.get(investidor=investidor, ano=datetime.date.today().year, fii=fii)
        
        # Chamar atualizar ano
        atualizar_checkpoints(investidor)
        
        # Verificar se houve alteração no checkpoint
        self.assertEqual(checkpoint, CheckpointFII.objects.get(investidor=investidor, ano=datetime.date.today().year, fii=fii))
        
    def test_verificar_checkpoint_operacao_ano_futuro(self):
        """Verificar se checkpoint de operação no futuro funciona ao chegar no ano da operação"""
        investidor = Investidor.objects.get(user__username='test')
        fii = FII.objects.get(ticker='BAPO11')
        
        # Apagar ano atual para fingir que acabamos de chegar a esse ano
        ano_atual = datetime.date.today().year
        self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).exists())
        CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).delete()
        self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, fii=fii).exists())
        
        # Trazer operação do futuro para ano atual
        OperacaoFII.objects.filter(investidor=investidor, data__gt=datetime.date.today()).update(data=datetime.date.today())
        
        # Atualizar da forma como é feito pelo middleware de ultimo acesso
        if investidor.data_ultimo_acesso.year < ano_atual:
            atualizar_checkpoints(investidor)
            
        # Verificar se quantidade de cotas está correta
        self.assertEqual(CheckpointFII.objects.get(investidor=investidor, ano=ano_atual, fii=fii).quantidade, 86)
        
    def test_checkpoints_venda_cotas(self):
        """Verificar se checkpoints são apagados quando cota é vendida"""
        investidor = Investidor.objects.get(user__username='test')
        fii = FII.objects.get(ticker='BAPO11')
        
        ano_atual = datetime.date.today().year
        OperacaoFII.objects.create(fii=fii, investidor=investidor, tipo_operacao='V', data=datetime.date(2016, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
        self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, fii=fii).exists())
