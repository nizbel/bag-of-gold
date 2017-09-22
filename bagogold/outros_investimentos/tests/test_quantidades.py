# -*- coding: utf-8 -*-
from bagogold.outros_investimentos.models import Investimento, Amortizacao
from bagogold.outros_investimentos.utils import \
    calcular_valor_outros_investimentos_ate_data, \
    calcular_valor_outros_investimentos_ate_data_por_investimento
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class QuantidadesOutrosInvestimentosTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        investimento_1 = Investimento.objects.create(nome='Investimento 1', descricao='', quantidade=Decimal(1000), investidor=user.investidor,
                                                     data=datetime.date(2017, 3, 1))
        
        investimento_2 = Investimento.objects.create(nome='Investimento 2', descricao='', quantidade=Decimal(2000), investidor=user.investidor,
                                                     data=datetime.date(2017, 4, 1))

        amortizacao_1 = Amortizacao.objects.create(investimento=investimento_1, data=datetime.date(2017, 4, 20), valor=Decimal('333.33'))
        
        amortizacao_2 = Amortizacao.objects.create(investimento=investimento_1, data=datetime.date(2017, 5, 20), valor=Decimal('333.33'))
        
        amortizacao_3 = Amortizacao.objects.create(investimento=investimento_2, data=datetime.date(2017, 6, 20), valor=Decimal(2000))
        
    def test_quantidades_ate_dia(self):
        """Testa quantidades de investimentos até dias determinados"""
        investidor = User.objects.get(username='tester').investidor
        investimento_1 = Investimento.objects.get(nome='Investimento 1')
        investimento_2 = Investimento.objects.get(nome='Investimento 2')
        
        qtd_apos_investimento_1 = calcular_valor_outros_investimentos_ate_data(investidor, datetime.date(2017, 3, 2))
        self.assertDictEqual(qtd_apos_investimento_1, {investimento_1.id: Decimal(1000)})
        
        qtd_apos_investimento_2 = calcular_valor_outros_investimentos_ate_data(investidor, datetime.date(2017, 4, 2))
        self.assertDictEqual(qtd_apos_investimento_2, {investimento_1.id: Decimal(1000), investimento_2.id: Decimal(2000)})
        
        qtd_apos_amortizacao_1 = calcular_valor_outros_investimentos_ate_data(investidor, datetime.date(2017, 5, 2))
        self.assertDictEqual(qtd_apos_amortizacao_1, {investimento_1.id: Decimal('666.67'), investimento_2.id: Decimal(2000)})
        
        qtd_apos_amortizacao_2 = calcular_valor_outros_investimentos_ate_data(investidor, datetime.date(2017, 5, 21))
        self.assertDictEqual(qtd_apos_amortizacao_2, {investimento_1.id: Decimal('333.34'), investimento_2.id: Decimal(2000)})
        
        qtd_apos_amortizacao_3 = calcular_valor_outros_investimentos_ate_data(investidor, datetime.date(2017, 6, 21))
        self.assertDictEqual(qtd_apos_amortizacao_3, {investimento_1.id: Decimal('333.34')})
        
    def test_quantidade_ate_dia_por_investimento(self):
        """Testa quantidades investida em investimento determinado até dia"""
        investidor = User.objects.get(username='tester').investidor
        investimento_1 = Investimento.objects.get(nome='Investimento 1')
        qtd_antes_amortizacao_1 = calcular_valor_outros_investimentos_ate_data_por_investimento(investimento_1, datetime.date(2017, 3, 20))
        self.assertEqual(qtd_antes_amortizacao_1, Decimal(1000))
        
        qtd_apos_amortizacao_1 = calcular_valor_outros_investimentos_ate_data_por_investimento(investimento_1, datetime.date(2017, 4, 21))
        self.assertEqual(qtd_apos_amortizacao_1, Decimal('666.67'))
        
        qtd_apos_amortizacao_2 = calcular_valor_outros_investimentos_ate_data_por_investimento(investimento_1, datetime.date(2017, 5, 21))
        self.assertEqual(qtd_apos_amortizacao_2, Decimal('333.34'))
        
        investimento_2 = Investimento.objects.get(nome='Investimento 2')
        qtd_antes_amortizacao_3 = calcular_valor_outros_investimentos_ate_data_por_investimento(investimento_2, datetime.date(2017, 4, 2))
        self.assertEqual(qtd_antes_amortizacao_3, Decimal(2000))
        
        qtd_apos_amortizacao_3 = calcular_valor_outros_investimentos_ate_data_por_investimento(investimento_2, datetime.date(2017, 6, 21))
        self.assertEqual(qtd_apos_amortizacao_3, 0)