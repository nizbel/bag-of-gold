# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.outros_investimentos.models import Investimento, \
    Rendimento, ImpostoRendaRendimento
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class ImpostoRendaSobreRendimentosTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        investimento_1 = Investimento.objects.create(nome='Investimento 1', descricao='', quantidade=Decimal(1000), investidor=user.investidor,
                                                     data=datetime.date(2017, 3, 1))
        
        rendimento_1 = Rendimento.objects.create(investimento=investimento_1, valor=Decimal('40.69'), data=datetime.date(2018, 3, 10))
        # Imposto longo prazo
        ImpostoRendaRendimento.objects.create(rendimento=rendimento_1, tipo='L')
        
    def test_imposto_longo_prazo(self):
        """Testa valor do imposto do tipo longo prazo"""
        investidor = Investidor.objects.get(user__username='tester')
        
        rendimento = Rendimento.objects.get(investimento__investidor=investidor, valor=Decimal('40.69'))
        self.assertAlmostEqual(rendimento.valor_liquido(), Decimal('33.57'), delta=Decimal('0.01'))
