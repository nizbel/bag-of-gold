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
from bagogold.bagogold.models.cdb_rdb import CDB_RDB,\
    HistoricoPorcentagemCDB_RDB, OperacaoCDB_RDB
from bagogold.bagogold.utils.cdb_rdb import calcular_valor_cdb_rdb_ate_dia

class ValorCDB_RDBAteDiaTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # Usar data do dia 27/10/2016
        data_atual = datetime.date(2016, 11, 10)
        
        # Letra de crédito
        rdb = CDB_RDB.objects.create(nome="RDB Teste", investidor=user.investidor, tipo='R', tipo_rendimento=2)
        rdb_porcentagem_di = HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=rdb, porcentagem=Decimal(110))
        OperacaoCDB_RDB.objects.create(quantidade=Decimal(3000), data=datetime.date(2016, 10, 14), tipo_operacao='C', \
                                            investimento=CDB_RDB.objects.get(nome="RDB Teste"), investidor=user.investidor)
        
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
