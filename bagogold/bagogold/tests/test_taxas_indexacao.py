# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.db.models.aggregates import Count
from django.test import TestCase

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI, \
    HistoricoTaxaSelic
from bagogold.bagogold.utils.misc import verifica_se_dia_util, \
    verificar_feriado_bovespa
from bagogold.bagogold.utils.taxas_indexacao import buscar_valores_diarios_di, \
    calcular_valor_atualizado_com_taxa_di, calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_selic


class BuscaDITestCase(TestCase):
    """Testa busca de valores históricos para o DI"""

    def test_buscar_datas(self):
        """Testa se a busca funciona"""
        buscar_valores_diarios_di()
        self.assertTrue(HistoricoTaxaDI.objects.exists())
        
    def test_buscar_datas_anterior_a_ultima(self):
        """Testa buscar datas que não haviam sido preenchidas e são anteriores a ultima data na base"""
        # Gerar valor para última data útil
        ultimo_dia_util = datetime.date.today() - datetime.timedelta(days=1)
        while not verifica_se_dia_util(ultimo_dia_util):
            ultimo_dia_util = ultimo_dia_util - datetime.timedelta(days=1)
        HistoricoTaxaDI.objects.create(data=ultimo_dia_util, taxa=Decimal(10))
        buscar_valores_diarios_di()
        self.assertTrue(HistoricoTaxaDI.objects.filter(data__lt=ultimo_dia_util).exists())
        
    def test_buscar_datas_com_datas_registradas(self):
        """Testa a busca quando já existem algumas datas na base"""
        # Gerar valores para os últimos 365 dias
        for data in (datetime.date.today() - datetime.timedelta(days=n) for n in xrange(5, 365)):
            if verifica_se_dia_util(data):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(10))
        qtd_historico = HistoricoTaxaDI.objects.count()
        buscar_valores_diarios_di()
        self.assertTrue(HistoricoTaxaDI.objects.count() > qtd_historico)
        
class AtualizacaoTaxasTestCase(TestCase):
    """Testa atualização de valores pelas taxas"""
    def setUp(self):
        # Preencher valores DI
        date_list = [datetime.date(2018, 3, 1) + datetime.timedelta(days=x) for x in range((datetime.date(2018, 4, 1) - datetime.date(2018, 3, 1)).days)]
        date_list = [data for data in date_list if data.weekday() < 5 and not verificar_feriado_bovespa(data)]
        
        for data in date_list:
            if data >= datetime.date(2018, 3, 22):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal('6.39'))
            else:
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal('6.64'))
        
        # Preencher valores IPCA
        
        # Preencher valores Selic
        
    def test_atualizar_valor_taxa_di(self):
        """Testa atualizar valor pela taxa DI"""
        # Buscar última taxa DI
        ultimo_di = HistoricoTaxaDI.objects.all().order_by('-data')[0].taxa
        
        # Atualizar 1 dia pela taxa integral
        self.assertAlmostEqual(calcular_valor_atualizado_com_taxa_di(ultimo_di, 1000, 100), 1000 * (1 + ultimo_di/100)**(Decimal(1)/252), 
                               delta=Decimal('0.001'))
        
        # Atualizar 1 dia por metade da taxa
        self.assertAlmostEqual(calcular_valor_atualizado_com_taxa_di(ultimo_di, 1000, 50), 1000 * (((1 + ultimo_di/100)**(Decimal(1)/252) - 1) / 2 + 1), 
                               delta=Decimal('0.001'))
        
#         print dict(HistoricoTaxaDI.objects.filter(data__range=[datetime.date(2018, 3, 1), datetime.date(2018, 3, 30)]).values('taxa').distinct().order_by('taxa') \
#                         .annotate(qtd_dias=Count('data')).values_list('taxa', 'qtd_dias'))
                        
        # Buscar taxas DI em um período
        taxas_di = dict(HistoricoTaxaDI.objects.filter(data__range=[datetime.date(2018, 3, 1), datetime.date(2018, 3, 30)]).values('taxa').distinct().order_by('taxa') \
                        .annotate(qtd_dias=Count('data')).values_list('taxa', 'qtd_dias'))
        
        # Atualizar vários dias pela taxa integral
        self.assertAlmostEqual(calcular_valor_atualizado_com_taxas_di(taxas_di, 1000, 100), 1000 * Decimal('1.00531564'), delta=Decimal('0.001'))
        
        # Atualizar vários dias por metade da taxa
        self.assertAlmostEqual(calcular_valor_atualizado_com_taxas_di(taxas_di, 1000, 50), 1000 * Decimal('1.00265446'), delta=Decimal('0.001'))
        
    def test_atualizar_valor_taxa_ipca(self):
        """Testa atualizar valor pelo IPCA"""
        pass
        
    def test_atualizar_valor_taxa_prefixado(self):
        """Testa atualizar valor por taxa prefixada"""
        pass
        
    def test_atualizar_valor_taxa_selic(self):
        """Testa atualizar valor pela taxa Selic"""
        pass
#         # Buscar última taxa DI
#         ultima_taxa = HistoricoTaxaSelic.objects.all().order_by('-data')[0].taxa_diaria
#         
#         # Atualizar 1 dia pela taxa integral
#         self.assertAlmostEqual(calcular_valor_atualizado_com_taxa_selic(ultima_taxa, 1000), 1000 * ultima_taxa, delta=Decimal('0.001'))
#         
#         # Buscar taxas Selic em um período
#         taxas_selic = dict(HistoricoTaxaSelic.objects.filter(data__range=[datetime.date(2018, 3, 1), datetime.date(2018, 3, 30)]).values_list('data', 'taxa'))
#         
#         # Atualizar vários dias pela taxa integral
#         self.assertAlmostEqual(calcular_valor_atualizado_com_taxas_di(taxas_selic, 1000, 100), 1000 * Decimal('1.005323448053666'), delta=Decimal('0.001'))
#         
#         # Atualizar vários dias por metade da taxa
#         self.assertAlmostEqual(calcular_valor_atualizado_com_taxas_di(taxas_selic, 1000, 50), 1000 * Decimal('1.00265446'), delta=Decimal('0.001'))
        
class BuscarTaxasIPCATesteCase(TestCase):
    def setUp(self):
        pass
    
    def test_buscar_historico_ipca(self):
        """Testa se a busca por histórico de IPCA está funcionando"""
        pass
    
    def test_buscar_ipca_projetado(self):
        """Testa se a busca por IPCA projetado está funcionando"""
        pass
    
    def test_ipca_projetado_antes_do_oficial(self):
        """Testa se nunca é criado IPCA projetado com data de início anterior a IPCA oficial"""
        pass
    
    def test_ipca_oficial_deve_pagar_ipca_projetado(self):
        """Testa se IPCA oficial ao ser criado apaga IPCA projetado anterior"""
        pass