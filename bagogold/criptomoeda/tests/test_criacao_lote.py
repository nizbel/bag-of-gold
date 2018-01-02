# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    Divisao, DivisaoTransferenciaCriptomoeda
from bagogold.criptomoeda.models import TransferenciaCriptomoeda, Criptomoeda, \
    OperacaoCriptomoeda, OperacaoCriptomoedaMoeda, OperacaoCriptomoedaTaxa, \
    ValorDiarioCriptomoeda
from bagogold.criptomoeda.utils import calcular_qtd_moedas_ate_dia, \
    calcular_qtd_moedas_ate_dia_por_criptomoeda, \
    calcular_qtd_moedas_ate_dia_por_divisao, buscar_valor_criptomoeda_atual, \
    buscar_valor_criptomoedas_atual, buscar_historico_criptomoeda, \
    buscar_valor_criptomoedas_atual_varias_moedas, salvar_operacoes_lote
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from urllib2 import urlopen
import datetime
import json

class CriacaoLoteTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        bitcoin = Criptomoeda.objects.create(nome='Bitcoin', ticker='BTC')
        
        ethereum = Criptomoeda.objects.create(nome='Ethereum', ticker='ETH')
        
        lisk = Criptomoeda.objects.create(nome='Lisk', ticker='LSK')
        
        factom = Criptomoeda.objects.create(nome='Factom', ticker='FCT')
        
        Divisao.objects.create(nome='Outra', investidor=user.investidor)
        

    def test_criacao_lote_operacoes_sucesso(self):
        """Testa criação de operações em lote sem erros"""
        investidor = User.objects.get(username='tester').investidor
        lista_operacoes = ['BTC/BRL;0,48784399;9968,99994;06/06/2017;C;0,00343898;BTC',
                           'FCT/BTC;2,04838866;0,0110499;07/06/2017;C;0,00513381;FCT',
                           'FCT/BTC;15,40786135;0,01104999;07/06/2017;C;0,03861619;FCT',
                           'FCT/BTC;0,61136046;0,01080999;07/06/2017;C;0,00153223;FCT',
                           'FCT/BTC;0,81185596;0,0098302;09/06/2017;V;0,00001995;BTC',
                           'FCT/BTC;7,68814404;0,0098302;09/06/2017;V;0,00011336;BTC',
                           'ETH/BTC;0,109725;0,0967;09/06/2017;C;0,000275;ETH',
                           'ETH/BTC;0,33706492;0,0967;09/06/2017;C;0,00050635;ETH',
                           'ETH/BTC;0,41450914;0,0967;09/06/2017;C;0,00062269;ETH',
                           'LSK/BTC;74,8125;0,00117999;09/06/2017;C;0,1875;LSK',
                           'LSK/BTC;9,48627159;0,00117998;09/06/2017;C;0,02377511;LSK'
                           ]
                           
        salvar_operacoes_lote(lista_operacoes, investidor, Divisao.objects.get(investidor=investidor, nome="Geral").id)
        self.assertTrue(OperacaoCriptomoeda.objects.filter(investidor=investidor).exists())
        
        qtd_moedas = calcular_qtd_moedas_ate_dia(investidor, datetime.date(2017, 6, 10))
        
        bitcoin = Criptomoeda.objects.get(nome='Bitcoin', ticker='BTC').id
        ethereum = Criptomoeda.objects.get(nome='Ethereum', ticker='ETH').id
        lisk = Criptomoeda.objects.get(nome='Lisk', ticker='LSK').id
        factom = Criptomoeda.objects.get(nome='Factom', ticker='FCT').id
        
        situacao_no_dia = {ethereum: Decimal('0.861299060000'), factom: Decimal('9.567610470000'), lisk: Decimal('84.298771590000'), 
                           bitcoin: Decimal('0.18812307118')}
        
        for id_criptomoeda in qtd_moedas.keys():
            self.assertAlmostEqual(qtd_moedas[id_criptomoeda], situacao_no_dia[id_criptomoeda], delta=Decimal('0.00000001'))
        
    def test_criacao_lote_operacoes_erro(self):
        """Testa criação de operações em lote com erros"""
        investidor = User.objects.get(username='tester').investidor
        divisao = Divisao.objects.get(investidor=investidor, nome="Geral")
        
        # Moeda e moeda utilizada iguais
        with self.assertRaises(ValueError):
            salvar_operacoes_lote(['BTC/BTC;0,48784399;9968,99994;06/06/2017;C;0,00343898;BTC'], investidor, divisao.id)
        
        # Quantidade 0
        with self.assertRaises(ValueError):
            salvar_operacoes_lote(['BTC/BRL;0;9968,99994;06/06/2017;C;0,00343898;BTC'], investidor, divisao.id)
        
        # Moeda taxa diferente de moeda e moeda utilizada
        with self.assertRaises(ValueError):
            salvar_operacoes_lote(['BTC/BRL;0,48784399;9968,99994;06/06/2017;C;0,00343898;LSK'], investidor, divisao.id)
            
        # Moeda não pode ser BRL
        with self.assertRaises(ValueError):
            salvar_operacoes_lote(['BRL/ETH;0,48784399;9968,99994;06/06/2017;C;0,00343898;ETH'], investidor, divisao.id)
            
        # String não pode ter mais ; que o formato padrão
        with self.assertRaises(ValueError):
            salvar_operacoes_lote(['BTC/BRL;0,48784399;9968,99994;06/06/2017;C;0,00343898;BTC;'], investidor, divisao.id)
        
        # Valor taxa deve ser maior ou igual a 0
        with self.assertRaises(ValueError):
            salvar_operacoes_lote(['BTC/BRL;0,48784399;9968,99994;06/06/2017;C;-0,02;BTC'], investidor, divisao.id)
        
        # Preço deve ser maior ou igual a 0
        with self.assertRaises(ValueError):
            salvar_operacoes_lote(['BTC/BRL;0,48784399;-3;06/06/2017;C;0,00343898;BTC'], investidor, divisao.id)
        
        # Data deve ser dia/mes/ano
        with self.assertRaises(ValueError):
            salvar_operacoes_lote(['BTC/BRL;0,48784399;9968,99994;2017/06/06;C;0,00343898;BTC'], investidor, divisao.id)
        
    def test_criacao_lote_transf_sucesso(self):
        """Testa criação de operações em lote sem erros"""
        pass
        
    def test_criacao_lote_transf_erro(self):
        """Testa criação de operações em lote com erros"""
        pass
        
    def test_qtd_moedas_ate_dia(self):
        """Testa se quantidade de moedas até dia está correta"""
        investidor = User.objects.get(username='tester').investidor
        
        lista_operacoes = ['BTC/BRL;0,48784399;9968,99994;06/06/2017;C;0,00343898;BTC',
                           'FCT/BTC;2,04838866;0,0110499;07/06/2017;C;0,00513381;FCT',
                           'FCT/BTC;15,40786135;0,01104999;07/06/2017;C;0,03861619;FCT',
                           'FCT/BTC;0,61136046;0,01080999;07/06/2017;C;0,00153223;FCT',
                           'FCT/BTC;0,81185596;0,0098302;09/06/2017;V;0,00001995;BTC',
                           'FCT/BTC;7,68814404;0,0098302;09/06/2017;V;0,00011336;BTC',
                           'ETH/BTC;0,109725;0,0967;09/06/2017;C;0,000275;ETH',
                           'ETH/BTC;0,33706492;0,0967;09/06/2017;C;0,00050635;ETH',
                           'ETH/BTC;0,41450914;0,0967;09/06/2017;C;0,00062269;ETH',
                           'LSK/BTC;74,8125;0,00117999;09/06/2017;C;0,1875;LSK',
                           'LSK/BTC;9,48627159;0,00117998;09/06/2017;C;0,02377511;LSK'
                           ]
                           
        salvar_operacoes_lote(lista_operacoes, investidor, Divisao.objects.get(investidor=investidor, nome="Geral").id)
        
        lista_transferencias = []
        
        #salvar_transferencias_lote(lista_transferencias, investidor, Divisao.objects.get(investidor=investidor, nome='Geral').id)