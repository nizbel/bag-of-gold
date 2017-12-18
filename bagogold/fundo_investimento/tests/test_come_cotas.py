# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.fundo_investimento.models import Administrador, FundoInvestimento, \
    OperacaoFundoInvestimento, HistoricoValorCotas
from bagogold.fundo_investimento.utils import \
    calcular_valor_fundos_investimento_ate_dia, calcular_qtd_cotas_ate_dia
from decimal import Decimal, ROUND_FLOOR
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class ComeCotasTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        administrador = Administrador.objects.create(nome='Administrador', cnpj='11.111.111/0001-99')
        
        fundo_1 = FundoInvestimento.objects.create(nome='Claritas 1', cnpj='00.000.000/0000-01', administrador=administrador, data_constituicao=datetime.date(2013, 2, 1),
                                                   situacao=FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL, tipo_prazo=FundoInvestimento.PRAZO_LONGO, classe=FundoInvestimento.CLASSE_FUNDO_MULTIMERCADO,
                                                   exclusivo_qualificados=False, ultimo_registro=datetime.date(2017, 6, 14))

        # Operações
        OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_1, tipo_operacao='C', data=datetime.date(2016, 12, 1), quantidade=('434.745626964385'), 
                                                 valor=Decimal(1000), investidor=user.investidor)
        OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_1, tipo_operacao='C', data=datetime.date(2017, 4, 24), quantidade=('2224.135216012990'), 
                                                 valor=Decimal('5402.74'), investidor=user.investidor)
        OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_1, tipo_operacao='C', data=datetime.date(2017, 5, 2), quantidade=('1642.748832319756'), 
                                                 valor=Decimal(4000), investidor=user.investidor)
        OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_1, tipo_operacao='C', data=datetime.date(2017, 7, 21), quantidade=('1201.988926268340'), 
                                                 valor=Decimal(3000), investidor=user.investidor)
        OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_1, tipo_operacao='C', data=datetime.date(2017, 8, 15), quantidade=('1195.241628334404'), 
                                                 valor=Decimal(3000), investidor=user.investidor)
        OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo_1, tipo_operacao='C', data=datetime.date(2017, 9, 20), quantidade=('473.052823810187'), 
                                                 valor=Decimal(1200), investidor=user.investidor)
        
        HistoricoValorCotas.objects.create(fundo_investimento=fundo_1, data=datetime.date(2017, 5, 30), valor_cota=Decimal('2.45791446'))
        HistoricoValorCotas.objects.create(fundo_investimento=fundo_1, data=datetime.date(2017, 5, 31), valor_cota=Decimal('2.45883695'))
        HistoricoValorCotas.objects.create(fundo_investimento=fundo_1, data=datetime.date(2017, 11, 29), valor_cota=Decimal('2.55930187'))
        HistoricoValorCotas.objects.create(fundo_investimento=fundo_1, data=datetime.date(2017, 11, 30), valor_cota=Decimal('2.55962314'))
        HistoricoValorCotas.objects.create(fundo_investimento=fundo_1, data=datetime.date(2017, 12, 13), valor_cota=Decimal('2.56529144'))
        
        
    def test_valor_em_13_12_2017(self):
        """Testa se em 13/12/2017 o valor das compras está num total de 18.283,74 para 7127,3542775 cotas"""
        soma = 0
        for operacao in OperacaoFundoInvestimento.objects.all():
            print operacao
            operacao.vlr_cota = operacao.valor_cota()
            if operacao.data < datetime.date(2017, 5, 31):
                print operacao.vlr_cota
                ir = ((HistoricoValorCotas.objects.get(data=datetime.date(2017, 5 ,31)).valor_cota - operacao.vlr_cota) * operacao.quantidade * Decimal('0.15')).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
                soma += ir
                operacao.quantidade -= ir / HistoricoValorCotas.objects.get(data=datetime.date(2017, 5, 31)).valor_cota
                operacao.vlr_cota = HistoricoValorCotas.objects.get(data=datetime.date(2017, 5, 31)).valor_cota
            if operacao.data < datetime.date(2017, 11, 30):
                print operacao.vlr_cota
                ir = ((HistoricoValorCotas.objects.get(data=datetime.date(2017, 11 ,30)).valor_cota - operacao.vlr_cota) * operacao.quantidade * Decimal('0.15')).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
                soma += ir
                operacao.quantidade -= ir / HistoricoValorCotas.objects.get(data=datetime.date(2017, 11, 30)).valor_cota
            
            print 'Qtd final', operacao.quantidade
        
        print soma
        # Alcançar esses valores
        # Claritas Inst Fim    13/12/2017    2,56529144    7127,35427765    R$ 0,00    R$ 18.236,80    R$ 18.283,74    
        investidor = Investidor.objects.get(user__username='tester')
        
        self.assertAlmostEqual(sum(calcular_valor_fundos_investimento_ate_dia(investidor, datetime.date(2017, 12, 13)).values()), Decimal('18283.74'), delta=Decimal('0.01'))
        self.assertAlmostEqual(calcular_qtd_cotas_ate_dia(investidor, datetime.date(2017, 12, 13)), Decimal('7127.3542775'), delta=Decimal('0.00000001'))