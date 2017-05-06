# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo, OperacaoTitulo
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia_por_titulo
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models.aggregates import Sum
from django.test import TestCase
from random import randint
import datetime

class TesouroDiretoTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        titulo_1 = Titulo.objects.create(tipo='LTN', data_vencimento=datetime.date(2017, 1, 1), data_inicio=datetime.date(2013, 1, 1))
        
        titulo_2 = Titulo.objects.create(tipo='NTNB', data_vencimento=datetime.date(2035, 1, 1), data_inicio=datetime.date(2013, 1, 1))
        
        titulo_3 = Titulo.objects.create(tipo='LFT', data_vencimento=datetime.date(2021, 1, 1), data_inicio=datetime.date(2013, 1, 1))
        
        for titulo in Titulo.objects.all():
            for _ in range(6):
                operacao_titulo = OperacaoTitulo.objects.create(investidor=user.investidor, titulo=titulo, quantidade=randint(1,3), preco_unitario=Decimal(760),
                                                                data=datetime.date(2015, 3, 5), taxa_bvmf=Decimal('2.50'), taxa_custodia=Decimal('1.52'), tipo_operacao='C')
            for _ in range(2):
                operacao_titulo = OperacaoTitulo.objects.create(investidor=user.investidor, titulo=titulo, quantidade=randint(1,3), preco_unitario=Decimal(800),
                                                                data=datetime.date(2016, 3, 5), taxa_bvmf=Decimal('2.50'), taxa_custodia=Decimal('1.52'), tipo_operacao='V')
        
    def test_qtd_titulos_ate_dia_por_titulo(self):
        "Testa quantidade de títulos até dia"
        investidor = User.objects.get(username='tester').investidor
        
        for titulo in Titulo.objects.all():
            compras = OperacaoTitulo.objects.filter(investidor=investidor, titulo=titulo, data__lte=datetime.date(2016, 3, 5), tipo_operacao='C').exclude(data__isnull=True) \
                .aggregate(total_compras=Sum('quantidade'))['total_compras'] or Decimal(0)
            vendas = OperacaoTitulo.objects.filter(investidor=investidor, titulo=titulo, data__lte=datetime.date(2016, 3, 5), tipo_operacao='V').exclude(data__isnull=True) \
                .aggregate(total_vendas=Sum('quantidade'))['total_vendas'] or Decimal(0)
            self.assertEqual(quantidade_titulos_ate_dia_por_titulo(investidor, titulo.id, datetime.date(2016, 3, 5)), compras - vendas)