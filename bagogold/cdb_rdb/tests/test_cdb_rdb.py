# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa,\
    qtd_dias_uteis_no_periodo
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.test import TestCase
import datetime
from bagogold.cdb_rdb.models import CDB_RDB,\
    HistoricoPorcentagemCDB_RDB, OperacaoCDB_RDB, OperacaoVendaCDB_RDB
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia,\
    buscar_operacoes_vigentes_ate_data

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