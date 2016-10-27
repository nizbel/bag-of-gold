# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo, OperacaoTitulo
from bagogold.bagogold.utils.misc import calcular_iof_regressivo, \
    verificar_feriado_bovespa, qtd_dias_uteis_no_periodo
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
        
class VerificarFeriadoBovespaTestCase(TestCase):
    
    def test_deve_ser_feriado(self):
        """Testa o Natal"""
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 12, 25)))
        
    def test_nao_deve_ser_feriado(self):
        """Testa dia 12 de Agosto"""
        self.assertFalse(verificar_feriado_bovespa(datetime.date(2016, 8, 12)))
        
class QtdDiasUteisNoPeriodoTestCase(TestCase):
    
    def test_mostrar_erro_data_final_menor_que_inicial(self):
        """Testa se é lançado um ValueError"""
        with self.assertRaises(ValueError):
            qtd_dias_uteis_no_periodo(datetime.date(2016, 5, 5), datetime.date(2016, 5, 1))
            
    def test_quantidade_com_feriados(self):
        """Testa se retorna os 81 dias úteis"""
        self.assertEqual(qtd_dias_uteis_no_periodo(datetime.date(2016, 7, 1), datetime.date(2016, 10, 26)), 81)

