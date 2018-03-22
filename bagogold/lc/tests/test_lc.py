# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLetraCambio, Divisao
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.lci_lca.utils import \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa, \
    qtd_dias_uteis_no_periodo, calcular_iof_regressivo, \
    calcular_imposto_renda_longo_prazo
from bagogold.lc.forms import HistoricoVencimentoCDB_RDBForm, \
    HistoricoCarenciaCDB_RDBForm
from bagogold.lc.models import CDB_RDB, HistoricoPorcentagemCDB_RDB, \
    OperacaoCDB_RDB, OperacaoVendaCDB_RDB, HistoricoCarenciaCDB_RDB, \
    HistoricoVencimentoCDB_RDB
from bagogold.lc.utils import calcular_valor_lc_ate_dia, \
    buscar_operacoes_vigentes_ate_data, calcular_valor_lc_ate_dia_por_divisao, \
    calcular_valor_venda_lc, calcular_valor_operacao_lc_ate_dia
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class ValorLetraCambioAteDiaTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # Usar data do dia 27/10/2016
        data_atual = datetime.date(2016, 11, 10)
        
        # Letra de Câmbio
        lc = LetraCambio.objects.create(nome="LC Teste", investidor=user.investidor, tipo='R', tipo_rendimento=LetraCambio.CDB_RDB_DI)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc, porcentagem=Decimal(110))
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, vencimento=2000)
        OperacaoLetraCambio.objects.create(quantidade=Decimal(3000), data=datetime.date(2016, 10, 14), tipo_operacao='C', \
                                            lc=lc, investidor=user.investidor)
        
        # Histórico
        date_list = [data_atual - datetime.timedelta(days=x) for x in range(0, (data_atual - datetime.date(2016, 10, 14)).days+1)]
        date_list = [data for data in date_list if data.weekday() < 5 and not verificar_feriado_bovespa(data)]
        
        for data in date_list:
            if data >= datetime.date(2016, 10, 20):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(13.88))
            else:
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(14.13))
            
    def test_valor_lc_ate_dia(self):
        """Testar valores das operações no dia 10/11/2016, permitindo erro de até 1 centavo"""
        investidor = User.objects.get(username='tester').investidor
        
        valor_lc = calcular_valor_lc_ate_dia(investidor, datetime.date(2016, 11, 10)).values()
        self.assertAlmostEqual(valor_lc[0], Decimal('3032.63'), delta=0.01)
        self.assertEqual(valor_lc[0], calcular_valor_operacao_lc_ate_dia(OperacaoLetraCambio.objects.get(investidor=investidor, tipo_operacao='C'), datetime.date(2016, 11, 10)))
        
    def test_valor_liquido_lc_ate_dia(self):
        """Testar valores líquidos das operações no dia 10/11/2016, permitindo erro de até 1 centavo"""
        valor_lc = calcular_valor_lc_ate_dia(User.objects.get(username='tester').investidor, datetime.date(2016, 11, 10), True).values()
        iof = Decimal('32.63') * calcular_iof_regressivo((datetime.date(2016, 11, 10) - datetime.date(2016, 10, 14)).days)
        ir = calcular_imposto_renda_longo_prazo(Decimal('32.63') - iof, (datetime.date(2016, 11, 10) - datetime.date(2016, 10, 14)).days)
        self.assertAlmostEqual(valor_lc[0], Decimal('3032.63') - iof - ir, delta=0.01)
        
    def test_valor_venda_lc_no_dia(self):
        """Testar valor da operação de venda no dia 10/11/2016, permitindo erro de até 1 centavo"""
        lc = LetraCambio.objects.get(nome="LC Teste")
        investidor = Investidor.objects.get(user__username='tester')
        
        operacao_venda = OperacaoLetraCambio.objects.create(quantidade=Decimal(3000), data=datetime.date(2016, 11, 10), tipo_operacao='V', \
                                            lc=lc, investidor=investidor)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=OperacaoLetraCambio.objects.get(investidor=investidor, lc=lc, tipo_operacao='C'), operacao_venda=operacao_venda)
        self.assertAlmostEqual(calcular_valor_venda_lc(operacao_venda), Decimal('3030.91'), delta=0.01)

class CalcularValorLetraCambioPrefixadoTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # CDB
        lc = LetraCambio.objects.create(nome="LC Teste", investidor=user.investidor, tipo='C', tipo_rendimento=LetraCambio.CDB_RDB_PREFIXADO)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc, porcentagem=Decimal('11.44'))
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, vencimento=2000)
        OperacaoLetraCambio.objects.create(quantidade=Decimal(2000), data=datetime.date(2017, 5, 23), tipo_operacao='C', \
                                            lc=lc, investidor=user.investidor)
        
    def test_valor_prefixado_no_dia(self):
        """Testar valor do CDB no dia 16/06/2017, permitindo erro de até 1 centavo"""
        qtd_dias = qtd_dias_uteis_no_periodo(datetime.date(2017, 5, 23), datetime.date(2017, 6, 16))
        operacao = OperacaoLetraCambio.objects.get(lc=LetraCambio.objects.get(nome="LC Teste"))
        valor = calcular_valor_atualizado_com_taxa_prefixado(operacao.quantidade, operacao.porcentagem(), qtd_dias)
        self.assertAlmostEqual(valor, Decimal('2014.67'), delta=0.01)
        self.assertEqual(valor.quantize(Decimal('.01'), ROUND_DOWN), calcular_valor_operacao_lc_ate_dia(operacao, datetime.date(2017, 6, 15)))
        
    def test_valor_venda_lc_no_dia(self):
        """Testar valor da operação de venda no dia 16/06/2017, permitindo erro de até 1 centavo"""
        lc = LetraCambio.objects.get(nome="LC Teste")
        investidor = Investidor.objects.get(user__username='tester')
        
        operacao_venda = OperacaoLetraCambio.objects.create(quantidade=Decimal(2000), data=datetime.date(2017, 6, 16), tipo_operacao='V', \
                                            lc=lc, investidor=investidor)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=OperacaoLetraCambio.objects.get(investidor=investidor, lc=lc, tipo_operacao='C'), operacao_venda=operacao_venda)
        self.assertAlmostEqual(calcular_valor_venda_lc(operacao_venda), Decimal('2014.67'), delta=0.01)
        
class CalcularQuantidadesLetraCambioTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # CDB
        lc = LetraCambio.objects.create(nome='LC Teste', investidor=user.investidor, tipo='C', tipo_rendimento=LetraCambio.CDB_RDB_DI)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc, porcentagem=Decimal(110))
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, vencimento=2000)
        
        # Operações
        operacao_1 = OperacaoLetraCambio.objects.create(quantidade=Decimal(2000), data=datetime.date(2017, 1, 23), tipo_operacao='C', \
                                            lc=lc, investidor=user.investidor)
        operacao_2 = OperacaoLetraCambio.objects.create(quantidade=Decimal(1000), data=datetime.date(2017, 2, 23), tipo_operacao='C', \
                                            lc=lc, investidor=user.investidor)
        operacao_3 = OperacaoLetraCambio.objects.create(quantidade=Decimal(1000), data=datetime.date(2017, 3, 23), tipo_operacao='V', \
                                            lc=lc, investidor=user.investidor)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=operacao_2, operacao_venda=operacao_3)
        operacao_4 = OperacaoLetraCambio.objects.create(quantidade=Decimal(3000), data=datetime.date(2017, 3, 23), tipo_operacao='C', \
                                            lc=lc, investidor=user.investidor)
        operacao_5 = OperacaoLetraCambio.objects.create(quantidade=Decimal(1000), data=datetime.date(2017, 5, 23), tipo_operacao='V', \
                                            lc=lc, investidor=user.investidor)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=operacao_4, operacao_venda=operacao_5)
        
        # Divisões
        divisao_1 = Divisao.objects.create(nome=u'Divisão 1', investidor=user.investidor)
        divisao_operacao_1 = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_1, operacao=operacao_1, quantidade=operacao_1.quantidade)
        divisao_operacao_2 = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_1, operacao=operacao_2, quantidade=operacao_2.quantidade)
        divisao_operacao_3 = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_1, operacao=operacao_3, quantidade=operacao_3.quantidade)
        divisao_operacao_4 = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_1, operacao=operacao_4, quantidade=Decimal(2000))
        divisao_operacao_5 = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_1, operacao=operacao_5, quantidade=Decimal(500))
        
        divisao_2 = Divisao.objects.create(nome=u'Divisão 2', investidor=user.investidor)
        divisao_operacao_6 = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_2, operacao=operacao_4, quantidade=Decimal(1000))
        divisao_operacao_7 = DivisaoOperacaoLetraCambio.objects.create(divisao=divisao_2, operacao=operacao_5, quantidade=Decimal(500))
        
    def test_buscar_qtd_vigente_ao_fim_das_operacoes(self):
        """Testa a quantidade vigente de CDB/RDB ao fim das operações"""
        operacoes_vigentes = buscar_operacoes_vigentes_ate_data(Investidor.objects.get(user__username='tester'), datetime.date(2017, 5, 25))
        self.assertEqual(len(operacoes_vigentes), 2)
        self.assertIn(OperacaoLetraCambio.objects.get(id=1), operacoes_vigentes)
        self.assertEqual(operacoes_vigentes.get(id=1).qtd_disponivel_venda, Decimal(2000))
        self.assertIn(OperacaoLetraCambio.objects.get(id=4), operacoes_vigentes)
        self.assertEqual(operacoes_vigentes.get(id=4).qtd_disponivel_venda, Decimal(2000))
        
    def test_verificar_qtds_por_divisao(self):
        """Testa a quantidade em cada divisão"""
        self.assertDictEqual(calcular_valor_lc_ate_dia_por_divisao(datetime.date(2017, 6, 13), Divisao.objects.get(nome=u'Divisão 1').id),
                             {LetraCambio.objects.get(nome=u'LC Teste').id: Decimal(3500)})
        self.assertDictEqual(calcular_valor_lc_ate_dia_por_divisao(datetime.date(2017, 6, 13), Divisao.objects.get(nome=u'Divisão 2').id),
                             {LetraCambio.objects.get(nome=u'LC Teste').id: Decimal(500)})
        
        
class FormulariosCarenciaVencimentoTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # CDB
        lc = LetraCambio.objects.create(nome='LC Teste', investidor=user.investidor, tipo='C', tipo_rendimento=LetraCambio.CDB_RDB_DI)
        carencia_inicial = HistoricoCarenciaLetraCambio.objects.create(lc=lc, data=None, carencia=361)
        vencimento_inicial = HistoricoVencimentoLetraCambio.objects.create(lc=lc, data=None, vencimento=400)
    
    # Forms de carência
    def test_form_carencia_valido(self):
        """Testa se formulário de carencia é válido"""
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        form_carencia = HistoricoCarenciaLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertTrue(form_carencia.is_valid())
        carencia = form_carencia.save()
        self.assertEqual(carencia.lc, lc)
        self.assertEqual(carencia.data, datetime.date(2017, 9, 10))
        self.assertEqual(carencia.carencia, 365)
        
    def test_form_carencia_maior_que_vencimento_vigente(self):
        """Testa formulário de carencia onde o vencimento vigente está maior do que o carencia inserida"""
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        form_carencia = HistoricoCarenciaLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'carencia': 410,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertFalse(form_carencia.is_valid())

    def test_form_carencia_maior_que_vencimento_periodo(self):
        """Testa formulário de carencia onde o vencimento no período fica maior do que o carencia inserida"""
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 12), vencimento=300)
        form_carencia = HistoricoCarenciaLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertFalse(form_carencia.is_valid())
        
    def test_form_carencia_periodo_carencia_valido(self):
        """
        Testa formulário de carencia onde o vencimento é testado no período entre o carencia inserida e uma próxima carencia
        sem vencimento no período menor que carencia
        """
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        HistoricoCarenciaLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 20), carencia=300)
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 20), vencimento=300)
        form_carencia = HistoricoCarenciaLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertTrue(form_carencia.is_valid())
        
    def test_form_carencia_periodo_carencia_invalido(self):
        """
        Testa formulário de carencia onde o vencimento é testado no período entre a carencia inserida e uma próxima carencia,
        com vencimento no período menor que carencia
        """
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 15), vencimento=370)
        HistoricoCarenciaLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 20), carencia=360)
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 20), vencimento=720)
        form_carencia = HistoricoCarenciaLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'carencia': 380,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertFalse(form_carencia.is_valid())
    
    # Forms de vencimento
    def test_form_vencimento_valido(self):
        """Testa se formulário de vencimento é válido"""
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        form_vencimento = HistoricoVencimentoLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertTrue(form_vencimento.is_valid())
        vencimento = form_vencimento.save()
        self.assertEqual(vencimento.lc, lc)
        self.assertEqual(vencimento.data, datetime.date(2017, 9, 10))
        self.assertEqual(vencimento.vencimento, 365)
        
    def test_form_vencimento_menor_que_carencia_vigente(self):
        """Testa formulário de vencimento onde a carência vigente está maior do que o vencimento inserido"""
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        form_vencimento = HistoricoVencimentoLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 360,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertFalse(form_vencimento.is_valid())

    def test_form_vencimento_menor_que_carencia_periodo(self):
        """Testa formulário de vencimento onde a carência no período fica maior do que o vencimento inserido"""
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        HistoricoCarenciaLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 12), carencia=720)
        form_vencimento = HistoricoVencimentoLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertFalse(form_vencimento.is_valid())
        
    def test_form_vencimento_periodo_carencia_valido(self):
        """
        Testa formulário de vencimento onde a carência é testada no período entre o vencimento inserido e um próximo vencimento
        sem carência no período maior que vencimento
        """
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 20), vencimento=720)
        HistoricoCarenciaLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 20), carencia=720)
        form_vencimento = HistoricoVencimentoLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertTrue(form_vencimento.is_valid())
        
    def test_form_vencimento_periodo_carencia_invalido(self):
        """
        Testa formulário de vencimento onde a carência é testada no período entre o vencimento inserido e um próximo vencimento,
        com carência no período maior que vencimento
        """
        investidor = User.objects.get(username='tester').investidor
        lc = LetraCambio.objects.get(nome='LC Teste')
        HistoricoCarenciaLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 15), carencia=370)
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 20), vencimento=720)
        HistoricoCarenciaLetraCambio.objects.create(lc=lc, data=datetime.date(2017, 9, 20), carencia=360)
        form_vencimento = HistoricoVencimentoLetraCambioForm({
            'lc': lc,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, lc=lc, initial={'lc': lc.id})
        self.assertFalse(form_vencimento.is_valid())