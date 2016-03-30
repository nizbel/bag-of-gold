# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo, OperacaoTitulo
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
from django.test import TestCase
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
