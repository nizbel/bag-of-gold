# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from bagogold.cdb_rdb.forms import OperacaoCDB_RDBForm
from bagogold.cdb_rdb.models import CDB_RDB, HistoricoCarenciaCDB_RDB, \
    HistoricoVencimentoCDB_RDB, HistoricoPorcentagemCDB_RDB, OperacaoCDB_RDB,\
    OperacaoVendaCDB_RDB


class FormularioOperacaoCDB_RDBTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        self.investidor = user.investidor
        
        # CDB
        self.cdb = CDB_RDB.objects.create(nome='CDB Teste', investidor=self.investidor, tipo_rendimento=CDB_RDB.CDB_RDB_DI)
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=self.cdb, data=None, carencia=358)
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=self.cdb, data=None, vencimento=365)
        HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=self.cdb, data=None, porcentagem=100)
    
    def test_form_inserir_compra_valido(self):
        """Testa se formulário de inserir operação de compra em CDB/RDB é válido"""
        form_compra = OperacaoCDB_RDBForm({
            'tipo_operacao': 'C', 'quantidade': Decimal(1000), 'data': datetime.date(2017, 10, 10), 
            'operacao_compra': None, 'cdb_rdb': self.cdb.id
        }, investidor=self.investidor)
        self.assertTrue(form_compra.is_valid())
        # Usar commit=False como nas views
        operacao_compra = form_compra.save(commit=False)
        operacao_compra.investidor=self.investidor
        operacao_compra.save()
        
        self.assertEqual(operacao_compra.tipo_operacao, 'C')
        self.assertEqual(operacao_compra.quantidade, Decimal(1000))
        self.assertEqual(operacao_compra.data, datetime.date(2017, 10, 10))
        self.assertEqual(operacao_compra.operacao_compra_relacionada(), None)
        self.assertEqual(operacao_compra.cdb_rdb, self.cdb)
        
    def test_form_inserir_venda_valido(self):
        """Testa se formulário de inserir operação de venda em CDB/RDB é válido"""
        operacao_compra = OperacaoCDB_RDB.objects.create(tipo_operacao='C', quantidade=Decimal(1000), data=datetime.date(2017, 10, 13),
                                                         cdb_rdb=self.cdb, investidor=self.investidor)
        form_venda = OperacaoCDB_RDBForm({
            'tipo_operacao': 'V', 'quantidade': Decimal(1000), 'data': datetime.date(2018, 10, 15), 
            'operacao_compra': operacao_compra.id, 'cdb_rdb': self.cdb.id
        }, investidor=self.investidor)
#         self.assertTrue(form_venda.is_valid())
        if not form_venda.is_valid():
            print form_venda.errors
        # Usar commit=False como nas views
        operacao_venda = form_venda.save(commit=False)
        operacao_venda.investidor=self.investidor
        operacao_venda.save()
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=operacao_compra, operacao_venda=operacao_venda)
        
        self.assertEqual(operacao_venda.tipo_operacao, 'V')
        self.assertEqual(operacao_venda.quantidade, Decimal(1000))
        self.assertEqual(operacao_venda.data, datetime.date(2018, 10, 15))
        self.assertEqual(operacao_venda.operacao_compra_relacionada(), operacao_compra)
        self.assertEqual(operacao_venda.cdb_rdb, self.cdb)
        
    def test_form_inserir_venda_invalido_data_menor_carencia(self):
        """Testa se formulário de inserir operação de venda em CDB/RDB é inválido por ter data anterior a carência"""
        operacao_compra = OperacaoCDB_RDB.objects.create(tipo_operacao='C', quantidade=Decimal(1000), data=datetime.date(2017, 10, 13),
                                                         cdb_rdb=self.cdb, investidor=self.investidor)
        form_venda = OperacaoCDB_RDBForm({
            'tipo_operacao': 'V', 'quantidade': Decimal(1000), 'data': datetime.date(2018, 10, 2), 
            'operacao_compra': operacao_compra.id, 'cdb_rdb': self.cdb.id
        }, investidor=self.investidor)
        self.assertFalse(form_venda.is_valid())
        self.assertIn('operacao_compra', form_venda.errors)
        self.assertTrue(len(form_venda.errors) == 1)
        
    def test_form_inserir_venda_invalido_data_maior_vencimento(self):
        """Testa se formulário de inserir operação de venda em CDB/RDB é inválido por ter data posterior a vencimento"""
        operacao_compra = OperacaoCDB_RDB.objects.create(tipo_operacao='C', quantidade=Decimal(1000), data=datetime.date(2017, 10, 13),
                                                         cdb_rdb=self.cdb, investidor=self.investidor)
        form_venda = OperacaoCDB_RDBForm({
            'tipo_operacao': 'V', 'quantidade': Decimal(1000), 'data': datetime.date(2018, 10, 16), 
            'operacao_compra': operacao_compra.id, 'cdb_rdb': self.cdb.id
        }, investidor=self.investidor)
        self.assertFalse(form_venda.is_valid())
        self.assertIn('operacao_compra', form_venda.errors)
        self.assertTrue(len(form_venda.errors) == 1)
        
