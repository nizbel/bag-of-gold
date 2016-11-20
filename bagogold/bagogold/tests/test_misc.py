# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo, OperacaoTitulo
from bagogold.bagogold.utils.misc import calcular_iof_regressivo, \
    verificar_feriado_bovespa, qtd_dias_uteis_no_periodo, \
    calcular_domingo_pascoa_no_ano, formatar_zeros_a_direita_apos_2_casas_decimais
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
    
    def test_domingo_pascoa(self):
        """Testa as datas do domingo de páscoa para 2014, 2015, 2016, 2017"""
        self.assertEqual(calcular_domingo_pascoa_no_ano(2014), datetime.date(2014, 4, 20))
        self.assertEqual(calcular_domingo_pascoa_no_ano(2015), datetime.date(2015, 4, 5))
        self.assertEqual(calcular_domingo_pascoa_no_ano(2016), datetime.date(2016, 3, 27))
        self.assertEqual(calcular_domingo_pascoa_no_ano(2017), datetime.date(2017, 4, 16))
        
    def test_deve_ser_feriado(self):
        """Testa o Natal"""
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 12, 25)))
        
    def test_nao_deve_ser_feriado(self):
        """Testa dia 12 de Agosto"""
        self.assertFalse(verificar_feriado_bovespa(datetime.date(2016, 8, 12)))
        
    def test_feriados_moveis(self):
        """Testa feriados móveis, carnaval, sexta-feira santa e corpus christi"""
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 2, 9)))
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 3, 25)))
        self.assertTrue(verificar_feriado_bovespa(datetime.date(2016, 5, 26)))
        
class QtdDiasUteisNoPeriodoTestCase(TestCase):
    
    def test_mostrar_erro_data_final_menor_que_inicial(self):
        """Testa se é lançado um ValueError"""
        with self.assertRaises(ValueError):
            qtd_dias_uteis_no_periodo(datetime.date(2016, 5, 5), datetime.date(2016, 5, 1))
            
    def test_quantidade_com_feriados(self):
        """Testa se retorna os 81 dias úteis"""
        self.assertEqual(qtd_dias_uteis_no_periodo(datetime.date(2016, 7, 1), datetime.date(2016, 10, 26)), 81)

class FormatarZerosADireitaApos2CasasTestCase(TestCase):
    
    def test_formatar_para_valor_inteiro(self):
        """Testa formatação em um valor inteiro"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(1), '1.00')
        
    def test_formatar_para_1_casa_decimal_diferente_zero(self):
        """Testa formatação em um número com 2 casas decimais diferentes de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(2.3), '2.30')
        
    def test_formatar_para_2_casas_decimais_iguais_zero(self):
        """Testa formatação em um número com 2 casas decimais diferentes de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(2.00), '2.00')
        
    def test_formatar_para_2_casas_decimais_diferentes_zero(self):
        """Testa formatação em um número com 2 casas decimais diferentes de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(2.34), '2.34')
        
    def test_formatar_para_varias_casas_decimais_iguais_zero(self):
        """Testa formatação em um número com várias casas decimais iguais de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(1.0000000), '1.00')
        
    def test_formatar_para_varias_casas_decimais_diferentes_zero(self):
        """Testa formatação em um número com várias casas decimais diferentes de zero"""
        self.assertEqual(formatar_zeros_a_direita_apos_2_casas_decimais(1.4987004), '1.4987004')