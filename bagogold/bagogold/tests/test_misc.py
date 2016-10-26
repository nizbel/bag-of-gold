# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao, Acao
from bagogold.bagogold.models.divisoes import Divisao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import OperacaoFII, FII
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.lc import LetraCredito, OperacaoLetraCredito
from bagogold.bagogold.models.td import Titulo, OperacaoTitulo
from bagogold.bagogold.utils.misc import calcular_iof_regressivo, \
    buscar_ultimas_operacoes
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class IOFTestCase(TestCase):
    # TODO preparar teste com TD
    
#     def setUp(self):
#         Titulo.objects.create(tipo="NTN-B Principal", data_vencimento=datetime.date(2035, 1, 1))
#         OperacaoTitulo.objects.create(preco_unitario=742.28, quantidade=1, data= models.DateField(u'Data', blank=True, null=True)
#     taxa_bvmf = models.DecimalField(u'Taxa BVMF', max_digits=11, decimal_places=2)
#     taxa_custodia = models.DecimalField(u'Taxa do agente de custódia', max_digits=11, decimal_places=2)
#     tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
#     titulo = models.ForeignKey('Titulo')
#     consolidada=True)

    def test_iof_regressivo(self):
        """Valores regressivos segundo a tabela"""
        self.assertEqual(calcular_iof_regressivo(1), 0.96)
        self.assertEqual(calcular_iof_regressivo(15), 0.50)
        self.assertEqual(calcular_iof_regressivo(29), 0.03)

class TelaInicioTestCase(TestCase):
    
    def setUp(self):
        # Investidor
        user = User.objects.create(username='tester')
        
        # Divisão
        divisao1 = Divisao.objects.create(investidor=user.investidor, nome='Teste 1')
        divisao2 = Divisao.objects.create(investidor=user.investidor, nome='Teste 2')
        
        # Operações
        # Ação
        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
        acao = Acao.objects.create(ticker='TEST3', empresa=empresa)
        operacao_acoes1 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(20), corretagem=Decimal(10), quantidade=200,
                                       data=datetime.date.today() - datetime.timedelta(days=0), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        operacao_acoes2 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(20), corretagem=Decimal(5), quantidade=100, 
                                       data=datetime.date.today() - datetime.timedelta(days=1), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        operacao_acoes3 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(10), corretagem=Decimal(10), quantidade=300, 
                                       data=datetime.date.today() - datetime.timedelta(days=2), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        
        # FII
        fii = FII.objects.create(ticker='TEST11')
        operacao_fii1 = OperacaoFII.objects.create(investidor=user.investidor, preco_unitario=Decimal(15), corretagem=Decimal(10), quantidade=400, 
                                    data=datetime.date.today() - datetime.timedelta(days=1), tipo_operacao='C', fii=fii, emolumentos=Decimal(0))
        operacao_fii1 = OperacaoFII.objects.create(investidor=user.investidor, preco_unitario=Decimal(100), corretagem=Decimal(10), quantidade=10, 
                                    data=datetime.date.today() - datetime.timedelta(days=2), tipo_operacao='C', fii=fii, emolumentos=Decimal(0))
        
        # LC
        lc = LetraCredito.objects.create(nome='Letra de teste', investidor=user.investidor)
        operacao_lc1 = OperacaoLetraCredito.objects.create(investidor=user.investidor, letra_credito=lc, data=datetime.date.today() - datetime.timedelta(days=0), tipo_operacao='C',
                                            quantidade=Decimal(1000))
        operacao_lc2 = OperacaoLetraCredito.objects.create(investidor=user.investidor, letra_credito=lc, data=datetime.date.today() - datetime.timedelta(days=1), tipo_operacao='C',
                                            quantidade=Decimal(2000))
        
    def test_buscar_ultimas_cinco_operacoes_deve_trazer_cinco(self):
        """Busca últimas 5 operações"""
        investidor = Investidor.objects.get(user__username='tester')
        
        self.assertTrue(len(buscar_ultimas_operacoes(investidor, 5)) == 5)
        
    def test_buscar_ultimas_dez_operacoes_deve_trazer_sete(self):
        """Testar se buscar últimas 10 operações traz apenas as 7"""
        investidor = Investidor.objects.get(user__username='tester')
        
        self.assertTrue(len(buscar_ultimas_operacoes(investidor, 10)) == 7)
    
    def test_buscar_ultimas_cinco_operacoes_nao_deve_trazer_duas(self):
        """Verificar se últimas operações não incluem operações com data de 2 dias atrás"""
        investidor = Investidor.objects.get(user__username='tester')
        ultimas_operacoes = buscar_ultimas_operacoes(investidor, 5)
        
        self.assertNotIn(OperacaoAcao.objects.get(data=datetime.date.today() - datetime.timedelta(days=2)), ultimas_operacoes)
        self.assertNotIn(OperacaoFII.objects.get(data=datetime.date.today() - datetime.timedelta(days=2)), ultimas_operacoes)
        
    def test_buscar_ultimas_operacoes_deve_ser_ordenado_decrescente_por_data(self):
        """Verificar se últimas operações está ordenado de maneira decrescente por data"""
        investidor = Investidor.objects.get(user__username='tester')
        ultimas_operacoes = buscar_ultimas_operacoes(investidor, 5)
        
        data = ultimas_operacoes[0].data
        for operacao in ultimas_operacoes[1:]:
            self.assertTrue(operacao.data <= data)
            data = operacao.data