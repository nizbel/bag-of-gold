# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao,\
    DivisaoOperacaoFundoInvestimento
from bagogold.fundo_investimento.models import Administrador, FundoInvestimento, \
    OperacaoFundoInvestimento, HistoricoValorCotas
from bagogold.fundo_investimento.utils import \
    calcular_qtd_cotas_ate_dia_por_fundo, calcular_qtd_cotas_ate_dia, \
    calcular_valor_fundos_investimento_ate_dia,\
    calcular_qtd_cotas_ate_dia_por_divisao
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class QuantidadesFundoInvestimentoTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        administrador = Administrador.objects.create(nome='Administrador', cnpj='11.111.111/0001-99')
        
        fundo_1 = FundoInvestimento.objects.create(nome='Claritas 1', cnpj='00.000.000/0000-01', administrador=administrador, data_constituicao=datetime.date(2013, 2, 1),
                                                   situacao=FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL, tipo_prazo=FundoInvestimento.PRAZO_LONGO, classe=FundoInvestimento.CLASSE_FUNDO_MULTIMERCADO,
                                                   exclusivo_qualificados=False, ultimo_registro=datetime.date(2017, 6, 14))
        
        fundo_2 = FundoInvestimento.objects.create(nome='Claritas 2', cnpj='00.000.000/0000-02', administrador=administrador, data_constituicao=datetime.date(2013, 2, 1),
                                                   situacao=FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL, tipo_prazo=FundoInvestimento.PRAZO_LONGO, classe=FundoInvestimento.CLASSE_FUNDO_MULTIMERCADO,
                                                   exclusivo_qualificados=False, ultimo_registro=datetime.date(2017, 6, 14))
        
        operacao_1 = OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_1, quantidade=Decimal('4291.07590514'), valor=Decimal(10000), investidor=user.investidor,
                                                              tipo_operacao='C', data=datetime.date(2016, 12, 1))
        operacao_2 = OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_2, quantidade=Decimal('600.56'), valor=Decimal(7000), investidor=user.investidor,
                                                              tipo_operacao='C', data=datetime.date(2016, 12, 6))
        operacao_3 = OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_2, quantidade=Decimal('420.9056'), valor=Decimal(5000), investidor=user.investidor,
                                                              tipo_operacao='V', data=datetime.date(2017, 1, 5))
        
        historico_1 = HistoricoValorCotas.objects.create(fundo_investimento=fundo_1, data=datetime.date(2017, 6, 14), valor_cota=Decimal('2.46782541'))
        historico_2 = HistoricoValorCotas.objects.create(fundo_investimento=fundo_2, data=datetime.date(2017, 6, 14), valor_cota=Decimal('12'))
        
        # Adicionar divisões para teste
        divisao_1 = Divisao.objects.create(nome='Divisão 1', investidor=user.investidor)
        DivisaoOperacaoFundoInvestimento.objects.create(operacao=operacao_1, divisao=divisao_1, quantidade=operacao_1.valor)
        
        divisao_2 = Divisao.objects.create(nome='Divisão 2', investidor=user.investidor)
        DivisaoOperacaoFundoInvestimento.objects.create(operacao=operacao_2, divisao=divisao_2, quantidade=operacao_2.valor)
        DivisaoOperacaoFundoInvestimento.objects.create(operacao=operacao_3, divisao=divisao_2, quantidade=operacao_3.valor)
        
        # Claritas Inst Fim     14/06/2017    4.291,07590514    2,46782541    10.589,63    20,09    0,00    10.569,54
        
    def test_qtd_cotas_ate_dia(self):
        """Testa quantidade de cotas até dia"""
        investidor = User.objects.get(username='tester').investidor
        qtd_cotas = calcular_qtd_cotas_ate_dia(investidor, datetime.date(2017, 6, 14))
        id_fundo_1 = FundoInvestimento.objects.get(cnpj='00.000.000/0000-01').id
        id_fundo_2 = FundoInvestimento.objects.get(cnpj='00.000.000/0000-02').id
        self.assertDictEqual(qtd_cotas, {id_fundo_1: Decimal('4291.07590514'), id_fundo_2: Decimal('179.6544')})
        
    def test_qtd_cotas_ate_dia_por_fundo(self):
        """Testa quantidade de cotas até dia por fundo"""
        investidor = User.objects.get(username='tester').investidor
        qtd_cotas = calcular_qtd_cotas_ate_dia_por_fundo(investidor, FundoInvestimento.objects.get(cnpj='00.000.000/0000-01').id, datetime.date(2017, 6, 14))
        self.assertEqual(qtd_cotas, Decimal('4291.07590514'))
        qtd_cotas = calcular_qtd_cotas_ate_dia_por_fundo(investidor, FundoInvestimento.objects.get(cnpj='00.000.000/0000-02').id, datetime.date(2017, 6, 14))
        self.assertEqual(qtd_cotas, Decimal('179.6544'))
        
    def test_qtd_cotas_ate_dia_por_divisao(self):
        """Testa quantidade de cotas até dia por divisão"""
        investidor = User.objects.get(username='tester').investidor
        qtd_cotas = calcular_qtd_cotas_ate_dia_por_divisao(datetime.date(2017, 1, 6), Divisao.objects.get(nome=u'Divisão 1').id)
        self.assertDictEqual(qtd_cotas, {FundoInvestimento.objects.get(nome='Claritas 1').id: Decimal('4291.07590514')})
        qtd_cotas = calcular_qtd_cotas_ate_dia_por_divisao(datetime.date(2017, 1, 6), Divisao.objects.get(nome=u'Divisão 2').id)
        self.assertDictEqual(qtd_cotas, {FundoInvestimento.objects.get(nome='Claritas 2').id: (Decimal('600.56') - Decimal('420.9056'))})
        
    def test_valor_cotas_ate_dia(self):
        """Testa valor das cotas até dia"""
        investidor = User.objects.get(username='tester').investidor
        valor_fundos = calcular_valor_fundos_investimento_ate_dia(investidor, datetime.date(2017, 6, 14))
        self.assertEqual(valor_fundos[FundoInvestimento.objects.get(cnpj='00.000.000/0000-01').id].quantize(Decimal('0.01')), Decimal('10589.63'))