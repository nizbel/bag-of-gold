# -*- coding: utf-8 -*-
from bagogold.outros_investimentos.models import Investimento, Amortizacao
from bagogold.outros_investimentos.utils import \
    calcular_valor_outros_investimentos_ate_data
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
        
    def test_quantidades_ate_dia(self):
        """Testa quantidades de investimentos até dias determinados"""
        investidor = User.objects.get(username='tester').investidor
        qtd_apos_investimento_1 = calcular_valor_outros_investimentos_ate_data(investidor, datetime.date(2017, 3, 2))
        self.assertDictEqual(qtd_apos_investimento_1, {1: Decimal(1000)})
        
        qtd_apos_investimento_2 = calcular_valor_outros_investimentos_ate_data(investidor, datetime.date(2017, 4, 2))
        self.assertDictEqual(qtd_apos_investimento_2, {1: Decimal(1000), 2: Decimal(2000)})
        
        qtd_apos_amortizacao_1 = calcular_valor_outros_investimentos_ate_data(investidor, datetime.date(2017, 5, 2))
        self.assertDictEqual(qtd_apos_amortizacao_1, {1: Decimal('666.67'), 2: Decimal(2000)})