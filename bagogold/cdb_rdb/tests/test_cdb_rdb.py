# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.utils.lc import \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa, \
    qtd_dias_uteis_no_periodo
from bagogold.cdb_rdb.forms import HistoricoVencimentoCDB_RDBForm, \
    HistoricoCarenciaCDB_RDBForm
from bagogold.cdb_rdb.models import CDB_RDB, HistoricoPorcentagemCDB_RDB, \
    OperacaoCDB_RDB, OperacaoVendaCDB_RDB, HistoricoCarenciaCDB_RDB, \
    HistoricoVencimentoCDB_RDB
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia, \
    buscar_operacoes_vigentes_ate_data
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class ValorCDB_RDBAteDiaTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # Usar data do dia 27/10/2016
        data_atual = datetime.date(2016, 11, 10)
        
        # RDB
        rdb = CDB_RDB.objects.create(nome="RDB Teste", investidor=user.investidor, tipo='R', tipo_rendimento=CDB_RDB.CDB_RDB_DI)
        rdb_porcentagem_di = HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=rdb, porcentagem=Decimal(110))
        OperacaoCDB_RDB.objects.create(quantidade=Decimal(3000), data=datetime.date(2016, 10, 14), tipo_operacao='C', \
                                            investimento=rdb, investidor=user.investidor)
        
        # Histórico
        date_list = [data_atual - datetime.timedelta(days=x) for x in range(0, (data_atual - datetime.date(2016, 10, 14)).days+1)]
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
            
    def test_valor_cdb_rdb_ate_dia(self):
        """Testar valores das operações no dia 27/10/2016, permitindo erro de até 1 centavo"""
        valor_cdb_rdb = calcular_valor_cdb_rdb_ate_dia(User.objects.get(username='tester').investidor, datetime.date(2016, 11, 10)).values()
        self.assertAlmostEqual(valor_cdb_rdb[0], Decimal('3032.63'), delta=0.01)

class CalcularValorCDB_RDBPrefixadoTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # RDB
        cdb = CDB_RDB.objects.create(nome="CDB Teste", investidor=user.investidor, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_PREFIXADO)
        cdb_porcentagem = HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb, porcentagem=Decimal('11.44'))
        OperacaoCDB_RDB.objects.create(quantidade=Decimal(2000), data=datetime.date(2017, 5, 23), tipo_operacao='C', \
                                            investimento=cdb, investidor=user.investidor)
        
    def test_valor_prefixado_no_dia(self):
        """Testar valor do CDB no dia 17/06/2017, permitindo erro de até 1 centavo"""
        qtd_dias = qtd_dias_uteis_no_periodo(datetime.date(2017, 5, 23), datetime.date(2017, 6, 16))
        operacao = OperacaoCDB_RDB.objects.get(investimento=CDB_RDB.objects.get(nome="CDB Teste"))
        valor = calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), qtd_dias)
        self.assertAlmostEqual(valor, Decimal('2014.67'), delta=0.01)
        
class CalcularQuantidadesCDB_RDBTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # CDB
        cdb = CDB_RDB.objects.create(nome='CDB Teste', investidor=user.investidor, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_DI)
        cdb_porcentagem_di = HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb, porcentagem=Decimal(110))
        
        # Operações
        operacao_1 = OperacaoCDB_RDB.objects.create(quantidade=Decimal(2000), data=datetime.date(2017, 1, 23), tipo_operacao='C', \
                                            investimento=cdb, investidor=user.investidor)
        operacao_2 = OperacaoCDB_RDB.objects.create(quantidade=Decimal(1000), data=datetime.date(2017, 2, 23), tipo_operacao='C', \
                                            investimento=cdb, investidor=user.investidor)
        operacao_3 = OperacaoCDB_RDB.objects.create(quantidade=Decimal(1000), data=datetime.date(2017, 3, 23), tipo_operacao='V', \
                                            investimento=cdb, investidor=user.investidor)
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=operacao_2, operacao_venda=operacao_3)
        operacao_4 = OperacaoCDB_RDB.objects.create(quantidade=Decimal(3000), data=datetime.date(2017, 3, 23), tipo_operacao='C', \
                                            investimento=cdb, investidor=user.investidor)
        operacao_5 = OperacaoCDB_RDB.objects.create(quantidade=Decimal(1000), data=datetime.date(2017, 5, 23), tipo_operacao='V', \
                                            investimento=cdb, investidor=user.investidor)
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=operacao_4, operacao_venda=operacao_5)
        
    def test_buscar_qtd_vigente_ao_fim_das_operacoes(self):
        """Testa a quantidade vigente de CDB/RDB ao fim das operações"""
        operacoes_vigentes = buscar_operacoes_vigentes_ate_data(Investidor.objects.get(user__username='tester'), datetime.date(2017, 5, 25))
        self.assertEqual(len(operacoes_vigentes), 2)
        self.assertIn(OperacaoCDB_RDB.objects.get(id=1), operacoes_vigentes)
        self.assertEqual(operacoes_vigentes.get(id=1).qtd_disponivel_venda, Decimal(2000))
        self.assertIn(OperacaoCDB_RDB.objects.get(id=4), operacoes_vigentes)
        self.assertEqual(operacoes_vigentes.get(id=4).qtd_disponivel_venda, Decimal(2000))
        
class FormulariosCarenciaVencimentoTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # CDB
        cdb = CDB_RDB.objects.create(nome='CDB Teste', investidor=user.investidor, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_DI)
        carencia_inicial = HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb, data=None, carencia=361)
        vencimento_inicial = HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb, data=None, vencimento=400)
    
    # Forms de carência
    def test_form_carencia_valido(self):
        """Testa se formulário de carencia é válido"""
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        form_carencia = HistoricoCarenciaCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertTrue(form_carencia.is_valid())
        carencia = form_carencia.save()
        self.assertEqual(carencia.cdb_rdb, cdb)
        self.assertEqual(carencia.data, datetime.date(2017, 9, 10))
        self.assertEqual(carencia.carencia, 365)
        
    def test_form_carencia_maior_que_vencimento_vigente(self):
        """Testa formulário de carencia onde o vencimento vigente está maior do que o carencia inserida"""
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        form_carencia = HistoricoCarenciaCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'carencia': 410,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertFalse(form_carencia.is_valid())

    def test_form_carencia_maior_que_vencimento_periodo(self):
        """Testa formulário de carencia onde o vencimento no período fica maior do que o carencia inserida"""
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 12), vencimento=300)
        form_carencia = HistoricoCarenciaCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertFalse(form_carencia.is_valid())
        
    def test_form_carencia_periodo_carencia_valido(self):
        """
        Testa formulário de carencia onde o vencimento é testado no período entre o carencia inserida e uma próxima carencia
        sem vencimento no período menor que carencia
        """
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 20), carencia=300)
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 20), vencimento=300)
        form_carencia = HistoricoCarenciaCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertTrue(form_carencia.is_valid())
        
    def test_form_carencia_periodo_carencia_invalido(self):
        """
        Testa formulário de carencia onde o vencimento é testado no período entre a carencia inserida e uma próxima carencia,
        com vencimento no período menor que carencia
        """
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 15), vencimento=370)
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 20), carencia=360)
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 20), vencimento=720)
        form_carencia = HistoricoCarenciaCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'carencia': 380,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertFalse(form_carencia.is_valid())
    
    # Forms de vencimento
    def test_form_vencimento_valido(self):
        """Testa se formulário de vencimento é válido"""
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        form_vencimento = HistoricoVencimentoCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertTrue(form_vencimento.is_valid())
        vencimento = form_vencimento.save()
        self.assertEqual(vencimento.cdb_rdb, cdb)
        self.assertEqual(vencimento.data, datetime.date(2017, 9, 10))
        self.assertEqual(vencimento.vencimento, 365)
        
    def test_form_vencimento_menor_que_carencia_vigente(self):
        """Testa formulário de vencimento onde a carência vigente está maior do que o vencimento inserido"""
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        form_vencimento = HistoricoVencimentoCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 360,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertFalse(form_vencimento.is_valid())

    def test_form_vencimento_menor_que_carencia_periodo(self):
        """Testa formulário de vencimento onde a carência no período fica maior do que o vencimento inserido"""
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 12), carencia=720)
        form_vencimento = HistoricoVencimentoCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertFalse(form_vencimento.is_valid())
        
    def test_form_vencimento_periodo_carencia_valido(self):
        """
        Testa formulário de vencimento onde a carência é testada no período entre o vencimento inserido e um próximo vencimento
        sem carência no período maior que vencimento
        """
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 20), vencimento=720)
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 20), carencia=720)
        form_vencimento = HistoricoVencimentoCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertTrue(form_vencimento.is_valid())
        
    def test_form_vencimento_periodo_carencia_invalido(self):
        """
        Testa formulário de vencimento onde a carência é testada no período entre o vencimento inserido e um próximo vencimento,
        com carência no período maior que vencimento
        """
        investidor = User.objects.get(username='tester').investidor
        cdb = CDB_RDB.objects.get(nome='CDB Teste')
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 15), carencia=370)
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 20), vencimento=720)
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb, data=datetime.date(2017, 9, 20), carencia=360)
        form_vencimento = HistoricoVencimentoCDB_RDBForm({
            'cdb_rdb': cdb,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, cdb_rdb=cdb, initial={'cdb_rdb': cdb.id})
        self.assertFalse(form_vencimento.is_valid())