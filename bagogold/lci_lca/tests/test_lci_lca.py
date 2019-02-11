# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa, \
    qtd_dias_uteis_no_periodo
from bagogold.bagogold.utils.taxas_indexacao import \
    calcular_valor_atualizado_com_taxa_di,\
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.lci_lca.models import OperacaoLetraCredito, LetraCredito, \
    HistoricoPorcentagemLetraCredito, HistoricoVencimentoLetraCredito
from bagogold.lci_lca.utils import calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_lci_lca_ate_dia, simulador_lci_lca
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class AtualizarLetraCreditoPorDITestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        lci_lca = LetraCredito.objects.create(nome="LCA Teste", investidor=user.investidor, tipo_rendimento=LetraCredito.LCI_LCA_DI)
        HistoricoPorcentagemLetraCredito.objects.create(letra_credito=lci_lca, porcentagem=Decimal(80))
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci_lca, vencimento=2000)
        OperacaoLetraCredito.objects.create(quantidade=Decimal(2500), data=datetime.date(2016, 5, 23), tipo_operacao='C', \
                                            letra_credito=lci_lca, investidor=user.investidor)

    def test_calculo_valor_atualizado_taxa_di(self):
        """Testar de acordo com o pego no extrato da conta"""
        # 2506,30 em 1 de Junho (6 dias após, todos com taxa DI 14,13%)
        operacao = OperacaoLetraCredito.objects.get(quantidade=(Decimal(2500)))
        for i in range(0,6):
            operacao.quantidade = calcular_valor_atualizado_com_taxa_di(Decimal(14.13), operacao.quantidade, operacao.porcentagem())
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
        lci_lca = LetraCredito.objects.create(nome="LCA Teste", investidor=user.investidor, tipo_rendimento=LetraCredito.LCI_LCA_DI)
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci_lca, vencimento=2000)
        lci_lca_porcentagem = HistoricoPorcentagemLetraCredito.objects.create(letra_credito=lci_lca, porcentagem=Decimal(80))
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
            
    def test_valor_lci_lca_ate_dia(self):
        """Testar valores das operações no dia 27/10/2016, permitindo erro de até 1 centavo"""
        valor_lci_lca = calcular_valor_lci_lca_ate_dia(User.objects.get(username='tester').investidor, datetime.date(2016, 10, 27)).values()
        self.assertAlmostEqual(valor_lci_lca[0], Decimal('15404.69'), delta=0.01)
        
class SimuladorLCI_LCATestCase(TestCase):
    
    def setUp(self):
        HistoricoTaxaDI.objects.create(data=datetime.date(2017, 10, 19), taxa=Decimal(12.13))
        HistoricoTaxaDI.objects.create(data=datetime.date(2017, 10, 20), taxa=Decimal(14.13))
        
    def test_simulador_lci_lca_pos_di(self):
        """Testa se simulador está buscando os valores corretamente para pos-fixado DI"""
        filtros_simulador = {'periodo': Decimal(365), 'percentual_indice': Decimal(88), \
                             'tipo': 'POS', 'indice': 'DI', 'aplicacao': Decimal(1400)}
        ultimo_valor_simulador = simulador_lci_lca(filtros_simulador)[-1][1]
        
        qtd_dias_uteis = qtd_dias_uteis_no_periodo(datetime.date.today(), datetime.date.today() \
                                                   + datetime.timedelta(days=int(filtros_simulador['periodo'])))
        valor_atualizado = calcular_valor_atualizado_com_taxas_di({Decimal(14.13): qtd_dias_uteis}, 
                                                                  filtros_simulador['aplicacao'], filtros_simulador['percentual_indice'])
        self.assertAlmostEqual(ultimo_valor_simulador, valor_atualizado,  delta=0.01)
        
        # Alterar valor do último DI
        HistoricoTaxaDI.objects.create(data=datetime.date(2017, 10, 23), taxa=Decimal(13.13))
        ultimo_valor_simulador = simulador_lci_lca(filtros_simulador)[-1][1]
        
        valor_atualizado = calcular_valor_atualizado_com_taxas_di({Decimal(13.13): qtd_dias_uteis}, 
                                                                  filtros_simulador['aplicacao'], filtros_simulador['percentual_indice'])
        self.assertAlmostEqual(ultimo_valor_simulador, valor_atualizado,  delta=0.01)
        
    def test_simulador_lci_lca_pre(self):
        """Testa se simulador está buscando os valores corretamente para prefixado"""
        filtros_simulador = {'periodo': Decimal(721), 'percentual_indice': Decimal('9.5'), \
                             'tipo': 'PRE', 'indice': 'PRE', 'aplicacao': Decimal(1400)}
        ultimo_valor_simulador = simulador_lci_lca(filtros_simulador)[-1][1]
        
        qtd_dias_uteis = qtd_dias_uteis_no_periodo(datetime.date.today(), datetime.date.today() \
                                                   + datetime.timedelta(int(filtros_simulador['periodo'])))
        valor_atualizado = calcular_valor_atualizado_com_taxa_prefixado(filtros_simulador['aplicacao'], filtros_simulador['percentual_indice'],
                                                                         qtd_dias_uteis)
        self.assertAlmostEqual(ultimo_valor_simulador, valor_atualizado,  delta=0.01)