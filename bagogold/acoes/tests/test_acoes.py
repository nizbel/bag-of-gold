# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

import boto3
from django.contrib.auth.models import User
from django.db.models.aggregates import Count
from django.test import TestCase

from bagogold.acoes.models import OperacaoAcao, EventoDesdobramentoAcao,\
    EventoAgrupamentoAcao, EventoBonusAcao, EventoAlteracaoAcao
from bagogold.acoes.models import Acao, Provento, \
    AtualizacaoSelicProvento, HistoricoAcao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic
from bagogold.acoes.utils import verificar_tipo_acao,\
    calcular_qtd_acoes_ate_dia_por_ticker
from bagogold.bagogold.utils.bovespa import buscar_historico_recente_bovespa, \
    processar_historico_recente_bovespa
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa, \
    ultimo_dia_util
from bagogold.bagogold.utils.taxas_indexacao import \
    calcular_valor_atualizado_com_taxas_selic
from bagogold.fii.models import FII, HistoricoFII
from conf.settings_local import AWS_STORAGE_BUCKET_NAME


class VerificarTipoAcaoTestCase(TestCase):
    def test_verificar_tipo_acao(self):
        """Testar se os tipos de ações estão sendo convertidos corretamente"""
        self.assertEqual(verificar_tipo_acao('CMIG3'), 'ON')
        self.assertEqual(verificar_tipo_acao('CMIG4'), 'PN')
        self.assertEqual(verificar_tipo_acao('CMIG5'), 'PNA')
        self.assertEqual(verificar_tipo_acao('CMIG6'), 'PNB')
        self.assertEqual(verificar_tipo_acao('CMIG7'), 'PNC')
        self.assertEqual(verificar_tipo_acao('CMIG8'), 'PND')

class CalcularAtualizacaoProventoSelicTestCase(TestCase):
    def setUp(self):
        empresa = Empresa.objects.create(nome='BB', nome_pregao='BBAS')
        acao = Acao.objects.create(ticker='BBAS3', empresa=empresa)
        provento_1 = Provento.objects.create(data_ex=datetime.date(2017, 3, 2), data_pagamento=datetime.date(2017, 3, 10), acao=acao,
                                           valor_unitario=Decimal('0.13676821544'), tipo_provento='J', oficial_bovespa=True)
        
        provento_2 = Provento.objects.create(data_ex=datetime.date(2017, 3, 2), data_pagamento=datetime.date(2017, 3, 10), acao=acao,
                                           valor_unitario=Decimal('0.02531542157'), tipo_provento='J', oficial_bovespa=True)
        
        data = datetime.date(2016, 6, 1)
        while data < datetime.date(2017, 3, 10):
            # Testar se é a segunda antes do carnaval, também não há taxa selic para essa data
            if data.weekday() < 5 and not verificar_feriado_bovespa(data) and not data == datetime.date(2017, 2, 27):
                if data < datetime.date(2016, 12, 1):
                    taxa = Decimal('1.00052531')
                elif data < datetime.date(2017, 1, 12):
                    taxa = Decimal('1.00050788')
                elif data < datetime.date(2017, 2, 23):
                    taxa = Decimal('1.00048159')
                else:
                    taxa = Decimal('1.00045513')
                HistoricoTaxaSelic.objects.create(data=data, taxa_diaria=taxa)
            data += datetime.timedelta(days=1)
        
    def test_verificar_valor_rendimentos(self):
        """Verifica se os valores alcançados são iguais aos pegos na bovespa"""
        # Provento 1 deve ser próximo a 0,00319717853
        provento = Provento.objects.get(valor_unitario__gt=Decimal('0.1'))
        atualizacao = AtualizacaoSelicProvento(provento=provento)
        atualizacao.data_inicio = datetime.date(2016, 6, 30)
        atualizacao.data_fim = datetime.date(2016, 8, 30)
        historico_selic = HistoricoTaxaSelic.objects.filter(data__range=[atualizacao.data_inicio, atualizacao.data_fim]).values('taxa_diaria').annotate(qtd_dias=Count('taxa_diaria'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_selic:
            taxas_dos_dias[taxa_quantidade['taxa_diaria']] = taxa_quantidade['qtd_dias']
        
        atualizacao.valor_rendimento = calcular_valor_atualizado_com_taxas_selic(taxas_dos_dias, provento.valor_unitario) - atualizacao.provento.valor_unitario
        
        self.assertAlmostEqual(atualizacao.valor_rendimento, Decimal('0.00319717853'), delta=Decimal('0.00000000001'))
        
        # Provento 2 deve ser próximo a 0,00059183169
        provento = Provento.objects.get(valor_unitario__lt=Decimal('0.1'))
        atualizacao = AtualizacaoSelicProvento(provento=provento)
        atualizacao.data_inicio = datetime.date(2016, 12, 30)
        atualizacao.data_fim = datetime.date(2017, 3, 9)
        historico_selic = HistoricoTaxaSelic.objects.filter(data__range=[atualizacao.data_inicio, atualizacao.data_fim]).values('taxa_diaria').annotate(qtd_dias=Count('taxa_diaria'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_selic:
            taxas_dos_dias[taxa_quantidade['taxa_diaria']] = taxa_quantidade['qtd_dias']
        
        atualizacao.valor_rendimento = calcular_valor_atualizado_com_taxas_selic(taxas_dos_dias, provento.valor_unitario) - atualizacao.provento.valor_unitario
        
        self.assertAlmostEqual(atualizacao.valor_rendimento, Decimal('0.00059183169'), delta=Decimal('0.00000000001'))
        
# class BuscarHistoricoRecenteTestCase(TestCase):
#     def setUp(self):
#         empresa_acao = Empresa.objects.create(nome='Banco do Brasil', nome_pregao='BBAS')
#         Acao.objects.create(ticker='BBAS3', tipo='ON', empresa=empresa_acao)
#         
#         empresa_fii = Empresa.objects.create(nome='BBPO', nome_pregao='BBPO')
#         FII.objects.create(ticker='BBPO11', empresa=empresa_fii)
#         
#     def test_buscar_historico_recente_bovespa(self):
#         """Testa se a busca por histórico recente retorna nome de documento"""
#         ultima_data_util = ultimo_dia_util()
#         nome_arq = buscar_historico_recente_bovespa(ultima_data_util)
#         self.assertTrue(nome_arq != None and nome_arq != '')
#         boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_arq)
#         
#     def test_processar_historico_recente_bovespa(self):
#         ultima_data_util = ultimo_dia_util()
#         nome_arq = buscar_historico_recente_bovespa(ultima_data_util)
# #         try:
#         processar_historico_recente_bovespa(boto3.client('s3').get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_arq))
# #         except:
# #             pass
#         boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=nome_arq)
#         self.assertTrue(HistoricoAcao.objects.all().count() > 0)
#         self.assertTrue(HistoricoFII.objects.all().count() > 0)

class EventosAcoesTestCase(TestCase):
    # TODO Testar frações e pagamentos de frações
    @classmethod
    def setUpTestData(cls):
        super(EventosAcoesTestCase, cls).setUpTestData()
        
        usuario = User.objects.create(username='test', password='test')
        cls.investidor = usuario.investidor
        
        # Agrupamento e Desdobramento
        empresa_1 = Empresa.objects.create(nome_pregao='BBAS', nome='Banco do Brasil')
        cls.acao_bbas = Acao.objects.create(ticker='BBAS3', empresa=empresa_1)
        
        # Alteração com desdobramento
        empresa_2 = Empresa.objects.create(nome_pregao='ABEV', nome='Ambev')
        cls.acao_abev = Acao.objects.create(ticker='ABEV3', empresa=empresa_2)
        cls.acao_ambv = Acao.objects.create(ticker='AMBV4', empresa=empresa_2)
        
        # Alteração com agrupamento
        empresa_3 = Empresa.objects.create(nome_pregao='VALE', nome='Vale')
        cls.acao_vale_3 = Acao.objects.create(ticker='VALE3', empresa=empresa_3)
        cls.acao_vale_5 = Acao.objects.create(ticker='VALE5', empresa=empresa_3)
        
        # Alteração e Bônus
        empresa_4 = Empresa.objects.create(nome_pregao='EGIE', nome='Engie')
        cls.acao_tble = Acao.objects.create(ticker='TBLE3', empresa=empresa_4)
        cls.acao_egie = Acao.objects.create(ticker='EGIE3', empresa=empresa_4)
        
        # Operações do investidor
        data_10_dias_atras = datetime.date.today() - datetime.timedelta(days=10)
        data_20_dias_atras = datetime.date.today() - datetime.timedelta(days=20)
        data_30_dias_atras = datetime.date.today() - datetime.timedelta(days=30)
        
        OperacaoAcao.objects.create(acao=cls.acao_bbas, quantidade=100, preco_unitario=30, corretagem=10, emolumentos=1, data=data_30_dias_atras, 
                                    tipo_operacao='C', investidor=cls.investidor)
        OperacaoAcao.objects.create(acao=cls.acao_ambv, quantidade=100, preco_unitario=80, corretagem=10, emolumentos=1, data=data_30_dias_atras, 
                                    tipo_operacao='C', investidor=cls.investidor)
        OperacaoAcao.objects.create(acao=cls.acao_vale_5, quantidade=100, preco_unitario=30, corretagem=10, emolumentos=1, data=data_30_dias_atras, 
                                    tipo_operacao='C', investidor=cls.investidor)
        OperacaoAcao.objects.create(acao=cls.acao_vale_3, quantidade=100, preco_unitario=30, corretagem=10, emolumentos=1, data=data_30_dias_atras, 
                                    tipo_operacao='C', investidor=cls.investidor)
        OperacaoAcao.objects.create(acao=cls.acao_tble, quantidade=100, preco_unitario=30, corretagem=10, emolumentos=1, data=data_30_dias_atras, 
                                    tipo_operacao='C', investidor=cls.investidor)
        
        # Eventos
        # Empresa 1
        EventoAgrupamentoAcao.objects.create(acao=cls.acao_bbas, data=data_20_dias_atras, proporcao=Decimal('0.2'))
        EventoDesdobramentoAcao.objects.create(acao=cls.acao_bbas, data=data_10_dias_atras, proporcao=Decimal('5'))
        
        # Empresa 2
        EventoDesdobramentoAcao.objects.create(acao=cls.acao_ambv, data=data_10_dias_atras, proporcao=Decimal('5'))
        EventoAlteracaoAcao.objects.create(acao=cls.acao_ambv, nova_acao=cls.acao_abev, data=data_10_dias_atras)
        
        # Empresa 3
        EventoAgrupamentoAcao.objects.create(acao=cls.acao_vale_5, data=data_10_dias_atras, proporcao=Decimal('0.9342'))
        EventoAlteracaoAcao.objects.create(acao=cls.acao_vale_5, nova_acao=cls.acao_vale_3, data=data_10_dias_atras)
        
        # Empresa 4
        EventoAlteracaoAcao.objects.create(acao=cls.acao_tble, nova_acao=cls.acao_egie, data=data_20_dias_atras)
        EventoBonusAcao.objects.create(acao=cls.acao_egie, data=data_10_dias_atras, proporcao=Decimal('0.25'))
        
    def test_qtd_acao_empresa_1(self):
        """Testa quantidade de ações de empresa que passou por agrupamento e desdobramento"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, self.acao_bbas.ticker, datetime.date.today()), 100)
        
    def test_qtd_acao_empresa_2(self):
        """Testa quantidade de ações de empresa que passou por alteração com desdobramento"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, self.acao_ambv.ticker, datetime.date.today()), 0)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, self.acao_abev.ticker, datetime.date.today()), 500)
        
    def test_qtd_acao_empresa_3(self):
        """Testa quantidade de ações de empresa que passou por alteração com agrupamento"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, self.acao_vale_5.ticker, datetime.date.today()), 0)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, self.acao_vale_3.ticker, datetime.date.today()), 193)
        
    def test_qtd_acao_empresa_4(self):
        """Testa quantidade de ações de empresa que passou por alteração e bônus"""
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, self.acao_tble.ticker, datetime.date.today()), 0)
        self.assertEqual(calcular_qtd_acoes_ate_dia_por_ticker(self.investidor, self.acao_egie.ticker, datetime.date.today()), 125)
        
        