# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLetraCambio, \
    Divisao, CheckpointDivisaoLetraCambio
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.investidores import atualizar_checkpoints
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa, \
    qtd_dias_uteis_no_periodo
from bagogold.lc.models import LetraCambio, HistoricoPorcentagemLetraCambio, \
    HistoricoVencimentoLetraCambio, OperacaoLetraCambio, OperacaoVendaLetraCambio, \
    CheckpointLetraCambio
from bagogold.lc.utils import calcular_valor_operacao_lc_ate_dia, \
    calcular_valor_lc_ate_dia, calcular_valor_um_lc_ate_dia_por_divisao, \
    calcular_valor_venda_lc
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models.aggregates import Sum
from django.test import TestCase
import datetime
 
class CalcularQuantidadesLetraCambioTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
         
        lc_1 = LetraCambio.objects.create(nome="LC 1", investidor=user.investidor, tipo_rendimento=LetraCambio.LC_DI)
        # TODO regularizar testes de IPCA
        lc_2 = LetraCambio.objects.create(nome="LC 2", investidor=user.investidor, tipo_rendimento=LetraCambio.LC_IPCA)
        lc_3 = LetraCambio.objects.create(nome="LC 3", investidor=user.investidor, tipo_rendimento=LetraCambio.LC_PREFIXADO)
        
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc_1, porcentagem=100)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc_2, porcentagem=5)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc_3, porcentagem=10)
        
        HistoricoVencimentoLetraCambio.objects.create(lc=lc_1, vencimento=1080)
        HistoricoVencimentoLetraCambio.objects.create(lc=lc_2, vencimento=1080)
        HistoricoVencimentoLetraCambio.objects.create(lc=lc_3, vencimento=1080)
         
        # Históricos DI e IPCA
        # Data final é 14/02/2018 mas atualizações só contam até data anterior para manter DI e prefixado pareados
        data_final = datetime.date(2018, 3, 13)
        date_list = [data_final - datetime.timedelta(days=x) for x in range(0, (data_final - datetime.date(2017, 3, 11)).days+1)]
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
            elif data >= datetime.date(2017, 4, 13):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(11.13))
            else:
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(12.13))
        
        # Operações de compra
        compra_1 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=2000)
        compra_2 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=1000)
        compra_3 = OperacaoLetraCambio.objects.create(lc=lc_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=2000)
        compra_4 = OperacaoLetraCambio.objects.create(lc=lc_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=1000)
        compra_5 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=2000)
        compra_6 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=1000)
        compra_7 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=3000)
         
        # Operações de venda
        venda_1 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 6, 15), quantidade=500)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=compra_2, operacao_venda=venda_1)
        venda_2 = OperacaoLetraCambio.objects.create(lc=lc_2, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 6, 15), quantidade=500)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=compra_4, operacao_venda=venda_2)
        venda_3 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 6, 15), quantidade=500)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=compra_6, operacao_venda=venda_3)
        venda_4 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='V', data=datetime.date(2017, 6, 15), quantidade=3000)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=compra_7, operacao_venda=venda_4)
         
        # Criar operação na divisão geral
        divisao_geral = Divisao.objects.get(investidor=user.investidor)
        for operacao in OperacaoLetraCambio.objects.all():
            DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_geral, operacao=operacao, quantidade=operacao.quantidade)
         
        # Operação extra para testes de divisão
        operacao_divisao = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=3000)
        divisao_teste = Divisao.objects.create(investidor=user.investidor, nome=u'Divisão de teste')
        DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_teste, operacao=operacao_divisao, quantidade=2000)
        DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_geral, operacao=operacao_divisao, quantidade=1000)
         
         
    def test_calculo_qtd_lc_por_operacao(self):
        """Calcula quantidade de Letras de Câmbio do usuário individualmente"""
        investidor = Investidor.objects.get(user__username='test')
        lc_1 = LetraCambio.objects.get(nome="LC 1")
        lc_3 = LetraCambio.objects.get(nome="LC 3")
        
        for operacao in OperacaoLetraCambio.objects.filter(investidor=investidor, tipo_operacao='C').exclude(lc=LetraCambio.objects.get(nome="LC 2")):
            if operacao.lc == lc_1:
                data = datetime.date(2017, 5, 11)
                self.assertAlmostEqual(calcular_valor_operacao_lc_ate_dia(operacao, data), operacao.quantidade * Decimal('1.00042'), delta=Decimal('0.01'))
                data = datetime.date(2017, 6, 15)
                self.assertAlmostEqual(calcular_valor_operacao_lc_ate_dia(operacao, data), operacao.qtd_disponivel_venda_na_data(data) \
                                       * Decimal('1.01016557'), delta=Decimal('0.01'))
                data = datetime.date(2018, 2, 13)
                self.assertAlmostEqual(calcular_valor_operacao_lc_ate_dia(operacao, data), operacao.qtd_disponivel_venda_na_data(data) \
                                       * Decimal('1.06363295'), delta=Decimal('0.01'))
            elif operacao.lc == lc_3:
                data = datetime.date(2017, 5, 11)
                self.assertAlmostEqual(calcular_valor_operacao_lc_ate_dia(operacao, data), operacao.quantidade \
                                       * pow((1+Decimal('0.1')), (Decimal(1)/252)), delta=Decimal('0.01'))
                data = datetime.date(2017, 6, 15)
                qtd_dias_uteis = Decimal(qtd_dias_uteis_no_periodo(operacao.data, data))
                self.assertAlmostEqual(calcular_valor_operacao_lc_ate_dia(operacao, data), operacao.qtd_disponivel_venda_na_data(data) \
                                  * pow((1+Decimal('0.1')), (qtd_dias_uteis/252)), delta=Decimal('0.01'))
                data = datetime.date(2018, 2, 13)
                qtd_dias_uteis = Decimal(qtd_dias_uteis_no_periodo(operacao.data, data))
                self.assertAlmostEqual(calcular_valor_operacao_lc_ate_dia(operacao, data), operacao.qtd_disponivel_venda_na_data(data) \
                                  * pow((1+Decimal('0.1')), (qtd_dias_uteis/252)), delta=Decimal('0.01'))
         
    def test_calculo_qtd_lcs(self):
        """Calcula quantidade de Letras de Câmbio do usuário"""
        investidor = Investidor.objects.get(user__username='test')
       
        data = datetime.date(2017, 5, 11)
        lc = calcular_valor_lc_ate_dia(investidor, data)
        for lc_id in lc.keys():
            self.assertEqual(lc[lc_id], sum([calcular_valor_operacao_lc_ate_dia(operacao, data) for operacao in OperacaoLetraCambio.objects.filter(tipo_operacao='C', lc__id=lc_id)]))
       
        data = datetime.date(2017, 6, 15)
        lc = calcular_valor_lc_ate_dia(investidor, data)
        for lc_id in lc.keys():
            self.assertEqual(lc[lc_id], sum([calcular_valor_operacao_lc_ate_dia(operacao, data) for operacao in OperacaoLetraCambio.objects.filter(tipo_operacao='C', lc__id=lc_id)]))
        
        data = datetime.date(2018, 2, 13)
        lc = calcular_valor_lc_ate_dia(investidor, data)
        for lc_id in lc.keys():
            self.assertEqual(lc[lc_id], sum([calcular_valor_operacao_lc_ate_dia(operacao, data) for operacao in OperacaoLetraCambio.objects.filter(tipo_operacao='C', lc__id=lc_id)]))
      
    def test_verificar_qtd_divisao(self):
        """Testa se a quantidade de Letra de Câmbio por divisão está correta"""
        investidor = Investidor.objects.get(user__username='test')
        
        data = datetime.date(2017, 5, 11)
        valor_lc = calcular_valor_lc_ate_dia(investidor, data)
        # Comparar a soma das divisões para cada investimento com o total calculado
        for lc_id in valor_lc.keys():
            lc = LetraCambio.objects.get(id=lc_id)
            self.assertAlmostEqual(valor_lc[lc_id], sum([calcular_valor_um_lc_ate_dia_por_divisao(lc, divisao.id, data) \
                                                             for divisao in Divisao.objects.filter(investidor=investidor)]), delta=Decimal('0.01'))
            
        data = datetime.date(2017, 6, 15)
        valor_lc = calcular_valor_lc_ate_dia(investidor, data)
        # Comparar a soma das divisões para cada investimento com o total calculado
        for lc_id in valor_lc.keys():
            lc = LetraCambio.objects.get(id=lc_id)
            self.assertAlmostEqual(valor_lc[lc_id], sum([calcular_valor_um_lc_ate_dia_por_divisao(lc, divisao.id, data) \
                                                             for divisao in Divisao.objects.filter(investidor=investidor)]), delta=Decimal('0.01'))
            
        data = datetime.date(2018, 2, 13)
        valor_lc = calcular_valor_lc_ate_dia(investidor, data)
        # Comparar a soma das divisões para cada investimento com o total calculado
        for lc_id in valor_lc.keys():
            lc = LetraCambio.objects.get(id=lc_id)
            self.assertAlmostEqual(valor_lc[lc_id], sum([calcular_valor_um_lc_ate_dia_por_divisao(lc, divisao.id, data) \
                                                             for divisao in Divisao.objects.filter(investidor=investidor)]), delta=Decimal('0.01'))
            
        # Verificar checkpoints criados para divisão
        for checkpoint in CheckpointLetraCambio.objects.all():
            self.assertAlmostEqual(checkpoint.qtd_restante, CheckpointDivisaoLetraCambio.objects.filter(ano=checkpoint.ano, divisao_operacao__operacao=checkpoint.operacao) \
                                   .aggregate(total_restante=Sum('qtd_restante'))['total_restante'], delta=Decimal('0.01'))
            
          
    def test_verificar_checkpoints_apagados(self):
        """Testa se checkpoints são apagados caso quantidades de Letras de Câmbio do usuário se tornem zero"""
        investidor = Investidor.objects.get(user__username='test')
        lc = LetraCambio.objects.get(nome='LC 1')
        divisao_geral = Divisao.objects.get(nome='Geral', investidor=investidor)
        
        compra = OperacaoLetraCambio.objects.create(lc=lc, investidor=investidor, tipo_operacao='C', data=datetime.date(2017, 8, 11), quantidade=3000)
        divisao_compra = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_geral, operacao=compra, quantidade=compra.quantidade)
        self.assertTrue(CheckpointLetraCambio.objects.filter(operacao=compra).exists())
        self.assertTrue(CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao=compra).exists())
         
        # Apagar checkpoint por venda
        venda = OperacaoLetraCambio.objects.create(lc=lc, investidor=investidor, tipo_operacao='V', data=datetime.date(2017, 8, 15), quantidade=3000)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=compra, operacao_venda=venda)
        divisao_venda = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_geral, operacao=venda, quantidade=venda.quantidade)
        self.assertFalse(CheckpointLetraCambio.objects.filter(operacao=compra).exists())
        self.assertFalse(CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao=compra).exists())
         
        # Checkpoints devem retornar ao apagar venda
        venda.delete()
        self.assertTrue(CheckpointLetraCambio.objects.filter(operacao=compra).exists())
        self.assertTrue(CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao=compra).exists())
        
        # Checkpoints devem sumir ao apagar compra
        compra_id = compra.id
        self.assertTrue(CheckpointLetraCambio.objects.filter(operacao__id=compra_id).exists())
        self.assertTrue(CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao__id=compra_id).exists())
        compra.delete()
        self.assertFalse(CheckpointLetraCambio.objects.filter(operacao__id=compra_id).exists())
        self.assertFalse(CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao__id=compra_id).exists())
          
    def test_verificar_qtd_atualizada(self):
        """Testa cálculos de quantidade atualizada"""
        investidor = Investidor.objects.get(user__username='test')
        lc_1 = LetraCambio.objects.get(nome="LC 1")
        lc_3 = LetraCambio.objects.get(nome="LC 3")
        
        for operacao in OperacaoLetraCambio.objects.filter(investidor=investidor, tipo_operacao='C').exclude(lc=LetraCambio.objects.get(nome="LC 2")):
            if operacao.lc == lc_1:
                data = datetime.date(2017, 12, 31)
                valor_operacao_fim_2017 = calcular_valor_operacao_lc_ate_dia(operacao, data)
                if valor_operacao_fim_2017 > 0:
                    self.assertAlmostEqual(CheckpointLetraCambio.objects.get(operacao=operacao, ano=2017).qtd_atualizada, 
                                     CheckpointLetraCambio.objects.get(operacao=operacao, ano=2017).qtd_restante * Decimal('1.05552808'),
                                     delta=Decimal('0.01'))
#                     print CheckpointLetraCambio.objects.get(operacao=operacao, ano=2017).qtd_restante, '->', CheckpointLetraCambio.objects.get(operacao=operacao, ano=2017).qtd_atualizada
                    for divisao_operacao in DivisaoOperacaoLetraCambio.objects.filter(operacao=operacao):
                        self.assertAlmostEqual(CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=2017).qtd_atualizada, 
                                               CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=2017).qtd_restante * Decimal('1.05552808'), delta=Decimal('0.01'))
#                         print divisao_operacao.divisao, CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=2017).qtd_restante, '->', \
#                             CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=2017).qtd_atualizada
                else:
                    self.assertFalse(CheckpointLetraCambio.objects.filter(operacao=operacao, ano=2017).exists())
                    self.assertFalse(CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao=operacao, ano=2017).exists())
            elif operacao.lc == lc_3:
                data = datetime.date(2017, 12, 31)
                qtd_dias_uteis = Decimal(qtd_dias_uteis_no_periodo(operacao.data, data))
                valor_operacao_fim_2017 = calcular_valor_operacao_lc_ate_dia(operacao, data)
                if valor_operacao_fim_2017 > 0:
                    self.assertAlmostEqual(CheckpointLetraCambio.objects.get(operacao=operacao, ano=2017).qtd_atualizada, 
                                     CheckpointLetraCambio.objects.get(operacao=operacao, ano=2017).qtd_restante * pow((1+Decimal('0.1')), (qtd_dias_uteis/252)),
                                     delta=Decimal('0.01'))
#                     print CheckpointLetraCambio.objects.get(operacao=operacao, ano=2017).qtd_restante, '->', CheckpointLetraCambio.objects.get(operacao=operacao, ano=2017).qtd_atualizada
                    for divisao_operacao in DivisaoOperacaoLetraCambio.objects.filter(operacao=operacao):
                        self.assertAlmostEqual(CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=2017).qtd_atualizada, 
                                               CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=2017).qtd_restante * pow((1+Decimal('0.1')), (qtd_dias_uteis/252)), 
                                               delta=Decimal('0.01'))
#                         print divisao_operacao.divisao, CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=2017).qtd_restante, '->', \
#                             CheckpointDivisaoLetraCambio.objects.get(divisao_operacao=divisao_operacao, ano=2017).qtd_atualizada
                else:
                    self.assertFalse(CheckpointLetraCambio.objects.filter(operacao=operacao, ano=2017).exists())
                    self.assertFalse(CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao=operacao, ano=2017).exists())
                
    def test_verificar_qtd_atualizada_venda(self):
        """Testa cálculo de valor da venda de Letra de Câmbio utilizando checkpoint"""
        investidor = Investidor.objects.get(user__username='test')
        lc = LetraCambio.objects.create(nome="LC 1", investidor=investidor, tipo_rendimento=LetraCambio.LC_DI)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc, porcentagem=110)
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, vencimento=361)
        
        operacao_compra = OperacaoLetraCambio.objects.create(lc=lc, quantidade=1250, data=datetime.date(2017, 3, 13), investidor=investidor, tipo_operacao='C')
        operacao_venda = OperacaoLetraCambio.objects.create(lc=lc, quantidade=1250, data=datetime.date(2018, 3, 9), investidor=investidor, tipo_operacao='V')
        OperacaoVendaLetraCambio.objects.create(operacao_compra=operacao_compra, operacao_venda=operacao_venda)
        
        self.assertAlmostEqual(Decimal('1349.33'), calcular_valor_venda_lc(operacao_venda, True, True), delta=Decimal('0.01'))
        
        
        
        
        
        
# class PerformanceCheckpointLetraCambioTestCase(TestCase):
#     def setUp(self):
#         user = User.objects.create(username='test', password='test')
#            
#         lc_1 = LetraCambio.objects.create(nome="LC 1", investidor=user.investidor, tipo_rendimento=LetraCambio.LC_DI)
#         lc_3 = LetraCambio.objects.create(nome="LC 3", investidor=user.investidor, tipo_rendimento=LetraCambio.LC_PREFIXADO)
#            
#         HistoricoPorcentagemLetraCambio.objects.create(lc=lc_1, porcentagem=100)
#         HistoricoPorcentagemLetraCambio.objects.create(lc=lc_3, porcentagem=10)
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
#                 compra_1 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=2000)
#                 compra_2 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=1000)
#                 compra_5 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=2000)
#                 compra_6 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=1000)
#                 compra_7 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=3000)
#                  
#                 # Operações de venda
#                 venda_1 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='V', data=datetime.date(ano, mes, 15), quantidade=500)
#                 OperacaoVendaLetraCambio.objects.create(operacao_compra=compra_2, operacao_venda=venda_1)
#                 venda_3 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='V', data=datetime.date(ano, mes, 15), quantidade=500)
#                 OperacaoVendaLetraCambio.objects.create(operacao_compra=compra_6, operacao_venda=venda_3)
#                 venda_4 = OperacaoLetraCambio.objects.create(lc=lc_3, investidor=user.investidor, tipo_operacao='V', data=datetime.date(ano, mes, 15), quantidade=3000)
#                 OperacaoVendaLetraCambio.objects.create(operacao_compra=compra_7, operacao_venda=venda_4)
#         
#     def calcular_valor_lc_ate_dia_antigo(self, investidor, dia=datetime.date.today(), considerar_impostos=False):
#         """ 
#         Calcula o valor das Letras de Câmbio no dia determinado
#         Parâmetros: Investidor
#                     Data final
#                     Levar em consideração impostos (IOF e IR)
#         Retorno: Valor de cada Letra de Câmbio na data escolhida {id_letra: valor_na_data, }
#         """
#         operacoes = self.buscar_operacoes_vigentes_ate_data_antigo(investidor, dia)
#         
#         lc = {}
#         # Buscar taxas dos dias
#         historico = HistoricoTaxaDI.objects.all()
#         for operacao in operacoes:
#             # TODO consertar verificação de todas vendidas
#             operacao.quantidade = operacao.qtd_disponivel_venda
#     
#             if operacao.lc.id not in lc.keys():
#                 lc[operacao.lc.id] = 0
#             
#             if operacao.lc.tipo_rendimento == LetraCambio.LC_DI:
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
#                     lc[operacao.lc.id] += valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao.quantidade, 
#                                                      (dia - operacao.data).days))
#                 else:
#                     lc[operacao.lc.id] += calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.quantidade, operacao.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN)
#             elif operacao.lc.tipo_rendimento == LetraCambio.LC_PREFIXADO:
#                 # Prefixado
#                 if considerar_impostos:
#                     valor_final = calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), qtd_dias_uteis_no_periodo(operacao.data, dia)) \
#                         .quantize(Decimal('.01'), ROUND_DOWN)
#                     lc[operacao.lc.id] += valor_final - sum(calcular_iof_e_ir_longo_prazo(valor_final - operacao.quantidade, 
#                                                      (dia - operacao.data).days))
#                 else:
#                     lc[operacao.lc.id] += calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), 
#                                                                                                       qtd_dias_uteis_no_periodo(operacao.data, dia)).quantize(Decimal('.01'), ROUND_DOWN)
#         
#         return lc
#     
#     def buscar_operacoes_vigentes_ate_data_antigo(self, investidor, data=datetime.date.today()):
#         operacoes = OperacaoLetraCambio.objects.filter(investidor=investidor, tipo_operacao='C', data__lte=data).exclude(data__isnull=True) \
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
#         qtd_antigo = self.calcular_valor_lc_ate_dia_antigo(investidor, data_final)
#         fim_antigo = datetime.datetime.now() - inicio
#                
#         inicio = datetime.datetime.now()
#         qtd_novo = calcular_valor_lc_ate_dia(investidor, data_final)
#         fim_novo = datetime.datetime.now() - inicio
#            
# #         print '%s: ' % (data_final.year), fim_antigo, fim_novo, (Decimal((fim_novo - fim_antigo).total_seconds() / fim_antigo.total_seconds() * 100)).quantize(Decimal('0.01'))
#            
#         self.assertDictEqual(qtd_antigo, qtd_novo)
#         self.assertTrue(fim_novo < fim_antigo)
         
class AtualizarCheckpointAnualTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
        user.investidor.data_ultimo_acesso = datetime.date(2016, 5, 11)
        user.investidor.save()
          
        lc_1 = LetraCambio.objects.create(nome="LC 1", investidor=user.investidor, tipo_rendimento=LetraCambio.LC_DI)
        
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc_1, porcentagem=100)
        HistoricoVencimentoLetraCambio.objects.create(lc=lc_1, vencimento=1080)
         
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
          
        OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2016, 5, 11), quantidade=2000)
        # Gera operação no futuro para depois trazer para ano atual
        OperacaoLetraCambio.objects.create(lc=lc_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(datetime.date.today().year+1, 5, 11), quantidade=2000)
        
        # Apagar checkpoint gerado
        CheckpointLetraCambio.objects.filter(ano__gt=datetime.date.today().year).delete()
           
    def test_atualizacao_ao_logar_prox_ano(self):
        """Verifica se é feita atualização ao logar em pŕoximo ano"""
        investidor = Investidor.objects.get(user__username='test')
        compra = OperacaoLetraCambio.objects.get(investidor=investidor, data=datetime.date(2016, 5, 11))
          
        # Verifica que existe checkpoint até ano atual
        ano_atual = datetime.date.today().year
        self.assertTrue(CheckpointLetraCambio.objects.filter(ano=ano_atual, operacao=compra).exists())
          
        # Apaga ano atual
        CheckpointLetraCambio.objects.filter(ano=ano_atual, operacao=compra).delete()
        self.assertFalse(CheckpointLetraCambio.objects.filter(ano=ano_atual, operacao=compra).exists())
          
        # Chamar o teste do middleware de ultimo acesso
        if investidor.data_ultimo_acesso.year < ano_atual:
            atualizar_checkpoints(investidor)
  
        # Verifica se ao logar foi gerado novamente checkpoint
        self.assertTrue(CheckpointLetraCambio.objects.filter(ano=ano_atual, operacao=compra).exists())
          
    def test_atualizacao_ao_logar_apos_varios_anos(self):
        """Verifica se é feita atualização ao logar depois de vários anos"""
        investidor = Investidor.objects.get(user__username='test')
        compra = OperacaoLetraCambio.objects.get(investidor=investidor, data=datetime.date(2016, 5, 11))
          
        # Verifica que existe checkpoint até ano atual
        ano_atual = datetime.date.today().year
        self.assertTrue(CheckpointLetraCambio.objects.filter(ano=ano_atual, operacao=compra).exists())
          
        # Apaga ano atual e ano passado
        CheckpointLetraCambio.objects.filter(ano__gte=ano_atual-1, operacao=compra).delete()
        self.assertFalse(CheckpointLetraCambio.objects.filter(ano=ano_atual, operacao=compra).exists())
        self.assertFalse(CheckpointLetraCambio.objects.filter(ano=ano_atual-1, operacao=compra).exists())
          
        # Chamar o teste do middleware de ultimo acesso
        if investidor.data_ultimo_acesso.year < ano_atual:
            atualizar_checkpoints(investidor)
  
        # Verifica se ao logar foi gerado novamente checkpoint
        self.assertTrue(CheckpointLetraCambio.objects.filter(ano=ano_atual, operacao=compra).exists())
        self.assertTrue(CheckpointLetraCambio.objects.filter(ano=ano_atual-1, operacao=compra).exists())
          
    def test_nao_atualizar_caso_mesmo_ano(self):
        """Verificar se em caso de já haver checkpoint no ano, função não altera nada"""
        investidor = Investidor.objects.get(user__username='test')
        compra = OperacaoLetraCambio.objects.get(data=datetime.date(2016, 5, 11))
        checkpoint = CheckpointLetraCambio.objects.get(ano=datetime.date.today().year, operacao=compra)
          
        # Chamar atualizar ano
        atualizar_checkpoints(investidor)
          
        # Verificar se houve alteração no checkpoint
        self.assertEqual(checkpoint, CheckpointLetraCambio.objects.get(ano=datetime.date.today().year, operacao=compra))
          
    def test_checkpoints_venda(self):
        """Verificar se checkpoints são apagados quando Letra de Câmbio é vendida"""
        investidor = Investidor.objects.get(user__username='test')
        compra = OperacaoLetraCambio.objects.get(investidor=investidor, data=datetime.date(2016, 5, 11))
          
        ano_atual = datetime.date.today().year
        venda = OperacaoLetraCambio.objects.create(lc=compra.lc, tipo_operacao='V', data=datetime.date(2016, 6, 15), quantidade=2000, investidor=investidor)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=compra, operacao_venda=venda)
        self.assertFalse(CheckpointLetraCambio.objects.filter(operacao=compra).exists())