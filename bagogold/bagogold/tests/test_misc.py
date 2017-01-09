# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, OperacaoAcao, HistoricoAcao, \
    Provento
from bagogold.bagogold.models.cdb_rdb import CDB_RDB, \
    HistoricoPorcentagemCDB_RDB, OperacaoCDB_RDB
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import ProventoFII, FII, OperacaoFII, \
    HistoricoFII
from bagogold.bagogold.models.lc import LetraCredito, \
    HistoricoPorcentagemLetraCredito, OperacaoLetraCredito, HistoricoTaxaDI
from bagogold.bagogold.models.td import Titulo, OperacaoTitulo
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas
from bagogold.bagogold.utils.misc import calcular_iof_regressivo, \
    verificar_feriado_bovespa, qtd_dias_uteis_no_periodo, \
    calcular_domingo_pascoa_no_ano, buscar_valores_diarios_selic, \
    calcular_rendimentos_ate_data, formatar_zeros_a_direita_apos_2_casas_decimais
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.db.models.aggregates import Count
from django.test import TestCase
from random import uniform
import datetime

class IOFTestCase(TestCase):
    # TODO preparar teste com TD
    
#     def setUp(self):
#         Titulo.objects.create(tipo="NTN-B Principal", data_vencimento=datetime.date(2035, 1, 1))
#         OperacaoTitulo.objects.create(preco_unitario=742.28, quantidade=1, data= models.DateField(u'Data', blank=True, null=True)
#     taxa_bvmf = models.DecimalField(u'Taxa BVMF', max_digits=11, decimal_places=2)
#     taxa_custodia = models.DecimalField(u'Taxa do agente de custódia', max_digits=11, decimal_places=2)
#     tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
#     titulo = models.ForeignKey('Titulo')
#     consolidada=True)

    def test_iof_regressivo(self):
        """Valores regressivos segundo a tabela"""
        self.assertEqual(calcular_iof_regressivo(1), 0.96)
        self.assertEqual(calcular_iof_regressivo(15), 0.50)
        self.assertEqual(calcular_iof_regressivo(29), 0.03)

class BuscarTaxaSELICTestCase(TestCase):
    
    def test_nao_buscar_se_periodo_maior_10_anos(self):
        """Testa se há erro caso o período escolhido seja superior a 10 anos"""
        with self.assertRaises(ValueError):
            buscar_valores_diarios_selic(datetime.date(2006,11,16), datetime.date(2016,11,17))
        
    def test_buscar_se_periodo_igual_10_anos(self):
        """Testa se busca funciona para período igual a 10 anos"""
        dados = buscar_valores_diarios_selic(datetime.date(2006,11,17), datetime.date(2016,11,17))
        self.assertTrue(len(dados) == 2513)

    def test_buscar_unico_dia(self):
        """Testa se função retorna resultado para um dia"""
        dados = buscar_valores_diarios_selic(datetime.date(2016,11,17), datetime.date(2016,11,17))
        self.assertTrue(len(dados) == 1)
        self.assertEqual(dados[0], (datetime.date(2016,11,17), Decimal('1.00051660')))
        
class VerificarFeriadoBovespaTestCase(TestCase):
    
    def test_domingo_pascoa(self):
        """Testa as datas do domingo de páscoa para 2014, 2015, 2016, 2017"""
        self.assertEqual(calcular_domingo_pascoa_no_ano(2014), datetime.date(2014, 4, 20))
        self.assertEqual(calcular_domingo_pascoa_no_ano(2015), datetime.date(2015, 4, 5))
        self.assertEqual(calcular_domingo_pascoa_no_ano(2016), datetime.date(2016, 3, 27))
        self.assertEqual(calcular_domingo_pascoa_no_ano(2017), datetime.date(2017, 4, 16))
        
    def test_deve_ser_feriado(self):
        """Testa o Natal"""
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 12, 25)))
        
    def test_nao_deve_ser_feriado(self):
        """Testa dia 12 de Agosto"""
        self.assertFalse(verificar_feriado_bovespa(datetime.date(2016, 8, 12)))
        
    def test_feriados_moveis(self):
        """Testa feriados móveis, carnaval, sexta-feira santa e corpus christi"""
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 2, 9)))
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 3, 25)))
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 5, 26)))
        
class QtdDiasUteisNoPeriodoTestCase(TestCase):
    
    def test_mostrar_erro_data_final_menor_que_inicial(self):
        """Testa se é lançado um ValueError"""
        with self.assertRaises(ValueError):
            qtd_dias_uteis_no_periodo(datetime.date(2016, 5, 5), datetime.date(2016, 5, 1))
            
    def test_quantidade_com_feriados(self):
        """Testa se retorna os 81 dias úteis"""
        self.assertEqual(qtd_dias_uteis_no_periodo(datetime.date(2016, 7, 1), datetime.date(2016, 10, 26)), 81)

class FormatarZerosADireitaApos2CasasTestCase(TestCase):
    
    def test_formatar_para_valor_inteiro(self):
        """Testa formatação em um valor inteiro"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(1), '1.00')
        
    def test_formatar_para_1_casa_decimal_diferente_zero(self):
        """Testa formatação em um número com 2 casas decimais diferentes de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(2.3), '2.30')
        
    def test_formatar_para_2_casas_decimais_iguais_zero(self):
        """Testa formatação em um número com 2 casas decimais diferentes de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(2.00), '2.00')
        
    def test_formatar_para_2_casas_decimais_diferentes_zero(self):
        """Testa formatação em um número com 2 casas decimais diferentes de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(2.34), '2.34')
        
    def test_formatar_para_varias_casas_decimais_iguais_zero(self):
        """Testa formatação em um número com várias casas decimais iguais de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(1.0000000), '1.00')
        
    def test_formatar_para_varias_casas_decimais_diferentes_zero(self):
        """Testa formatação em um número com várias casas decimais diferentes de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(1.4987004), '1.4987004')

class RendimentosTestCase(TestCase):
    
    def setUp(self):
        # Investidor
        user = User.objects.create(username='tester')
        
        # Data do dia
        data_atual = datetime.date(2016, 12, 10)
        
        # Operações
        # Ação
        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
        acao = Acao.objects.create(ticker='TEST3', empresa=empresa)
        operacao_acoes1 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(20), corretagem=Decimal(10), quantidade=200,
                                      data=data_atual - datetime.timedelta(days=0), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        operacao_acoes2 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(20), corretagem=Decimal(5), quantidade=100, 
                                      data=data_atual - datetime.timedelta(days=10), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        operacao_acoes3 = OperacaoAcao.objects.create(investidor=user.investidor, destinacao='B', preco_unitario=Decimal(10), corretagem=Decimal(10), quantidade=300, 
                                      data=data_atual - datetime.timedelta(days=20), acao=acao, tipo_operacao='C', emolumentos=Decimal(0))
        
        # FII
        fii = FII.objects.create(ticker='TEST11')
        operacao_fii1 = OperacaoFII.objects.create(investidor=user.investidor, preco_unitario=Decimal(15), corretagem=Decimal(10), quantidade=400, 
                                   data=data_atual - datetime.timedelta(days=10), tipo_operacao='C', fii=fii, emolumentos=Decimal(0))
        operacao_fii2 = OperacaoFII.objects.create(investidor=user.investidor, preco_unitario=Decimal(100), corretagem=Decimal(10), quantidade=10, 
                                   data=data_atual - datetime.timedelta(days=20), tipo_operacao='C', fii=fii, emolumentos=Decimal(0))
        
        # CDB/RDB
        cdb_rdb = CDB_RDB.objects.create(nome='CDB de teste', investidor=user.investidor, tipo='C', tipo_rendimento='2')
        cdb_rdb_porcentagem_di = HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_rdb, porcentagem=Decimal(90))
        operacao_cdb_rdb1 = OperacaoCDB_RDB.objects.create(investidor=user.investidor, investimento=cdb_rdb, data=data_atual + datetime.timedelta(days=1), tipo_operacao='C',
                                           quantidade=Decimal(1000))
        operacao_cdb_rdb2 = OperacaoCDB_RDB.objects.create(investidor=user.investidor, investimento=cdb_rdb, data=data_atual - datetime.timedelta(days=10), tipo_operacao='C',
                                           quantidade=Decimal(2000))
        
        # Gerar valores históricos
        date_list = [data_atual - datetime.timedelta(days=x) for x in range(0, (data_atual - datetime.date(2016, 10, 1)).days+1)]
        date_list = [data for data in date_list if data.weekday() < 5 and not verificar_feriado_bovespa(data)]
        
        for data in date_list:
            HistoricoAcao.objects.create(data=data, acao=acao, preco_unitario=Decimal(uniform(10, 20)))
            HistoricoFII.objects.create(data=data, fii=fii, preco_unitario=Decimal(uniform(10, 20)))
            HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(uniform(12, 15)))
            
        # Gerar proventos
        provento_acao = Provento.objects.create(valor_unitario=Decimal(1), acao=acao, data_ex=data_atual - datetime.timedelta(days=10), 
                                                  data_pagamento=data_atual - datetime.timedelta(days=1), tipo_provento='D')
        provento_fii = ProventoFII.objects.create(valor_unitario=Decimal(1), fii=fii, data_ex=data_atual - datetime.timedelta(days=10), 
                                               data_pagamento=data_atual - datetime.timedelta(days=1))
    
    def test_deve_trazer_zero_caso_nao_haja_investimentos(self):
        """Testa se método traz resultado 0 caso não haja investimentos"""
        investidor = User.objects.get(username='tester').investidor
        self.assertEqual(Decimal(0), sum(calcular_rendimentos_ate_data(investidor, datetime.date(2016, 1, 1)).values()))
        
    def test_deve_trazer_valor_apenas_de_cdb_rdb(self):
        """Testa se traz valor apenas para CDB/RDB"""
        investidor = User.objects.get(username='tester').investidor
        rendimentos = calcular_rendimentos_ate_data(investidor, datetime.date(2016, 12, 10), 'C')
        self.assertEqual(len(rendimentos.keys()), 1)
        self.assertIn('C', rendimentos.keys())
        
        # Calcular valor esperado
        operacao_cdb_rdb = OperacaoCDB_RDB.objects.all().order_by('data')[0]
        # Definir período do histórico relevante
        historico_utilizado = HistoricoTaxaDI.objects.filter(data__range=[operacao_cdb_rdb.data, datetime.date(2016, 12, 10)]).values('taxa').annotate(qtd_dias=Count('taxa'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_utilizado:
            taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']
        
        # Calcular
        valor_esperado = calcular_valor_atualizado_com_taxas(taxas_dos_dias, operacao_cdb_rdb.quantidade, operacao_cdb_rdb.porcentagem()).quantize(Decimal('.01'), ROUND_DOWN) \
            - operacao_cdb_rdb.quantidade
        self.assertEqual(valor_esperado, rendimentos['C'])
        
    def test_deve_trazer_valor_fii_e_acao(self):
        """Testa se traz valor para FIIs e ações"""
        investidor = User.objects.get(username='tester').investidor
        rendimentos = calcular_rendimentos_ate_data(investidor, datetime.date(2016, 12, 10), 'BF')
        self.assertEqual(len(rendimentos.keys()), 2)
        self.assertIn('B', rendimentos.keys())
        self.assertIn('F', rendimentos.keys())
        self.assertEqual(Decimal('300'), rendimentos['B'])
        self.assertEqual(Decimal('10'), rendimentos['F'])
        self.assertEqual(Decimal('310'), sum(rendimentos.values()))
