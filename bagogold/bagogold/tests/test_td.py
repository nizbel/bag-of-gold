# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo, OperacaoTitulo
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia_por_titulo, \
    quantidade_titulos_ate_dia
from decimal import Decimal
from django.contrib.auth.models import User
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
            for _ in range(90):
                operacao_titulo = OperacaoTitulo.objects.create(investidor=user.investidor, titulo=titulo, quantidade=randint(1,5), preco_unitario=Decimal(760),
                                                                data=datetime.date(2015, 3, 5), taxa_bvmf=Decimal('2.50'), taxa_custodia=Decimal('1.52'), tipo_operacao='C')
            for _ in range(40):
                operacao_titulo = OperacaoTitulo.objects.create(investidor=user.investidor, titulo=titulo, quantidade=randint(1,5), preco_unitario=Decimal(800),
                                                                data=datetime.date(2016, 3, 5), taxa_bvmf=Decimal('2.50'), taxa_custodia=Decimal('1.52'), tipo_operacao='V')
        
