# -*- coding: utf-8 -*-
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import FII, OperacaoFII, \
    EventoDesdobramentoFII, EventoAgrupamentoFII, EventoIncorporacaoFII
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia, \
    calcular_qtd_fiis_ate_dia_por_ticker
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class CalcularQuantidadesFIITestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
        
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
        fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
        empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='FII BB')
        fii_2 = FII.objects.create(ticker='BBPO11', empresa=empresa_2)
        empresa_3 = Empresa.objects.create(nome='BC', nome_pregao='FII BC')
        fii_3 = FII.objects.create(ticker='BCPO11', empresa=empresa_3)
        empresa_4 = Empresa.objects.create(nome='BD', nome_pregao='FII BD')
        fii_4 = FII.objects.create(ticker='BDPO11', empresa=empresa_4)
        
        # Desdobramento
        OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=43, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        # Agrupamento
        OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=430, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        # Desdobramento + Incorporação
        OperacaoFII.objects.create(fii=fii_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=37, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=271, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        
        OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 11, 11), quantidade=40, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 11, 12), quantidade=50, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        
        
        EventoDesdobramentoFII.objects.create(fii=fii_1, data=datetime.date(2017, 6, 3), proporcao=10)
        EventoAgrupamentoFII.objects.create(fii=fii_2, data=datetime.date(2017, 6, 3), proporcao=Decimal('0.1'))
        EventoDesdobramentoFII.objects.create(fii=fii_3, data=datetime.date(2017, 6, 3), proporcao=Decimal('9.3674360842'))
        EventoIncorporacaoFII.objects.create(fii=fii_3, data=datetime.date(2017, 6, 3), novo_fii=fii_4)
        
    def test_calculo_qtd_fii_por_ticker(self):
        """Calcula quantidade de FIIs do usuário individualmente"""
        investidor = Investidor.objects.get(user__username='test')
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BAPO11'), 43)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BBPO11'), 430)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BCPO11'), 37)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BDPO11'), 271)
        
    def test_calculo_qtd_fiis(self):
       """Calcula quantidade de FIIs do usuário"""
       self.assertDictEqual(calcular_qtd_fiis_ate_dia(Investidor.objects.get(user__username='test'), datetime.date(2017, 5, 12)), 
                            {'BAPO11': 43, 'BBPO11': 430, 'BCPO11': 37, 'BDPO11': 271}) 
       calcular_qtd_fiis_ate_dia(Investidor.objects.get(user__username='test'), datetime.date(2017, 11, 13))
    
    def test_calculo_qtd_apos_agrupamento(self):
        """Verifica se a função que recebe uma quantidade calcula o resultado correto para agrupamento"""
        self.assertEqual(EventoAgrupamentoFII.objects.get(fii=FII.objects.get(ticker='BBPO11')).qtd_apos(100), 10)
        
    def test_calculo_qtd_apos_desdobramento(self):    
        """Verifica se a função que recebe uma quantidade calcula o resultado correto para agrupamento"""
        self.assertEqual(EventoDesdobramentoFII.objects.get(fii=FII.objects.get(ticker='BAPO11')).qtd_apos(100), 1000)
    
    def test_verificar_qtd_apos_agrupamento_fii_1(self):
        """Testa se a quantidade de cotas do usuário está correta após o agrupamento do FII 1"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(Investidor.objects.get(user__username='test'), datetime.date(2017, 6, 4), 'BAPO11'), 430)
    
    def test_verificar_qtd_apos_desdobramento_fii_2(self):
        """Testa se a quantidade de cotas do usuário está correta após o desdobramento do FII 2"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(Investidor.objects.get(user__username='test'), datetime.date(2017, 6, 4), 'BBPO11'), 43)
            
    def test_verificar_qtd_apos_incorporacao(self):
        """Testa se a quantidade de cotas do usuário está correta após o desdobramento e incorporação do FII 3"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(Investidor.objects.get(user__username='test'), datetime.date(2017, 6, 4), 'BCPO11'), 0)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(Investidor.objects.get(user__username='test'), datetime.date(2017, 6, 4), 'BDPO11'), 617)

