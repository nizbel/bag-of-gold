# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII, Divisao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import FII, OperacaoFII, \
    EventoDesdobramentoFII, EventoAgrupamentoFII, EventoIncorporacaoFII
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia, \
    calcular_qtd_fiis_ate_dia_por_ticker, calcular_qtd_fiis_ate_dia_por_divisao
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class CalcularQuantidadesFIITestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
        
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
        fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
        empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='FII BB')
        fii_2 = FII.objects.create(ticker='BBPO11', empresa=empresa_2)
        empresa_3 = Empresa.objects.create(nome='BC', nome_pregao='FII BC')
        fii_3 = FII.objects.create(ticker='BCPO11', empresa=empresa_3)
        empresa_4 = Empresa.objects.create(nome='BD', nome_pregao='FII BD')
        fii_4 = FII.objects.create(ticker='BDPO11', empresa=empresa_4)
        
        # Desdobramento
        OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=43, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        # Agrupamento
        OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=430, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        # Desdobramento + Incorporação
        OperacaoFII.objects.create(fii=fii_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=37, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 5, 11), quantidade=271, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        
        OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 11, 11), quantidade=40, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(2017, 11, 12), quantidade=50, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        
        for operacao in OperacaoFII.objects.all():
            DivisaoOperacaoFII.objects.create(divisao=Divisao.objects.get(investidor=user.investidor), operacao=operacao, quantidade=operacao.quantidade)
        
        EventoDesdobramentoFII.objects.create(fii=fii_1, data=datetime.date(2017, 6, 3), proporcao=10)
        EventoAgrupamentoFII.objects.create(fii=fii_2, data=datetime.date(2017, 6, 3), proporcao=Decimal('0.1'))
        EventoDesdobramentoFII.objects.create(fii=fii_3, data=datetime.date(2017, 6, 3), proporcao=Decimal('9.3674360842'))
        EventoIncorporacaoFII.objects.create(fii=fii_3, data=datetime.date(2017, 6, 3), novo_fii=fii_4)
        
    def test_calculo_qtd_fii_por_ticker(self):
        """Calcula quantidade de FIIs do usuário individualmente"""
        investidor = Investidor.objects.get(user__username='test')
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BAPO11'), 43)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BBPO11'), 430)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BCPO11'), 37)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(2017, 5, 12), 'BDPO11'), 271)
        
    def test_calculo_qtd_fiis(self):
       """Calcula quantidade de FIIs do usuário"""
       self.assertDictEqual(calcular_qtd_fiis_ate_dia(Investidor.objects.get(user__username='test'), datetime.date(2017, 5, 12)), 
                            {'BAPO11': 43, 'BBPO11': 430, 'BCPO11': 37, 'BDPO11': 271}) 
       self.assertDictEqual(calcular_qtd_fiis_ate_dia(Investidor.objects.get(user__username='test'), datetime.date(2017, 11, 13)),
                            {'BAPO11': 430, 'BBPO11': 43, 'BDPO11': 707})
    
    def test_calculo_qtd_apos_agrupamento(self):
        """Verifica se a função que recebe uma quantidade calcula o resultado correto para agrupamento"""
        self.assertEqual(EventoAgrupamentoFII.objects.get(fii=FII.objects.get(ticker='BBPO11')).qtd_apos(100), 10)
        
    def test_calculo_qtd_apos_desdobramento(self):    
        """Verifica se a função que recebe uma quantidade calcula o resultado correto para agrupamento"""
        self.assertEqual(EventoDesdobramentoFII.objects.get(fii=FII.objects.get(ticker='BAPO11')).qtd_apos(100), 1000)
    
    def test_verificar_qtd_apos_agrupamento_fii_1(self):
        """Testa se a quantidade de cotas do usuário está correta após o agrupamento do FII 1"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(Investidor.objects.get(user__username='test'), datetime.date(2017, 6, 4), 'BAPO11'), 430)
    
    def test_verificar_qtd_apos_desdobramento_fii_2(self):
        """Testa se a quantidade de cotas do usuário está correta após o desdobramento do FII 2"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(Investidor.objects.get(user__username='test'), datetime.date(2017, 6, 4), 'BBPO11'), 43)
            
    def test_verificar_qtd_apos_incorporacao(self):
        """Testa se a quantidade de cotas do usuário está correta após o desdobramento e incorporação do FII 3"""
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(Investidor.objects.get(user__username='test'), datetime.date(2017, 6, 4), 'BCPO11'), 0)
        self.assertEqual(calcular_qtd_fiis_ate_dia_por_ticker(Investidor.objects.get(user__username='test'), datetime.date(2017, 6, 4), 'BDPO11'), 617)

    def test_verificar_qtd_divisao_antes_eventos(self):
        """Testa se a quantidade de cotas por divisão está correta antes dos eventos"""
        investidor = Investidor.objects.get(user__username='test')
        self.assertDictEqual(calcular_qtd_fiis_ate_dia_por_divisao(datetime.date(2017, 5, 12), Divisao.objects.get(investidor=investidor).id), 
                             {'BAPO11': 43, 'BBPO11': 430, 'BCPO11': 37, 'BDPO11': 271})
        
    def test_verificar_qtd_divisao_apos_eventos(self):
        """Testa se a quantidade de cotas por divisão está correta após os eventos"""
        investidor = Investidor.objects.get(user__username='test')
        self.assertDictEqual(calcular_qtd_fiis_ate_dia_por_divisao(datetime.date(2017, 11, 13), Divisao.objects.get(investidor=investidor).id), 
                             {'BAPO11': 430, 'BBPO11': 43, 'BDPO11': 707})
                             
class PerformanceCheckpointFIITestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test', password='test')
        
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
        fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
        empresa_2 = Empresa.objects.create(nome='BB', nome_pregao='FII BB')
        fii_2 = FII.objects.create(ticker='BBPO11', empresa=empresa_2)
        empresa_3 = Empresa.objects.create(nome='BC', nome_pregao='FII BC')
        fii_3 = FII.objects.create(ticker='BCPO11', empresa=empresa_3)
        empresa_4 = Empresa.objects.create(nome='BD', nome_pregao='FII BD')
        fii_4 = FII.objects.create(ticker='BDPO11', empresa=empresa_4)
        
        # Gerar operações mensalmente de 2012 a 2016
        for ano in range(2012, 2017):
            for mes in range(1, 13):
                # Desdobramento
                OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
                # Agrupamento
                OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
                # Desdobramento + Incorporação
                OperacaoFII.objects.create(fii=fii_3, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
                OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, tipo_operacao='C', data=datetime.date(ano, mes, 11), quantidade=10, preco_unitario=Decimal('100'), corretagem=0, emolumentos=0)
        
        EventoDesdobramentoFII.objects.create(fii=fii_1, data=datetime.date(2017, 6, 3), proporcao=10)
        EventoAgrupamentoFII.objects.create(fii=fii_2, data=datetime.date(2017, 6, 3), proporcao=Decimal('0.1'))
        EventoDesdobramentoFII.objects.create(fii=fii_3, data=datetime.date(2017, 6, 3), proporcao=10)
        EventoIncorporacaoFII.objects.create(fii=fii_3, data=datetime.date(2017, 6, 3), novo_fii=fii_4)
        
    def calculo_forma_antiga(investidor, dia):
        if not all([verificar_se_existe_evento_para_fii(fii, dia) for fii in FII.objects.filter(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
                                                                                                .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True))]):
            qtd_fii = dict(OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).annotate(ticker=F('fii__ticker')).values('ticker') \
                .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                                    When(tipo_operacao='V', then=F('quantidade')*-1),
                                    output_field=DecimalField()))).values_list('ticker', 'total').exclude(total=0))
    
        else:
            qtd_fii = {}
            for fii in FII.objects.filter(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
                                                                                                .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)):
                qtd_fii_na_data = calculo_forma_antiga_por_ticker(investidor, dia, fii.ticker)
                if qtd_fii_na_data > 0:
                    qtd_fii[fii.ticker] = qtd_fii_na_data
        return qtd_fii
    
    def calculo_forma_antiga_por_ticker(investidor, dia, ticker, ignorar_incorporacao_id=None):
        if not verificar_se_existe_evento_para_fii(FII.objects.get(ticker=ticker), dia):
            qtd_fii = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True) \
                .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                                          When(tipo_operacao='V', then=F('quantidade')*-1),
                                          output_field=DecimalField())))['total'] or 0
        else:
            qtd_fii = 0
        
            operacoes = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True) \
                .annotate(qtd_final=(Case(When(tipo_operacao='C', then=F('quantidade')),
                                          When(tipo_operacao='V', then=F('quantidade')*-1),
                                          output_field=DecimalField()))).annotate(tipo=Value(u'Operação', output_field=CharField()))
                                      
                                      
            # Verificar agrupamentos e desdobramentos
            agrupamentos = EventoAgrupamentoFII.objects.filter(fii__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))

            desdobramentos = EventoDesdobramentoFII.objects.filter(fii__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
        
            incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__ticker=ticker, data__lte=dia) | Q(novo_fii__ticker=ticker, data__lte=dia)).exclude(id=ignorar_incorporacao_id) \
                .annotate(tipo=Value(u'Incorporação', output_field=CharField()))
        
            lista_conjunta = sorted(chain(agrupamentos, desdobramentos, incorporacoes, operacoes), key=attrgetter('data'))
        
            for elemento in lista_conjunta:
                if elemento.tipo == 'Operação':
                    qtd_fii += elemento.qtd_final
                elif elemento.tipo == 'Agrupamento':
                    qtd_fii = elemento.qtd_apos(qtd_fii)
                elif elemento.tipo == 'Desdobramento':
                    qtd_fii = elemento.qtd_apos(qtd_fii)
                elif elemento.tipo == 'Incorporação':
                    if elemento.fii.ticker == ticker:
                        qtd_fii = 0
                    elif elemento.novo_fii.ticker == ticker:
                        qtd_fii += calculo_forma_antiga_por_ticker(investidor, elemento.data, elemento.fii.ticker, elemento.id)
        
        return qtd_fii
    
    def test_verificar_performance(self):
        """Verifica se a forma de calcular quantidades a partir de checkpoints melhora a performance"""
        investidor = Investidor.objects.get(user__username='test')
        
        # TODO apagar essa parte
        # Verificar tempos a cada ano
        for ano in range(2013, 2018):
            inicio = datetime.datetime.now()
            calculo_forma_antiga(investidor, datetime.date(ano, 1, 1)
            fim_antigo = datetime.datetime.now() - inicio
            
            inicio = datetime.datetime.now()
            calcular_qtd_fiis_ate_dia(investidor, datetime.date(ano, 1, 1)
            fim_novo = datetime.datetime.now() - inicio
            
            print '%s: ' % (ano), fim_antigo, fim_novo
        
        # Verificar no ano de 2017 após eventos
        inicio = datetime.datetime.now()
        qtd_antigo = calculo_forma_antiga(investidor, datetime.date(2017, 8, 12)
        fim_antigo = datetime.datetime.now() - inicio
            
        inicio = datetime.datetime.now()
        qtd_novo = calcular_qtd_fiis_ate_dia(investidor, datetime.date(2017, 8, 12)
        fim_novo = datetime.datetime.now() - inicio
            
        self.assertEqual(qtd_antigo, qtd_novo)
        self.assertTrue(fim_novo < fim_antigo)
    