# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import OperacaoLetraCredito, LetraCredito
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa
from decimal import Decimal
from django.test import TestCase
import datetime

class AtualizarLCPorDITestCase(TestCase):
    
    def setUp(self):
        LetraCredito.objects.create(nome="LCA Teste")
        OperacaoLetraCredito.objects.create(quantidade=Decimal(2500), data=datetime.date(2016, 5, 23), tipo_operacao='C', \
                                            letra_credito=LetraCredito.objects.get(nome="LCA Teste"))

    def test_calculo_valor_atualizado_taxa_di(self):
        """Testar de acordo com o pego no extrato da conta"""
        # 2506,30 em 1 de Junho (6 dias após, todos com taxa DI 14,13%)
        operacao = OperacaoLetraCredito.objects.get(quantidade=(Decimal(2500)))
        for i in range(0,6):
            operacao.quantidade = calcular_valor_atualizado_com_taxa(Decimal(14.13), operacao.quantidade, Decimal(80))
        str_auxiliar = str(operacao.quantidade.quantize(Decimal('.0001')))
        operacao.quantidade = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        self.assertEqual(operacao.quantidade, Decimal('2506.30'))
