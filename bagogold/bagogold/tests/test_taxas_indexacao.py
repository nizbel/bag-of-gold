# -*- coding: utf-8 -*-
from django.test import TestCase
from bagogold.bagogold.utils.taxas_indexacao import buscar_valores_diarios_di

class DITestCase(TestCase):

    def test_buscar_datas(self):
        """Testa se a busca funciona"""
        buscar_valores_diarios_di()
        self.assertTrue(HistoricoTaxaDI.objects.exists())
        
    def test_buscar_datas_anterior_a_ultima(self):
        """Testa buscar datas que não haviam sido preenchidas e são anteriores a ultima data na base"""
        # Gerar valor para última data útil
        ultimo_dia_util = datetime.date.today() - datetime.timedelta(days=1)
        while not verificar_se_dia_util(ultimo_dia_util):
            ultimo_dia_util = ultimo_dia_util - datetime.timedelta(days=1)
        HistoricoTaxaDI.objects.create(data=ultimo_dia_util, taxa=Decimal(10))
        buscar_valores_diarios_di()
        self.assertTrue(HistoricoTaxaDI.objects.filter(data__lt=ultimo_dia_util).exists()
        
    def test_buscar_datas_com_datas_registradas(self):
        """Testa a busca quando já existem algumas datas na base"""
        # Gerar valores para os últimos 365 dias
        for data in (datetime.date.today() - datetime.timedelta(days=n) for n in xrange(5, 365)):
            if verificar_se_dia_util(data):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(10))
        qtd_historico = HistoricoTaxaDI.objects.count()
        buscar_valores_diarios_di()
        self.assertTrue(HistoricoTaxaDI.objects.count() > qtd_historico)