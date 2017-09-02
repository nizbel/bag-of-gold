# -*- coding: utf-8 -*-
from bagogold.criptomoeda.models import TransferenciaCriptomoeda, Criptomoeda, \
    OperacaoCriptomoeda, OperacaoCriptomoedaMoeda, OperacaoCriptomoedaTaxa
from bagogold.criptomoeda.utils import calcular_qtd_moedas_ate_dia
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class QuantidadesCriptomoedaTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        bitcoin = Criptomoeda.objects.create(nome='Bitcoin', ticker='BTC')
        
        ethereum = Criptomoeda.objects.create(nome='Ethereum', ticker='ETH')
        
        lisk = Criptomoeda.objects.create(nome='Lisk', ticker='LSK')
        
        factom = Criptomoeda.objects.create(nome='Factom', ticker='FCT')
        
        # Até dia 10 de Junho as operações serão:
        # Transferir dinheiro para casa de câmbio, comprar bitcoins, transferir bitcoins, vender e comprar outras criptomoedas
        transferencia_1 = TransferenciaCriptomoeda.objects.create(moeda=None, investidor=user.investidor, data=datetime.date(2017, 6, 6), quantidade=Decimal('4999.99'), 
                                                                  taxa=Decimal('102.39'), origem='Conta', destino='Mercado Bitcoin')
        transferencia_2 = TransferenciaCriptomoeda.objects.create(moeda=bitcoin, data=datetime.date(2017, 6, 6), quantidade=Decimal('0.2'), investidor=user.investidor, 
                                                                  origem='Mercado Bitcoin', destino='Poloniex', taxa=Decimal('0.0006102'))
        transferencia_3 = TransferenciaCriptomoeda.objects.create(moeda=bitcoin, data=datetime.date(2017, 6, 9), quantidade=Decimal('0.19'), investidor=user.investidor, 
                                                                  origem='Mercado Bitcoin', destino='Poloniex', taxa=Decimal('0.0006102'))
        
        
        
        compra_1 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.48784399'), valor=Decimal('9968.99994'), data=datetime.date(2017, 6, 6), tipo_operacao='C', criptomoeda=bitcoin, investidor=user.investidor)
        compra_2 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('2.04838866'), valor=Decimal('0.0110499'), data=datetime.date(2017, 6, 7), tipo_operacao='C', criptomoeda=factom, investidor=user.investidor)
        compra_3 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('15.40786135'), valor=Decimal('0.01104999'), data=datetime.date(2017, 6, 7), tipo_operacao='C', criptomoeda=factom, investidor=user.investidor)
        compra_4 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.61136046'), valor=Decimal('0.01080999'), data=datetime.date(2017, 6, 7), tipo_operacao='C', criptomoeda=factom, investidor=user.investidor)
        compra_5 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.81185596'), valor=Decimal('0.0098302'), data=datetime.date(2017, 6, 9), tipo_operacao='V', criptomoeda=factom, investidor=user.investidor)
        compra_6 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('7.68814404'), valor=Decimal('0.0098302'), data=datetime.date(2017, 6, 9), tipo_operacao='V', criptomoeda=factom, investidor=user.investidor)
        compra_7 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.11'), valor=Decimal('0.0967'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=ethereum, investidor=user.investidor)
        compra_8 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.33757127'), valor=Decimal('0.0967'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=ethereum, investidor=user.investidor)
        compra_9 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.41513183'), valor=Decimal('0.0967'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=ethereum, investidor=user.investidor)
        compra_10 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('75.00'), valor=Decimal('0.00117999'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=lisk, investidor=user.investidor)
        compra_11 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('9.5100467'), valor=Decimal('0.00117998'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=lisk, investidor=user.investidor)
        
        # Moedas utilizas nas operações
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_2, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_3, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_4, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_5, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_6, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_7, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_8, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_9, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_10, criptomoeda=bitcoin)
        OperacaoCriptomoedaMoeda.objects.create(operacao=compra_11, criptomoeda=bitcoin)
        
        # Taxas das operações
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.00343898'), operacao=compra_1, moeda=bitcoin)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.00513381'), operacao=compra_2, moeda=factom)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.03861619'), operacao=compra_3, moeda=factom)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.00153223'), operacao=compra_4, moeda=factom)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.00001995'), operacao=compra_5, moeda=bitcoin)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.00011336'), operacao=compra_6, moeda=bitcoin)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.000275'), operacao=compra_7, moeda=ethereum)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.000506357'), operacao=compra_8, moeda=ethereum)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.000622698'), operacao=compra_9, moeda=ethereum)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.1875'), operacao=compra_10, moeda=lisk)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.023775117'), operacao=compra_11, moeda=lisk)
        

    def test_qtd_moedas_ate_dia(self):
        # Posição no dia 10/06/2017
        # [u'ETH: 0.862703100000', u'FCT: 9.567610470000', u'LSK: 84.510046700000', u'BTC: 0.186517598234185500000000']
        """Testa quantidade de moedas até dia"""
        investidor = User.objects.get(username='tester').investidor
        qtd_moedas = calcular_qtd_moedas_ate_dia(investidor, datetime.date(2017, 6, 14))
        
        bitcoin = Criptomoeda.objects.get(nome='Bitcoin', ticker='BTC').id
        ethereum = Criptomoeda.objects.get(nome='Ethereum', ticker='ETH').id
        lisk = Criptomoeda.objects.get(nome='Lisk', ticker='LSK').id
        factom = Criptomoeda.objects.get(nome='Factom', ticker='FCT').id
        
        self.assertDictEqual(qtd_moedas, {ethereum: Decimal('0.862703100000'), factom: Decimal('9.567610470000'), lisk: Decimal('84.510046700000'), bitcoin: Decimal('0.186517598234185500000000')})
        
#     def test_qtd_cotas_ate_dia_por_fundo(self):
#         """Testa quantidade de cotas até dia por fundo"""
#         investidor = User.objects.get(username='tester').investidor
#         qtd_cotas = calcular_qtd_cotas_ate_dia_por_fundo(investidor, FundoInvestimento.objects.get(cnpj='00.000.000/0000-01').id, datetime.date(2017, 6, 14))
#         self.assertEqual(qtd_cotas, Decimal('4291.07590514'))
#         qtd_cotas = calcular_qtd_cotas_ate_dia_por_fundo(investidor, FundoInvestimento.objects.get(cnpj='00.000.000/0000-02').id, datetime.date(2017, 6, 14))
#         self.assertEqual(qtd_cotas, Decimal('179.6544'))
#         
#     def test_valor_cotas_ate_dia(self):
#         """Testa valor das cotas até dia"""
#         investidor = User.objects.get(username='tester').investidor
#         valor_fundos = calcular_valor_fundos_investimento_ate_dia(investidor, datetime.date(2017, 6, 14))
#         self.assertEqual(valor_fundos[FundoInvestimento.objects.get(cnpj='00.000.000/0000-01').id].quantize(Decimal('0.01')), Decimal('10589.63'))