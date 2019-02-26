# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.test import TestCase

from bagogold.bagogold.models.empresa import Empresa
from bagogold.fii.models import FII, HistoricoFII
from bagogold.fii.utils import calcular_variacao_percentual_fii_por_periodo


class CalcularVariacaoPercentualFIIPeriodoTestCase(TestCase):
    """Testa a função calcular_variacao_percentual_fii_por_periodo"""
    @classmethod
    def setUpClass(cls):
        super(CalcularVariacaoPercentualFIIPeriodoTestCase, cls).setUpClass()
        empresa_1 = Empresa.objects.create(nome='BA', nome_pregao='FII BA')
        cls.fii_1 = FII.objects.create(ticker='BAPO11', empresa=empresa_1)
        
        HistoricoFII.objects.create(fii=cls.fii_1, data=datetime.date(2017, 10, 31), preco_unitario=Decimal(100))
        HistoricoFII.objects.create(fii=cls.fii_1, data=datetime.date(2018, 10, 29), preco_unitario=Decimal(100))
        HistoricoFII.objects.create(fii=cls.fii_1, data=datetime.date(2018, 10, 30), preco_unitario=Decimal(70))
        HistoricoFII.objects.create(fii=cls.fii_1, data=datetime.date(2018, 10, 31), preco_unitario=Decimal(300))
        
    def test_variacao_positiva(self):
        """Testa se cálculo de variação está certo para situação de ganho"""
#         fii = FII.objects.get(ticker='BAPO11')
        self.assertEqual(calcular_variacao_percentual_fii_por_periodo(self.fii_1, datetime.date(2017, 10, 31), datetime.date(2018, 10, 31)), 200)
    
    def test_variacao_negativa(self):
        """Testa se cálculo de variação está certo para situação de perda"""
#         fii = FII.objects.get(ticker='BAPO11')
        self.assertEqual(calcular_variacao_percentual_fii_por_periodo(self.fii_1, datetime.date(2017, 10, 31), datetime.date(2018, 10, 30)), -30)
        
    def test_sem_variacao(self):
        """Testa se cálculo retorna 0 para situação sem variação"""
#         fii = FII.objects.get(ticker='BAPO11')
        self.assertEqual(calcular_variacao_percentual_fii_por_periodo(self.fii_1, datetime.date(2017, 10, 31), datetime.date(2018, 10, 29)), 0)
        
    def test_sem_valores_no_periodo(self):
        """Testa se cálculo retorna 0 para caso de não existir valores no período"""
#         fii = FII.objects.get(ticker='BAPO11')
        self.assertEqual(calcular_variacao_percentual_fii_por_periodo(self.fii_1, datetime.date(2016, 10, 31), datetime.date(2018, 10, 31)), 0)
        
    def test_erro_nas_datas(self):
        """Testa se cálculo joga erro para data fim menor ou igual a data inicial"""
#         fii = FII.objects.get(ticker='BAPO11')
        with self.assertRaises(ValueError):
            calcular_variacao_percentual_fii_por_periodo(self.fii_1, datetime.date(2018, 10, 31), datetime.date(2017, 10, 31))
        
