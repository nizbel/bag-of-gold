# -*- coding: utf-8 -*-
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class QuantidadesCriptomoedaTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        bitcoin = Criptomoeda.objects.create(nome='Bitcoin', ticker='BTC')
        
        ethereum = Criptomoeda.objects.create(nome='Ethereum', ticker='ETH')
        
        operacao_1 = OperacaoCriptomoeda.objects.create(criptomoeda=bitcoin, quantidade=Decimal('0.48784399'), valor=Decimal(), taxa=(Decimal('102.39') + Decimal('')), investidor=user.investidor,
                                                              tipo_operacao='C', data=datetime.date(2017, 6, 6))
        operacao_2 = OperacaoCriptomoeda.objects.create(criptomoeda=ethereum, quantidade=Decimal('600.56'), valor=Decimal(7000), investidor=user.investidor,
                                                              tipo_operacao='C', data=datetime.date(2016, 12, 6))
        operacao_3 = OperacaoCriptomoeda.objects.create(criptomoeda=ethereum, quantidade=Decimal('420.9056'), valor=Decimal(5000), investidor=user.investidor,
                                                              tipo_operacao='V', data=datetime.date(2017, 1, 5))
        
    def test_qtd_moedas_ate_dia(self):
        #[u'ETH: 0.862703100000', u'FCT: 9.567610470000', u'LSK: 84.510046700000', u'BTC: 0.186517598234185500000000']
        """Testa quantidade de cotas até dia"""
        investidor = User.objects.get(username='tester').investidor
        qtd_cotas = calcular_qtd_cotas_ate_dia(investidor, datetime.date(2017, 6, 14))
        id_fundo_1 = FundoInvestimento.objects.get(cnpj='00.000.000/0000-01').id
        id_fundo_2 = FundoInvestimento.objects.get(cnpj='00.000.000/0000-02').id
        self.assertDictEqual(qtd_cotas, {id_fundo_1: Decimal('4291.07590514'), id_fundo_2: Decimal('179.6544')})
        
    def test_qtd_cotas_ate_dia_por_fundo(self):
        """Testa quantidade de cotas até dia por fundo"""
        investidor = User.objects.get(username='tester').investidor
        qtd_cotas = calcular_qtd_cotas_ate_dia_por_fundo(investidor, FundoInvestimento.objects.get(cnpj='00.000.000/0000-01').id, datetime.date(2017, 6, 14))
        self.assertEqual(qtd_cotas, Decimal('4291.07590514'))
        qtd_cotas = calcular_qtd_cotas_ate_dia_por_fundo(investidor, FundoInvestimento.objects.get(cnpj='00.000.000/0000-02').id, datetime.date(2017, 6, 14))
        self.assertEqual(qtd_cotas, Decimal('179.6544'))
        
    def test_valor_cotas_ate_dia(self):
        """Testa valor das cotas até dia"""
        investidor = User.objects.get(username='tester').investidor
        valor_fundos = calcular_valor_fundos_investimento_ate_dia(investidor, datetime.date(2017, 6, 14))
        self.assertEqual(valor_fundos[FundoInvestimento.objects.get(cnpj='00.000.000/0000-01').id].quantize(Decimal('0.01')), Decimal('10589.63'))