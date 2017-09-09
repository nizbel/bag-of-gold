# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.lc import OperacaoLetraCredito, LetraCredito, \
    HistoricoPorcentagemLetraCredito, HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa_di, \
    calcular_valor_lc_ate_dia, calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa,\
    qtd_dias_uteis_no_periodo
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.test import TestCase
import datetime
from bagogold.cdb_rdb.models import CDB_RDB,\
    HistoricoPorcentagemCDB_RDB, OperacaoCDB_RDB
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia

class ValorCDB_RDBAteDiaTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # Usar data do dia 27/10/2016
        data_atual = datetime.date(2016, 11, 10)
        
        # RDB
        rdb = CDB_RDB.objects.create(nome="RDB Teste", investidor=user.investidor, tipo='R', tipo_rendimento=2)
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

class CalcularValorCDBPrefixadoTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # RDB
        cdb = CDB_RDB.objects.create(nome="CDB Teste", investidor=user.investidor, tipo='C', tipo_rendimento=1)
        cdb_porcentagem = HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb, porcentagem=Decimal('11.44'))
        OperacaoCDB_RDB.objects.create(quantidade=Decimal(2000), data=datetime.date(2017, 5, 23), tipo_operacao='C', \
                                            investimento=cdb, investidor=user.investidor)
        
    def test_valor_prefixado_no_dia(self):
        """Testar valor do CDB no dia 17/06/2017, permitindo erro de até 1 centavo"""
        qtd_dias = qtd_dias_uteis_no_periodo(datetime.date(2017, 5, 23), datetime.date(2017, 6, 16))
        operacao = OperacaoCDB_RDB.objects.get(investimento=CDB_RDB.objects.get(nome="CDB Teste"))
        valor = calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), qtd_dias)
        self.assertAlmostEqual(valor, Decimal('2014.67'), delta=0.01)