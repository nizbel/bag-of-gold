# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls.base import reverse

from bagogold.cdb_rdb.models import CDB_RDB, HistoricoPorcentagemCDB_RDB, \
    HistoricoCarenciaCDB_RDB, HistoricoVencimentoCDB_RDB, OperacaoCDB_RDB


class ProxVencimentosPainelGeralTestCase(TestCase):
    def setUp(self):
        tester = User.objects.create_user('tester', 'tester@teste.com', 'tester')
        self.tester = tester.investidor
        
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        self.nizbel = nizbel.investidor 
        
        # Cadastrar investimentos
        cdb_rdb_1 = CDB_RDB.objects.create(investidor=nizbel, nome='CDB teste 1', tipo='C', tipo_rendimento=2)
        HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, porcentagem=Decimal(100))
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, carencia=Decimal(365))
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, porcentagem=Decimal(365))
        
        cdb_rdb_2 = CDB_RDB.objects.create(investidor=nizbel, nome='CDB teste 2', tipo='C', tipo_rendimento=2)
        HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, porcentagem=Decimal(100))
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, carencia=Decimal(365))
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, porcentagem=Decimal(365))
        
        OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=360)), tipo_operacao='C')
        OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=355)), tipo_operacao='C')
        OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=355)), tipo_operacao='C')
        OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=datetime.date.today(), tipo_operacao='C')
        
        OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=361)), tipo_operacao='C')
        OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=356)), tipo_operacao='C')
        
    def test_investidor_deslogado(self):
        """Testa investidor deslogado"""
        with self.assertRaises(ValueError):
            response = self.client.get(reverse('inicio:proximos_vencimentos'))
        
    def test_investidor_logado_sem_investimentos(self):
        """Testa investidor logado sem investimentos cadastrados"""
        pass
        
    def test_investidor_logado_com_investimentos(self):
        """Testa investidor logado com investimentos cadastrados"""
        pass