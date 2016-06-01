# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa
from django.test import TestCase
import datetime

class AtualizarLCPorDITestCase(TestCase):
    
#     def setUp(self):
#         Titulo.objects.create(tipo="NTN-B Principal", data_vencimento=datetime.date(2035, 1, 1))
#         OperacaoTitulo.objects.create(preco_unitario=742.28, quantidade=1, data= models.DateField(u'Data', blank=True, null=True)
#     taxa_bvmf = models.DecimalField(u'Taxa BVMF', max_digits=11, decimal_places=2)
#     taxa_custodia = models.DecimalField(u'Taxa do agente de custódia', max_digits=11, decimal_places=2)
#     tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
#     titulo = models.ForeignKey('Titulo')
#     consolidada=True)

    def test_iof_regressivo(self):
        """Testar de acordo com o pego no extrato da conta"""
        #10.224,87    10.229,17 
        self.assertEqual(calcular_valor_atualizado_com_taxa(14.13, 10224.87, 80), 10229.17)
