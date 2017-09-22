# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoInvestimento, Divisao
from bagogold.outros_investimentos.models import Investimento, Amortizacao
from bagogold.outros_investimentos.utils import \
    calcular_valor_outros_investimentos_ate_data, \
    calcular_valor_outros_investimentos_ate_data_por_investimento, \
    calcular_valor_outros_investimentos_ate_data_por_divisao
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
        
        investimento_3 = Investimento.objects.create(nome='Investimento 3', descricao='', quantidade=Decimal(3000), investidor=user.investidor,
                                                     data=datetime.date(2017, 7, 1))
        
        amortizacao_4 = Amortizacao.objects.create(investimento=investimento_3, data=datetime.date(2017, 7, 20), valor=Decimal(2000))
        
        divisao_1 = Divisao.objects.create(nome='Divisão 1', investidor=user.investidor)
        
        divisao_2 = Divisao.objects.create(nome='Divisão 2', investidor=user.investidor)
        
        divisao_investimento_1 = DivisaoInvestimento.objects.create(divisao=divisao_1, investimento=investimento_1, quantidade=Decimal(1000))
        
        divisao_investimento_2 = DivisaoInvestimento.objects.create(divisao=divisao_1, investimento=investimento_2, quantidade=Decimal(1500))
        
        divisao_investimento_3 = DivisaoInvestimento.objects.create(divisao=divisao_2, investimento=investimento_3, quantidade=Decimal(2000))
        
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
        
    def test_quantidade_ate_dia_para_um_investimento(self):
        """Testa quantidade investida em investimento determinado até dia"""
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
        
    def test_quantidade_ate_dia_para_uma_divisao(self):
        """Testa quantidades investidas para uma divisão determinada até dia"""
        investidor = User.objects.get(username='tester').investidor
        investimento_1 = Investimento.objects.get(nome='Investimento 1')
        investimento_2 = Investimento.objects.get(nome='Investimento 2')
        investimento_3 = Investimento.objects.get(nome='Investimento 3')
        divisao_1 = Divisao.objects.get(nome='Divisão 1')
        qtd_apos_investimento_1 = calcular_valor_outros_investimentos_ate_data_por_divisao(divisao_1, datetime.date(2017, 3, 2))
        self.assertDictEqual(qtd_apos_investimento_1, {investimento_1.id: Decimal(1000)})
        
        qtd_apos_investimento_2 = calcular_valor_outros_investimentos_ate_data_por_divisao(divisao_1, datetime.date(2017, 4, 2))
        self.assertDictEqual(qtd_apos_investimento_2, {investimento_1.id: Decimal(1000), investimento_2.id: Decimal(1500)})
        
        qtd_apos_amortizacao_1 = calcular_valor_outros_investimentos_ate_data_por_divisao(divisao_1, datetime.date(2017, 5, 2))
        self.assertDictEqual(qtd_apos_amortizacao_1, {investimento_1.id: Decimal('666.67'), investimento_2.id: Decimal(1500)})
        
        qtd_apos_amortizacao_2 = calcular_valor_outros_investimentos_ate_data_por_divisao(divisao_1, datetime.date(2017, 5, 21))
        self.assertDictEqual(qtd_apos_amortizacao_2, {investimento_1.id: Decimal('333.34'), investimento_2.id: Decimal(1500)})
        
        qtd_apos_amortizacao_3 = calcular_valor_outros_investimentos_ate_data_por_divisao(divisao_1, datetime.date(2017, 6, 21))
        self.assertDictEqual(qtd_apos_amortizacao_3, {investimento_1.id: Decimal('333.34')})
        
        divisao_2 = Divisao.objects.get(nome='Divisão 2')
        qtd_apos_investimento_3 = calcular_valor_outros_investimentos_ate_data_por_divisao(divisao_2, datetime.date(2017, 7, 2))
        self.assertDictEqual(qtd_apos_investimento_3, {investimento_3.id: Decimal(2000)})
        
        qtd_apos_amortizacao_4 = calcular_valor_outros_investimentos_ate_data_por_divisao(divisao_2, datetime.date(2017, 7, 21))
        self.assertDictEqual(qtd_apos_amortizacao_4, {investimento_3.id: (Decimal(2000)/3).quantize(Decimal('0.01'))})