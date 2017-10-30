# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    Divisao, DivisaoTransferenciaCriptomoeda
from bagogold.criptomoeda.models import TransferenciaCriptomoeda, Criptomoeda, \
    OperacaoCriptomoeda, OperacaoCriptomoedaMoeda, OperacaoCriptomoedaTaxa,\
    ValorDiarioCriptomoeda
from bagogold.criptomoeda.utils import calcular_qtd_moedas_ate_dia, \
    calcular_qtd_moedas_ate_dia_por_criptomoeda, \
    calcular_qtd_moedas_ate_dia_por_divisao, buscar_valor_criptomoeda_atual, \
    buscar_valor_criptomoedas_atual, buscar_historico_criptomoeda, \
    buscar_valor_criptomoedas_atual_varias_moedas
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from urllib2 import urlopen
import datetime
import json

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
        
        for transferencia in TransferenciaCriptomoeda.objects.all():
            DivisaoTransferenciaCriptomoeda.objects.create(divisao=Divisao.objects.get(investidor=user.investidor), transferencia=transferencia, quantidade=transferencia.quantidade)
        
        compra_1 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.48784399'), preco_unitario=Decimal('9968.99994'), data=datetime.date(2017, 6, 6), tipo_operacao='C', criptomoeda=bitcoin, investidor=user.investidor)
        compra_2 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('2.04838866'), preco_unitario=Decimal('0.0110499'), data=datetime.date(2017, 6, 7), tipo_operacao='C', criptomoeda=factom, investidor=user.investidor)
        compra_3 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('15.40786135'), preco_unitario=Decimal('0.01104999'), data=datetime.date(2017, 6, 7), tipo_operacao='C', criptomoeda=factom, investidor=user.investidor)
        compra_4 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.61136046'), preco_unitario=Decimal('0.01080999'), data=datetime.date(2017, 6, 7), tipo_operacao='C', criptomoeda=factom, investidor=user.investidor)
        compra_5 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.81185596'), preco_unitario=Decimal('0.0098302'), data=datetime.date(2017, 6, 9), tipo_operacao='V', criptomoeda=factom, investidor=user.investidor)
        compra_6 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('7.68814404'), preco_unitario=Decimal('0.0098302'), data=datetime.date(2017, 6, 9), tipo_operacao='V', criptomoeda=factom, investidor=user.investidor)
        compra_7 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.109725'), preco_unitario=Decimal('0.0967'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=ethereum, investidor=user.investidor)
        compra_8 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.33706492'), preco_unitario=Decimal('0.0967'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=ethereum, investidor=user.investidor)
        compra_9 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.41450914'), preco_unitario=Decimal('0.0967'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=ethereum, investidor=user.investidor)
        compra_10 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('74.8125'), preco_unitario=Decimal('0.00117999'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=lisk, investidor=user.investidor)
        compra_11 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('9.48627159'), preco_unitario=Decimal('0.00117998'), data=datetime.date(2017, 6, 9), tipo_operacao='C', criptomoeda=lisk, investidor=user.investidor)
        
        for operacao in OperacaoCriptomoeda.objects.all():
            DivisaoOperacaoCriptomoeda.objects.create(divisao=Divisao.objects.get(investidor=user.investidor), operacao=operacao, quantidade=operacao.quantidade)
        
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
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.00050635'), operacao=compra_8, moeda=ethereum)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.00062269'), operacao=compra_9, moeda=ethereum)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.1875'), operacao=compra_10, moeda=lisk)
        OperacaoCriptomoedaTaxa.objects.create(valor=Decimal('0.02377511'), operacao=compra_11, moeda=lisk)
        

    def test_qtd_moedas_ate_dia(self):
        # Posição no dia 10/06/2017
        # POLO: eth - 0.86129905, lsk - 84.29877158, fct - 9.56761046
        # [u'ETH: 0.861299060000', u'FCT: 9.567610470000', u'LSK: 84.298771590000', u'BTC: 0.186902671181483300000000']
        """Testa quantidade de moedas até dia"""
        investidor = User.objects.get(username='tester').investidor
        qtd_moedas = calcular_qtd_moedas_ate_dia(investidor, datetime.date(2017, 6, 14))
        
        bitcoin = Criptomoeda.objects.get(nome='Bitcoin', ticker='BTC').id
        ethereum = Criptomoeda.objects.get(nome='Ethereum', ticker='ETH').id
        lisk = Criptomoeda.objects.get(nome='Lisk', ticker='LSK').id
        factom = Criptomoeda.objects.get(nome='Factom', ticker='FCT').id
        
        situacao_no_dia = {ethereum: Decimal('0.861299060000'), factom: Decimal('9.567610470000'), lisk: Decimal('84.298771590000'), 
                           bitcoin: Decimal('0.186902671181483300000000')}
        
        for id_criptomoeda in qtd_moedas.keys():
            self.assertAlmostEqual(qtd_moedas[id_criptomoeda], situacao_no_dia[id_criptomoeda], delta=Decimal('0.00000001'))
        
    def test_qtd_moedas_ate_dia_por_criptomoeda(self):
        # Posição no dia 10/06/2017
        # [u'ETH: 0.861299060000', u'FCT: 9.567610470000', u'LSK: 84.298771590000', u'BTC: 0.186902671181483300000000']
        """Testa quantidade de moedas até dia para uma criptomoeda"""
        investidor = User.objects.get(username='tester').investidor
        
        qtd_bitcoin = calcular_qtd_moedas_ate_dia_por_criptomoeda(investidor, Criptomoeda.objects.get(nome='Bitcoin', ticker='BTC').id, datetime.date(2017, 6, 14))
        self.assertAlmostEqual(qtd_bitcoin, Decimal('0.186902671181483300000000'), delta=Decimal('0.00000001'))
        
        qtd_ethereum = calcular_qtd_moedas_ate_dia_por_criptomoeda(investidor, Criptomoeda.objects.get(nome='Ethereum', ticker='ETH').id, datetime.date(2017, 6, 14))
        self.assertAlmostEqual(qtd_ethereum, Decimal('0.861299060000'), delta=Decimal('0.00000001'))

        qtd_lisk = calcular_qtd_moedas_ate_dia_por_criptomoeda(investidor, Criptomoeda.objects.get(nome='Lisk', ticker='LSK').id, datetime.date(2017, 6, 14))
        self.assertAlmostEqual(qtd_lisk, Decimal('84.298771590000'), delta=Decimal('0.00000001'))
        
        qtd_factom = calcular_qtd_moedas_ate_dia_por_criptomoeda(investidor, Criptomoeda.objects.get(nome='Factom', ticker='FCT').id, datetime.date(2017, 6, 14))
        self.assertAlmostEqual(qtd_factom, Decimal('9.567610470000'), delta=Decimal('0.00000001'))

    def test_qtd_moedas_ate_dia_por_divisao(self):
        # Posição no dia 10/06/2017, para divisão geral
        # [u'ETH: 0.861299060000', u'FCT: 9.567610470000', u'LSK: 84.298771590000', u'BTC: 0.186902671181483300000000']
        """Testa quantidade de moedas até dia para uma divisão"""
        investidor = User.objects.get(username='tester').investidor
        
        qtd_divisao = calcular_qtd_moedas_ate_dia_por_divisao(Divisao.objects.get(investidor=investidor).id, datetime.date(2017, 6, 14))
        
        bitcoin = Criptomoeda.objects.get(nome='Bitcoin', ticker='BTC').id
        ethereum = Criptomoeda.objects.get(nome='Ethereum', ticker='ETH').id
        lisk = Criptomoeda.objects.get(nome='Lisk', ticker='LSK').id
        factom = Criptomoeda.objects.get(nome='Factom', ticker='FCT').id
        
        situacao_no_dia = {ethereum: Decimal('0.861299060000'), factom: Decimal('9.567610470000'), lisk: Decimal('84.298771590000'), 
                           bitcoin: Decimal('0.186902671181483300000000')}
        
        for id_criptomoeda in qtd_divisao.keys():
            self.assertAlmostEqual(qtd_divisao[id_criptomoeda], situacao_no_dia[id_criptomoeda], delta=Decimal('0.00000001'))

    def test_buscar_valor_atual_bitcoin_cryptocompare(self):
        """Testa o retorno do CryptoCompare para uma criptomoeda"""
        ticker_bitcoin = 'BTC'
        url = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms=%s&tsyms=BRL' % (ticker_bitcoin)
        resultado = urlopen(url)
        data = json.load(resultado) 
        if 'Response' in data.keys() and 'Error' in data['Response']:
            self.fail('Resposta indica erro: %s' % (data['Message']))
        self.assertIn(ticker_bitcoin, data)
        self.assertIn('BRL', data[ticker_bitcoin])
        self.assertNotEqual(0, data[ticker_bitcoin]['BRL'])
        
    def test_buscar_valor_atual_criptomoeda(self):
        """Testa a busca de valor atual para uma criptomoeda"""
        tickers = Criptomoeda.objects.all().values_list('ticker', flat=True)[:3]
        for ticker in tickers:
            self.assertNotEqual(buscar_valor_criptomoeda_atual, 0)
            
    def test_buscar_valores_atuais_criptomoeda(self):
        """Testa a busca de valor atual para uma lista de criptomoedas"""
        tickers = Criptomoeda.objects.all().values_list('ticker', flat=True)[:3]
        valores_atuais = buscar_valor_criptomoedas_atual(tickers)
        self.assertEqual(len(tickers), len(valores_atuais))

    def test_buscar_valores_atuais_criptomoeda_varias_moedas(self):
        """Testa a busca de valor atual em várias moedas para uma lista de criptomoedas"""
        tickers = Criptomoeda.objects.all().values_list('ticker', flat=True)[:3]
        valores_atuais = buscar_valor_criptomoedas_atual_varias_moedas(tickers, [ValorDiarioCriptomoeda.MOEDA_DOLAR, ValorDiarioCriptomoeda.MOEDA_REAL])
        self.assertEqual(len(tickers), len(valores_atuais))
        for ticker in valores_atuais.keys():
            self.assertIn(ValorDiarioCriptomoeda.MOEDA_DOLAR, valores_atuais[ticker].keys())
            self.assertIn(ValorDiarioCriptomoeda.MOEDA_REAL, valores_atuais[ticker].keys())

    def test_buscar_historico(self):
        """Testa a busca de histórico de valor de uma criptomoeda"""
        ticker_bitcoin = 'BTC'
        historico = buscar_historico_criptomoeda(ticker_bitcoin)
        self.assertGreater(len(historico), 0)
        for data, valor in historico:
            self.assertTrue(isinstance(data, datetime.date))
            self.assertGreater(valor, 0)