# -*- coding: utf-8 -*-
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import FII, OperacaoFII
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
import datetime

class CalcularAtualizacaoProventoSelicTestCase(TestCase):
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
        OperacaoFII.objects.create(fii=fii_1, investidor=user.investidor, data=datetime.date(2017, 5, 11), quantidade=43, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        # Agrupamento
        OperacaoFII.objects.create(fii=fii_2, investidor=user.investidor, data=datetime.date(2017, 5, 11), quantidade=430, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        # Desdobramento + Incorporação
        OperacaoFII.objects.create(fii=fii_3, investidor=user.investidor, data=datetime.date(2017, 5, 11), quantidade=37, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        OperacaoFII.objects.create(fii=fii_4, investidor=user.investidor, data=datetime.date(2017, 5, 11), quantidade=271, preco_unitario=Decimal('93.44'), corretagem=0, emolumentos=0)
        
        
    def test_verificar_qtd_apos_agrupamento(self):
        
    def test_verificar_qtd_apos_desdobramento(self):
        
    def test_verificar_qtd_apos_incorporacao(self):
        
