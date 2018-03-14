# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCDB_RDB, Divisao, \
    CheckpointDivisaoCDB_RDB
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.investidores import atualizar_checkpoints
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa, \
    qtd_dias_uteis_no_periodo, calcular_iof_e_ir_longo_prazo
from bagogold.cdb_rdb.models import CDB_RDB, OperacaoVendaCDB_RDB, \
    OperacaoCDB_RDB, HistoricoPorcentagemCDB_RDB, CheckpointCDB_RDB
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia, \
    buscar_operacoes_vigentes_ate_data, calcular_valor_operacao_cdb_rdb_ate_dia, \
    calcular_valor_cdb_rdb_ate_dia_por_divisao, \
    calcular_valor_um_cdb_rdb_ate_dia_por_divisao
from bagogold.lci_lca.utils import calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Case, When, F
from django.db.models.functions import Coalesce
from django.test import TestCase
import datetime
 
class CalcularQuantidadesCDB_RDBTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
         
        cdb_1 = CDB_RDB.objects.create(nome="CDB 1", investidor=user.investidor, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_DI)
        # TODO regularizar testes de IPCA
        cdb_2 = CDB_RDB.objects.create(nome="CDB 2", investidor=user.investidor, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_IPCA)
        cdb_3 = CDB_RDB.objects.create(nome="CDB 3", investidor=user.investidor, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_PREFIXADO)
        
        HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_1, porcentagem=100)
        HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_3, porcentagem=10)
         
        # Históricos DI e IPCA
        # Data final é 14/02/2018 mas atualizações só contam até data anterior para manter DI e prefixado pareados
        data_final = datetime.date(2018, 2, 13)
        date_list = [data_final - datetime.timedelta(days=x) for x in range(0, (data_final - datetime.date(2017, 5, 11)).days+1)]
        date_list = [data for data in date_list if data.weekday() < 5 and not verificar_feriado_bovespa(data)]
        
        for data in date_list:
            if data >= datetime.date(2018, 2, 8):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(6.64))
            elif data >= datetime.date(2017, 12, 7):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(6.89))
            elif data >= datetime.date(2017, 10, 26):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(7.39))
            elif data >= datetime.date(2017, 9, 8):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(8.14))
            elif data >= datetime.date(2017, 7, 27):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(9.14))
            elif data >= datetime.date(2017, 6, 1):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(10.14))
            else:
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(11.13))
        
        # Operações de compra
        compra_1 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=2000)
        compra_2 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=1000)
        compra_3 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=2000)
        compra_4 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=1000)
        compra_5 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=2000)
        compra_6 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=1000)
        compra_7 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=3000)
         
        # Operações de venda
        venda_1 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_1, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 6, 15), quantidade=500)
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra_2, operacao_venda=venda_1)
        venda_2 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_2, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 6, 15), quantidade=500)
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra_4, operacao_venda=venda_2)
        venda_3 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 6, 15), quantidade=500)
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra_6, operacao_venda=venda_3)
        venda_4 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 6, 15), quantidade=3000)
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra_7, operacao_venda=venda_4)
         
        for operacao in OperacaoCDB_RDB.objects.all():
            DivisaoOperacaoCDB_RDB.objects.create(divisao=Divisao.objects.get(investidor=user.investidor), operacao=operacao, quantidade=operacao.quantidade)
         
        # Operação extra para testes de divisão
        operacao_divisao = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=3000)
        divisao_teste = Divisao.objects.create(investidor=user.investidor, nome=u'Divisão de teste')
        DivisaoOperacaoCDB_RDB.objects.create(divisao=divisao_teste, operacao=operacao_divisao, quantidade=operacao_divisao.quantidade)
         
         
    def test_calculo_qtd_cdb_por_operacao(self):
        """Calcula quantidade de CDBs do usuário individualmente"""
        investidor = Investidor.objects.get(user__username='test')
        cdb_1 = CDB_RDB.objects.get(nome="CDB 1")
        cdb_3 = CDB_RDB.objects.get(nome="CDB 3")
        
        for operacao in OperacaoCDB_RDB.objects.filter(investidor=investidor, tipo_operacao='C').exclude(cdb_rdb=CDB_RDB.objects.get(nome="CDB 2")):
            if operacao.cdb_rdb == cdb_1:
                data = datetime.date(2017, 5, 11)
                self.assertAlmostEqual(calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data), operacao.quantidade*Decimal('1.00042'), delta=Decimal('0.01'))
                data = datetime.date(2017, 6, 15)
                self.assertAlmostEqual(calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data), operacao.qtd_disponivel_venda_na_data(data) \
                                       * Decimal('1.01016557'), delta=Decimal('0.01'))
                data = datetime.date(2018, 2, 14)
                self.assertAlmostEqual(calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data), operacao.qtd_disponivel_venda_na_data(data) \
                                       * Decimal('1.06363295'), delta=Decimal('0.01'))
            elif operacao.cdb_rdb == cdb_3:
                data = datetime.date(2017, 5, 11)
                self.assertAlmostEqual(calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data), operacao.quantidade, delta=Decimal('0.01'))
                data = datetime.date(2017, 6, 15)
                qtd_dias_uteis = Decimal(qtd_dias_uteis_no_periodo(operacao.data, data))
                self.assertAlmostEqual(calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data), operacao.qtd_disponivel_venda_na_data(data) \
                                  * pow((1+Decimal('0.1')), (qtd_dias_uteis/252)), delta=Decimal('0.01'))
                data = datetime.date(2018, 2, 14)
                qtd_dias_uteis = Decimal(qtd_dias_uteis_no_periodo(operacao.data, data))
                self.assertAlmostEqual(calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data), operacao.qtd_disponivel_venda_na_data(data) \
                                  * pow((1+Decimal('0.1')), (qtd_dias_uteis/252)), delta=Decimal('0.01'))
         
    def test_calculo_qtd_cdbs(self):
        """Calcula quantidade de CDB/RDBs do usuário"""
        investidor = Investidor.objects.get(user__username='test')
       
        data = datetime.date(2017, 5, 11)
        cdb_rdb = calcular_valor_cdb_rdb_ate_dia(investidor, data)
        for cdb_rdb_id in cdb_rdb.keys():
            self.assertEqual(cdb_rdb[cdb_rdb_id], sum([calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data) for operacao in OperacaoCDB_RDB.objects.filter(tipo_operacao='C', cdb_rdb__id=cdb_rdb_id)]))
       
        data = datetime.date(2017, 6, 15)
        cdb_rdb = calcular_valor_cdb_rdb_ate_dia(investidor, data)
        for cdb_rdb_id in cdb_rdb.keys():
            self.assertEqual(cdb_rdb[cdb_rdb_id], sum([calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data) for operacao in OperacaoCDB_RDB.objects.filter(tipo_operacao='C', cdb_rdb__id=cdb_rdb_id)]))
        
        data = datetime.date(2018, 2, 14)
        cdb_rdb = calcular_valor_cdb_rdb_ate_dia(investidor, data)
        for cdb_rdb_id in cdb_rdb.keys():
            self.assertEqual(cdb_rdb[cdb_rdb_id], sum([calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data) for operacao in OperacaoCDB_RDB.objects.filter(tipo_operacao='C', cdb_rdb__id=cdb_rdb_id)]))
      
    def test_verificar_qtd_divisao(self):
        """Testa se a quantidade de CDB/RDB por divisão está correta"""
        investidor = Investidor.objects.get(user__username='test')
        
        data = datetime.date(2017, 5, 11)
        valor_cdb_rdb = calcular_valor_cdb_rdb_ate_dia(investidor, data)
        # Comparar a soma das divisões para cada investimento com o total calculado
        for cdb_rdb_id in valor_cdb_rdb.keys():
            cdb_rdb = CDB_RDB.objects.get(id=cdb_rdb_id)
            self.assertAlmostEqual(valor_cdb_rdb[cdb_rdb_id], sum([calcular_valor_um_cdb_rdb_ate_dia_por_divisao(cdb_rdb, divisao.id, data) \
                                                             for divisao in Divisao.objects.filter(investidor=investidor)]), delta=Decimal('0.01'))
            
        data = datetime.date(2017, 6, 15)
        valor_cdb_rdb = calcular_valor_cdb_rdb_ate_dia(investidor, data)
        # Comparar a soma das divisões para cada investimento com o total calculado
        for cdb_rdb_id in valor_cdb_rdb.keys():
            cdb_rdb = CDB_RDB.objects.get(id=cdb_rdb_id)
            self.assertAlmostEqual(valor_cdb_rdb[cdb_rdb_id], sum([calcular_valor_um_cdb_rdb_ate_dia_por_divisao(cdb_rdb, divisao.id, data) \
                                                             for divisao in Divisao.objects.filter(investidor=investidor)]), delta=Decimal('0.01'))
            
        data = datetime.date(2018, 2, 14)
        valor_cdb_rdb = calcular_valor_cdb_rdb_ate_dia(investidor, data)
        # Comparar a soma das divisões para cada investimento com o total calculado
        for cdb_rdb_id in valor_cdb_rdb.keys():
            cdb_rdb = CDB_RDB.objects.get(id=cdb_rdb_id)
            self.assertAlmostEqual(valor_cdb_rdb[cdb_rdb_id], sum([calcular_valor_um_cdb_rdb_ate_dia_por_divisao(cdb_rdb, divisao.id, data) \
                                                             for divisao in Divisao.objects.filter(investidor=investidor)]), delta=Decimal('0.01'))
            
          
    def test_verificar_checkpoints_apagados(self):
        """Testa se checkpoints são apagados caso quantidades de CDB do usuário se torne zero"""
        investidor = Investidor.objects.get(user__username='test')
        cdb = CDB_RDB.objects.get(nome='CDB 1')
        
        compra = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb, investidor=investidor, tipo_operacao='C', data=datetime.date(2017, 8, 11), quantidade=3000)
        self.assertTrue(CheckpointCDB_RDB.objects.filter(operacao=compra).exists())
         
        # Apagar checkpoint por venda
        venda = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb, investidor=investidor, tipo_operacao='V', data=datetime.date(2017, 8, 15), quantidade=3000)
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra, operacao_venda=venda)
        self.assertFalse(CheckpointCDB_RDB.objects.filter(operacao=compra).exists())
         
        # Checkpoints devem retornar ao apagar venda
        venda.delete()
        self.assertTrue(CheckpointCDB_RDB.objects.filter(operacao=compra).exists())
        
        # Checkpoints devem sumir ao apagar compra
        compra_id = compra.id
        self.assertTrue(CheckpointCDB_RDB.objects.filter(operacao__id=compra_id).exists())
        compra.delete()
        self.assertFalse(CheckpointCDB_RDB.objects.filter(operacao__id=compra_id).exists())
          
    def test_verificar_qtd_atualizada(self):
        """Testa cálculos de quantidade atualizada"""
        investidor = Investidor.objects.get(user__username='test')
        cdb_1 = CDB_RDB.objects.get(nome="CDB 1")
        cdb_3 = CDB_RDB.objects.get(nome="CDB 3")
        
        for operacao in OperacaoCDB_RDB.objects.filter(investidor=investidor, tipo_operacao='C').exclude(cdb_rdb=CDB_RDB.objects.get(nome="CDB 2")):
            if operacao.cdb_rdb == cdb_1:
                data = datetime.date(2017, 12, 31)
                valor_operacao_fim_2017 = calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data)
                if valor_operacao_fim_2017 > 0:
                    self.assertAlmostEqual(CheckpointCDB_RDB.objects.get(operacao=operacao, ano=2017).qtd_atualizada, 
                                     CheckpointCDB_RDB.objects.get(operacao=operacao, ano=2017).qtd_restante * Decimal('1.05552808'),
                                     delta=Decimal('0.01'))
                else:
                    self.assertFalse(CheckpointCDB_RDB.objects.filter(operacao=operacao, ano=2017).exists())
            elif operacao.cdb_rdb == cdb_3:
                data = datetime.date(2017, 12, 31)
                qtd_dias_uteis = Decimal(qtd_dias_uteis_no_periodo(operacao.data, data))
                valor_operacao_fim_2017 = calcular_valor_operacao_cdb_rdb_ate_dia(operacao, data)
                if valor_operacao_fim_2017 > 0:
                    self.assertAlmostEqual(CheckpointCDB_RDB.objects.get(operacao=operacao, ano=2017).qtd_atualizada, 
                                     CheckpointCDB_RDB.objects.get(operacao=operacao, ano=2017).qtd_restante * pow((1+Decimal('0.1')), (qtd_dias_uteis/252)),
                                     delta=Decimal('0.01'))
                else:
                    self.assertFalse(CheckpointCDB_RDB.objects.filter(operacao=operacao, ano=2017).exists())
                
        
        
#         # Testar funções individuais
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 3, 1), 'BAPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BAPO11'), Decimal(4500) / 43, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 6, 4), 'BAPO11'), Decimal(4500) / 430, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 11, 20), 'BAPO11'), Decimal(4500) / 430 - Decimal('9.1'), places=3)
#           
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 3, 1), 'BBPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BBPO11'), Decimal(43200) / 430, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 6, 4), 'BBPO11'), Decimal(43200) / 43, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 11, 20), 'BBPO11'), Decimal(43200) / 43, places=3)
#           
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 3, 1), 'BCPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BCPO11'), Decimal(3900) / 37, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 6, 4), 'BCPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 11, 20), 'BCPO11'), 0, places=3)
#           
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 3, 1), 'BDPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BDPO11'), Decimal(27300) / 271, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 6, 4), 'BDPO11'), Decimal(27300 + 3900) / 617, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 11, 20), 'BDPO11'), Decimal(27300 + 3900 + 9400) / 707, places=3)
#           
#         # Testar função geral
#         for data in [datetime.date(2017, 3, 1), datetime.date(2017, 5, 12), datetime.date(2017, 6, 4), datetime.date(2017, 11, 20)]:
#             precos_medios = calcular_preco_medio_fiis_ate_dia(investidor, data)
#             for ticker in FII.objects.all().values_list('ticker', flat=True):
#                 qtd_individual = calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, data, ticker)
#                 if qtd_individual > 0:
#                     self.assertAlmostEqual(precos_medios[ticker], qtd_individual, places=3)
#                 else:
#                     self.assertNotIn(ticker, precos_medios.keys())
#           
#         # Testar checkpoints
#         self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=2016).exists())
#         for fii in FII.objects.all().exclude(ticker__in=['BCPO11', 'BFPO11']):
#             self.assertAlmostEqual(CheckpointFII.objects.get(investidor=investidor, ano=2017, cdb_rdb=fii).preco_medio, 
#                                    calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 12, 31), fii.ticker), places=3)
#         # Garantir que o checkpoint do BCPO11 e BFPO11 não foi criado pois não há um ano anterior com quantidade diferente de 0, e
#         #a quantidade atual é 0
#         self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=2017, cdb_rdb=FII.objects.get(ticker='BCPO11')).exists())
#         self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=2017, cdb_rdb=FII.objects.get(ticker='BFPO11')).exists())
#              
#     def test_verificar_preco_medio_por_divisao(self):
#         """Testa cálculos de preço médio por divisão"""
#         geral = Divisao.objects.get(nome='Geral')
#         teste = Divisao.objects.get(nome=u'Divisão de teste')
#          
#         # Testar funções individuais
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 3, 1), 'BAPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 5, 12), 'BAPO11'), Decimal(4500) / 43, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 6, 4), 'BAPO11'), Decimal(4500) / 430, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 11, 20), 'BAPO11'), Decimal(4500) / 430 - Decimal('9.1'), places=3)
#          
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 3, 1), 'BBPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 5, 12), 'BBPO11'), Decimal(43200) / 430, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 6, 4), 'BBPO11'), Decimal(43200) / 43, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 11, 20), 'BBPO11'), Decimal(43200) / 43, places=3)
#          
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 3, 1), 'BCPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 5, 12), 'BCPO11'), Decimal(3900) / 37, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 6, 4), 'BCPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 11, 20), 'BCPO11'), 0, places=3)
#          
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 3, 1), 'BDPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 5, 12), 'BDPO11'), Decimal(27300) / 271, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 6, 4), 'BDPO11'), Decimal(27300 + 3900) / 617, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 11, 20), 'BDPO11'), Decimal(27300 + 3900 + 9400) / 707, places=3)
#          
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(teste, datetime.date(2017, 3, 1), 'BEPO11'), 0, places=3)
#         self.assertAlmostEqual(calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(teste, datetime.date(2017, 5, 12), 'BEPO11'), Decimal(5200) / 50, places=3)
#          
#         # Testar função geral
#         for data in [datetime.date(2017, 3, 1), datetime.date(2017, 5, 12), datetime.date(2017, 6, 4), datetime.date(2017, 11, 20)]:
#             precos_medios = calcular_preco_medio_fiis_ate_dia_por_divisao(geral, data)
#             for ticker in FII.objects.all().values_list('ticker', flat=True):
#                 qtd_individual = calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, data, ticker)
#                 if qtd_individual > 0:
#                     self.assertAlmostEqual(precos_medios[ticker], qtd_individual, places=3)
#                 else:
#                     self.assertNotIn(ticker, precos_medios.keys())
#          
#         # Testar checkpoints
#         self.assertFalse(CheckpointDivisaoFII.objects.filter(divisao=geral, ano=2016).exists())
#         for fii in FII.objects.all().exclude(ticker__in=['BCPO11', 'BEPO11', 'BFPO11']):
#             self.assertAlmostEqual(CheckpointDivisaoFII.objects.get(divisao=geral, ano=2017, cdb_rdb=fii).preco_medio, 
#                                    calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(geral, datetime.date(2017, 12, 31), fii.ticker), places=3)
#         # Garantir que o checkpoint do BCPO11 e BFPO11 não foi criado pois não há um ano anterior com quantidade diferente de 0, e
#         #a quantidade atual é 0
#         self.assertFalse(CheckpointDivisaoFII.objects.filter(divisao=geral, ano=2017, cdb_rdb=FII.objects.get(ticker='BCPO11')).exists())
#         self.assertFalse(CheckpointDivisaoFII.objects.filter(divisao=geral, ano=2017, cdb_rdb=FII.objects.get(ticker='BFPO11')).exists())
#         self.assertAlmostEqual(CheckpointDivisaoFII.objects.get(divisao=teste, ano=2017, cdb_rdb=FII.objects.get(ticker='BEPO11')).preco_medio, 
#                                calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(teste, datetime.date(2017, 12, 31), 'BEPO11'), places=3)
#              
# class PerformanceCheckpointCDB_RDBTestCase(TestCase):
#     def setUp(self):
#         user = User.objects.create(username='test', password='test')
#            
#         cdb_1 = CDB_RDB.objects.create(nome="CDB 1", investidor=user.investidor, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_DI)
#         cdb_3 = CDB_RDB.objects.create(nome="CDB 3", investidor=user.investidor, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_PREFIXADO)
#            
#         HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_1, porcentagem=100)
#         HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_3, porcentagem=10)
#         
#         # Históricos DI e IPCA
#         # Data final é 14/02/2018 mas atualizações só contam até data anterior para manter DI e prefixado pareados
#         data_final = datetime.date(2018, 2, 13)
#         date_list = [data_final - datetime.timedelta(days=x) for x in range(0, (data_final - datetime.date(2012, 1, 1)).days+1)]
#         date_list = [data for data in date_list if data.weekday() < 5 and not verificar_feriado_bovespa(data)]
#         
#         for data in date_list:
#             HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(11.13))   
#         
#         # Gerar operações mensalmente de 2012 a 2017
#         for ano in range(2012, 2018):
#             for mes in range(1, 13):
#                 compra_1 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=2000)
#                 compra_2 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=1000)
#                 compra_5 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=2000)
#                 compra_6 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=1000)
#                 compra_7 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=3000)
#                  
#                 # Operações de venda
#                 venda_1 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_1, investidor=user.investidor, tipo_operacao='V', data=datetime.date(ano, mes, 15), quantidade=500)
#                 OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra_2, operacao_venda=venda_1)
#                 venda_3 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='V', data=datetime.date(ano, mes, 15), quantidade=500)
#                 OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra_6, operacao_venda=venda_3)
#                 venda_4 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_3, investidor=user.investidor, tipo_operacao='V', data=datetime.date(ano, mes, 15), quantidade=3000)
#                 OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra_7, operacao_venda=venda_4)
#         
#     def calcular_valor_cdb_rdb_ate_dia_antigo(self, investidor, dia=datetime.date.today(), considerar_impostos=False):
#         """ 
#         Calcula o valor dos CDB/RDB no dia determinado
#         Parâmetros: Investidor
#                     Data final
#                     Levar em consideração impostos (IOF e IR)
#         Retorno: Valor de cada CDB/RDB na data escolhida {id_letra: valor_na_data, }
#         """
#         operacoes = self.buscar_operacoes_vigentes_ate_data_antigo(investidor, dia)
#         
#         cdb_rdb = {}
#         # Buscar taxas dos dias
#         historico = HistoricoTaxaDI.objects.all()
#         for operacao in operacoes:
#             # TODO consertar verificação de todas vendidas
#             operacao.quantidade = operacao.qtd_disponivel_venda
#     
#             if operacao.cdb_rdb.id not in cdb_rdb.keys():
#                 cdb_rdb[operacao.cdb_rdb.id] = 0
#             
#             if operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
#                 # DI
#                 # Definir período do histórico relevante para a operação
#                 historico_utilizado = historico.filter(data__range=[operacao.data, dia]).values('taxa').annotate(qtd_dias=Count('taxa'))
#                 taxas_dos_dias = {}
#                 for taxa_quantidade in historico_utilizado:
#                     taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
#                 
#                 # Calcular
#                 if considerar_impostos:
#                     valor_final = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
#                     cdb_rdb[operacao.cdb_rdb.id] += valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao.quantidade, 
#                                                      (dia - operacao.data).days))
#                 else:
#                     cdb_rdb[operacao.cdb_rdb.id] += calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
#             elif operacao.cdb_rdb.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
#                 # Prefixado
#                 if considerar_impostos:
#                     valor_final = calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), qtd_dias_uteis_no_periodo(operacao.data, dia)) \
#                         .quantize(Decimal('.01'), ROUND_DOWN)
#                     cdb_rdb[operacao.cdb_rdb.id] += valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao.quantidade, 
#                                                      (dia - operacao.data).days))
#                 else:
#                     cdb_rdb[operacao.cdb_rdb.id] += calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), 
#                                                                                                       qtd_dias_uteis_no_periodo(operacao.data, dia)).quantize(Decimal('.01'), ROUND_DOWN)
#         
#         return cdb_rdb
#     
#     def buscar_operacoes_vigentes_ate_data_antigo(self, investidor, data=datetime.date.today()):
#         operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor, tipo_operacao='C', data__lte=data).exclude(data__isnull=True) \
#             .annotate(qtd_vendida=Coalesce(Sum(Case(When(operacao_compra__operacao_venda__data__lte=data, then='operacao_compra__operacao_venda__quantidade'))), 0)).exclude(quantidade=F('qtd_vendida')) \
#             .annotate(qtd_disponivel_venda=(F('quantidade') - F('qtd_vendida')))
#     
#         return operacoes
#        
#     def test_verificar_performance(self):
#         """Verifica se a forma de calcular quantidades a partir de checkpoints melhora a performance"""
#         investidor = Investidor.objects.get(user__username='test')
#            
#         data_final = datetime.date(2018, 1, 1)
#         # Verificar no ano de 2017 após eventos
#         inicio = datetime.datetime.now()
#         qtd_antigo = self.calcular_valor_cdb_rdb_ate_dia_antigo(investidor, data_final)
#         fim_antigo = datetime.datetime.now() - inicio
#                
#         inicio = datetime.datetime.now()
#         qtd_novo = calcular_valor_cdb_rdb_ate_dia(investidor, data_final)
#         fim_novo = datetime.datetime.now() - inicio
#            
# #         print '%s: ' % (data_final.year), fim_antigo, fim_novo, (Decimal((fim_novo - fim_antigo).total_seconds() / fim_antigo.total_seconds() * 100)).quantize(Decimal('0.01'))
#            
#         self.assertDictEqual(qtd_antigo, qtd_novo)
#         self.assertTrue(fim_novo < fim_antigo)
         
# class AtualizarCheckpointAnualTestCase(TestCase):
#     def setUp(self):
#         user = User.objects.create(username='test', password='test')
#         user.investidor.data_ultimo_acesso = datetime.date(2016, 5, 11)
#         user.investidor.save()
#          
#         empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
#         fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
#          
#         OperacaoCDB_RDB.objects.create(cdb_rdb=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2016, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
#         # Gera operação no futuro para depois trazer para ano atual
#         OperacaoCDB_RDB.objects.create(cdb_rdb=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(datetime.date.today().year+1, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
#         # Apagar checkpoint gerado
#         CheckpointFII.objects.filter(ano__gt=datetime.date.today().year).delete()
#           
#     def test_atualizacao_ao_logar_prox_ano(self):
#         """Verifica se é feita atualização ao logar em pŕoximo ano"""
#         investidor = Investidor.objects.get(user__username='test')
#         fii = FII.objects.get(ticker='BAPO11')
#          
#         # Verifica que existe checkpoint até ano atual
#         ano_atual = datetime.date.today().year
#         self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).exists())
#          
#         # Apaga ano atual
#         CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).delete()
#         self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).exists())
#          
#         # Chamar o teste do middleware de ultimo acesso
#         if investidor.data_ultimo_acesso.year < ano_atual:
#             atualizar_checkpoints(investidor)
#  
#         # Verifica se ao logar foi gerado novamente checkpoint
#         self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).exists())
#          
#     def test_atualizacao_ao_logar_apos_varios_anos(self):
#         """Verifica se é feita atualização ao logar depois de vários anos"""
#         investidor = Investidor.objects.get(user__username='test')
#         fii = FII.objects.get(ticker='BAPO11')
#          
#         # Verifica que existe checkpoint até ano atual
#         ano_atual = datetime.date.today().year
#         self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).exists())
#          
#         # Apaga ano atual e ano passado
#         CheckpointFII.objects.filter(investidor=investidor, ano__gte=ano_atual-1, cdb_rdb=fii).delete()
#         self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).exists())
#         self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual-1, cdb_rdb=fii).exists())
#          
#         # Chamar o teste do middleware de ultimo acesso
#         if investidor.data_ultimo_acesso.year < ano_atual:
#             atualizar_checkpoints(investidor)
#  
#         # Verifica se ao logar foi gerado novamente checkpoint
#         self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).exists())
#         self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual-1, cdb_rdb=fii).exists())
#          
#     def test_nao_atualizar_caso_mesmo_ano(self):
#         """Verificar se em caso de já haver checkpoint no ano, função não altera nada"""
#         investidor = Investidor.objects.get(user__username='test')
#         fii = FII.objects.get(ticker='BAPO11')
#         checkpoint = CheckpointFII.objects.get(investidor=investidor, ano=datetime.date.today().year, cdb_rdb=fii)
#          
#         # Chamar atualizar ano
#         atualizar_checkpoints(investidor)
#          
#         # Verificar se houve alteração no checkpoint
#         self.assertEqual(checkpoint, CheckpointFII.objects.get(investidor=investidor, ano=datetime.date.today().year, cdb_rdb=fii))
#          
#     def test_verificar_checkpoint_operacao_ano_futuro(self):
#         """Verificar se checkpoint de operação no futuro funciona ao chegar no ano da operação"""
#         investidor = Investidor.objects.get(user__username='test')
#         fii = FII.objects.get(ticker='BAPO11')
#          
#         # Apagar ano atual para fingir que acabamos de chegar a esse ano
#         ano_atual = datetime.date.today().year
#         self.assertTrue(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).exists())
#         CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).delete()
#         self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, ano=ano_atual, cdb_rdb=fii).exists())
#          
#         # Trazer operação do futuro para ano atual
#         OperacaoCDB_RDB.objects.filter(investidor=investidor, data__gt=datetime.date.today()).update(data=datetime.date.today())
#          
#         # Atualizar da forma como é feito pelo middleware de ultimo acesso
#         if investidor.data_ultimo_acesso.year < ano_atual:
#             atualizar_checkpoints(investidor)
#              
#         # Verificar se quantidade de cotas está correta
#         self.assertEqual(CheckpointFII.objects.get(investidor=investidor, ano=ano_atual, cdb_rdb=fii).quantidade, 86)
#          
#     def test_checkpoints_venda_cotas(self):
#         """Verificar se checkpoints são apagados quando cota é vendida"""
#         investidor = Investidor.objects.get(user__username='test')
#         fii = FII.objects.get(ticker='BAPO11')
#          
#         ano_atual = datetime.date.today().year
#         OperacaoCDB_RDB.objects.create(cdb_rdb=fii, investidor=investidor, tipo_operacao='V', data=datetime.date(2016, 5, 11), quantidade=43, preco_unitario=Decimal('100'), corretagem=100, emolumentos=100)
#         self.assertFalse(CheckpointFII.objects.filter(investidor=investidor, cdb_rdb=fii).exists())