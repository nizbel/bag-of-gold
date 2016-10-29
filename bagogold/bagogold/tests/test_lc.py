# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.lc import OperacaoLetraCredito, LetraCredito, \
    HistoricoPorcentagemLetraCredito, HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa, \
    calcular_valor_lc_ate_dia
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class AtualizarLCPorDITestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        LetraCredito.objects.create(nome="LCA Teste", investidor=user.investidor)
        OperacaoLetraCredito.objects.create(quantidade=Decimal(2500), data=datetime.date(2016, 5, 23), tipo_operacao='C', \
                                            letra_credito=LetraCredito.objects.get(nome="LCA Teste"), investidor=user.investidor)

    def test_calculo_valor_atualizado_taxa_di(self):
        """Testar de acordo com o pego no extrato da conta"""
        # 2506,30 em 1 de Junho (6 dias após, todos com taxa DI 14,13%)
        operacao = OperacaoLetraCredito.objects.get(quantidade=(Decimal(2500)))
        for i in range(0,6):
            operacao.quantidade = calcular_valor_atualizado_com_taxa(Decimal(14.13), operacao.quantidade, Decimal(80))
        operacao.quantidade = operacao.quantidade.quantize(Decimal('0.01'))
#         str_auxiliar = str(operacao.quantidade.quantize(Decimal('.0001')))
#         operacao.quantidade = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        self.assertEqual(operacao.quantidade, Decimal('2506.30'))

class ValorLCAteDiaTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # Usar data do dia 27/10/2016
        data_atual = datetime.date(2016, 10, 27)
        
        # Letra de crédito
        lc = LetraCredito.objects.create(nome="LCA Teste", investidor=user.investidor)
        lc_porcentagem_di = HistoricoPorcentagemLetraCredito.objects.create(letra_credito=lc, porcentagem_di=Decimal(80))
        OperacaoLetraCredito.objects.create(quantidade=Decimal(10000), data=datetime.date(2016, 3, 14), tipo_operacao='C', \
                                            letra_credito=LetraCredito.objects.get(nome="LCA Teste"), investidor=user.investidor)
        OperacaoLetraCredito.objects.create(quantidade=Decimal(2000), data=datetime.date(2016, 5, 20), tipo_operacao='C', \
                                            letra_credito=LetraCredito.objects.get(nome="LCA Teste"), investidor=user.investidor)
        OperacaoLetraCredito.objects.create(quantidade=Decimal(2500), data=datetime.date(2016, 5, 23), tipo_operacao='C', \
                                            letra_credito=LetraCredito.objects.get(nome="LCA Teste"), investidor=user.investidor)
        
        # Histórico
        date_list = [data_atual - datetime.timedelta(days=x) for x in range(0, (data_atual - datetime.date(2016, 3, 14)).days+1)]
        date_list = [data for data in date_list if data.weekday() < 5 and not verificar_feriado_bovespa(data)]
        
        for data in date_list:
            # Pular sexta-feira santa
            if data == datetime.date(2016, 3, 25):
                continue
            # Pular corpus christi
            if data == datetime.date(2016, 5, 26):
                continue
            
            if data >= datetime.date(2016, 10, 20):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(13.88))
            else:
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(14.13))
            
    def test_valor_lc_ate_dia(self):
        """Testar valores das operações no dia 27/10/2016, permitindo erro de até 1 centavo"""
        valor_lc = calcular_valor_lc_ate_dia(User.objects.get(username='tester').investidor, datetime.date(2016, 10, 27)).values()
        self.assertAlmostEqual(valor_lc[0], Decimal('15404.69'), delta=0.01)
