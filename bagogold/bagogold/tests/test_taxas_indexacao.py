# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.test import TestCase

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.misc import verifica_se_dia_util
from bagogold.bagogold.utils.taxas_indexacao import buscar_valores_diarios_di


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
        
        # Preencher valores IPCA
        
        # Preencher valores Selic
        
    def test_atualizar_valor_taxa_di(self):
        """Testa atualizar valor pela taxa DI"""
        # Buscar última taxa DI
        ultimo_di = HistoricoTaxaDI.objects.all().order_by('-data')[0].taxa
        
        # Atualizar 1 dia pela taxa integral
        self.assertEqual(calcular_valor_atualizado_com_taxa_di(taxa, 1000, 100), 1000 * (1 + ultimo_di/100)**(Decimal(1)/252))
        
        # Atualizar 1 dia por metade da taxa
        self.assertEqual(calcular_valor_atualizado_com_taxa_di(taxa, 1000, 50), 1000 * (1 + ultimo_di/100 / 2)**(Decimal(1)/252))
        
        # Buscar taxas DI em um período
        taxas_di = dict(HistoricoTaxaDI.objects.filter(data__range=[datetime.date(2018, 3, 1), datetime.date(2018, 3, 30)]).values_list('data', 'taxa'))
        
        # Atualizar vários dias pela taxa integral
        self.assertEqual(calcular_valor_atualizado_com_taxas_di(taxas_di, 1000, 100), 1000 * Decimal('1.00531564'))
        
        # Atualizar vários dias por metade da taxa
        self.assertEqual(calcular_valor_atualizado_com_taxas_di(taxas_di, 1000, 50), 1000 * Decimal('1.00265446'))
        
    def test_atualizar_valor_taxa_ipca(self):
        """Testa atualizar valor pelo IPCA"""
        pass
        
    def test_atualizar_valor_taxa_prefixado(self):
        """Testa atualizar valor por taxa prefixada"""
        pass
        
    def test_atualizar_valor_taxa_selic(self):
        """Testa atualizar valor pela taxa Selic"""
        # Buscar última taxa DI
        ultima_taxa = HistoricoTaxaSelic.objects.all().order_by('-data')[0].taxa_diaria
        
        # Atualizar 1 dia pela taxa integral
        self.assertEqual(calcular_valor_atualizado_com_taxa_selic(taxa, 1000, 100), 1000 * ultima_taxa)
        
        # Atualizar 1 dia por metade da taxa
        self.assertEqual(calcular_valor_atualizado_com_taxa_di(taxa, 1000, 50), 1000 * ultima_taxa / 2)
        
        # Buscar taxas DI em um período
        taxas_selic = dict(HistoricoTaxaSelic.objects.filter(data__range=[datetime.date(2018, 3, 1), datetime.date(2018, 3, 30)]).values_list('data', 'taxa'))
        
        # Atualizar vários dias pela taxa integral
        self.assertEqual(calcular_valor_atualizado_com_taxas_di(taxas_selic, 1000, 100), 1000 * Decimal('1.005323448053666'))
        
        # Atualizar vários dias por metade da taxa
        self.assertEqual(calcular_valor_atualizado_com_taxas_di(taxas_selic, 1000, 50), 1000 * Decimal('1.00265446'))