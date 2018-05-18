# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.contrib.auth.models import User

from django.core.management import call_command
from django.db.models.aggregates import Sum
from django.test import TestCase

from bagogold.bagogold.management.commands import buscar_historico_ipca
from bagogold.bagogold.models.taxas_indexacao import HistoricoIPCA
from bagogold.tesouro_direto.models import Titulo, OperacaoTitulo, \
    HistoricoTitulo
from bagogold.tesouro_direto.utils import quantidade_titulos_ate_dia_por_titulo, \
    calcular_valor_td_ate_dia, quantidade_titulos_ate_dia


class TesouroDiretoTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        titulo_1 = Titulo.objects.create(tipo='LTN', data_vencimento=datetime.date(2017, 1, 1), data_inicio=datetime.date(2013, 1, 1))
        
        titulo_2 = Titulo.objects.create(tipo='NTNB', data_vencimento=datetime.date(2035, 1, 1), data_inicio=datetime.date(2013, 1, 1))
        
        titulo_3 = Titulo.objects.create(tipo='LFT', data_vencimento=datetime.date(2021, 1, 1), data_inicio=datetime.date(2013, 1, 1))
        
        for titulo in Titulo.objects.all():
            for _ in range(6):
                operacao_titulo = OperacaoTitulo.objects.create(investidor=user.investidor, titulo=titulo, quantidade=3, preco_unitario=Decimal(760),
                                                                data=datetime.date(2015, 3, 5), taxa_bvmf=Decimal('2.50'), taxa_custodia=Decimal('1.52'), tipo_operacao='C')
            for _ in range(2):
                operacao_titulo = OperacaoTitulo.objects.create(investidor=user.investidor, titulo=titulo, quantidade=2, preco_unitario=Decimal(800),
                                                                data=datetime.date(2016, 3, 5), taxa_bvmf=Decimal('2.50'), taxa_custodia=Decimal('1.52'), tipo_operacao='V')
            
            # Adicionar histórico por uma semana
            for dias in range(5):
                HistoricoTitulo.objects.create(data=datetime.date(2016, 9, 12) + datetime.timedelta(days=dias), titulo=titulo, taxa_compra=Decimal('4.5'), taxa_venda=Decimal(5),
                                               preco_compra=Decimal(720 + dias*2.5), preco_venda=Decimal(710 + dias*2.5))
        
    def test_qtd_titulos_ate_dia_por_titulo(self):
        """Testa quantidade de títulos até dia"""
        investidor = User.objects.get(username='tester').investidor
        
        for titulo in Titulo.objects.all():
            compras = OperacaoTitulo.objects.filter(investidor=investidor, titulo=titulo, data__lte=datetime.date(2016, 3, 5), tipo_operacao='C').exclude(data__isnull=True) \
                .aggregate(total_compras=Sum('quantidade'))['total_compras'] or Decimal(0)
            vendas = OperacaoTitulo.objects.filter(investidor=investidor, titulo=titulo, data__lte=datetime.date(2016, 3, 5), tipo_operacao='V').exclude(data__isnull=True) \
                .aggregate(total_vendas=Sum('quantidade'))['total_vendas'] or Decimal(0)
            self.assertEqual(quantidade_titulos_ate_dia_por_titulo(investidor, titulo.id, datetime.date(2016, 3, 5)), compras - vendas)
            
    def test_valor_titulos_ate_dia_por_titulo(self):
        """Testa valor de títulos até dia"""
        investidor = User.objects.get(username='tester').investidor
        qtd_titulos = quantidade_titulos_ate_dia(investidor, datetime.date(2016, 9, 14))
        qtd_titulos.update((titulo_id, Decimal(qtd*715)) for titulo_id, qtd in qtd_titulos.items())
        self.assertDictEqual(calcular_valor_td_ate_dia(investidor, datetime.date(2016, 9, 14)), qtd_titulos)
                         

class ComandoPreencherHistoricoAnoAtualTDTestCase(TestCase):
    def test_comando(self):
        """Testa comando de preencher histórico para ano atual de Tesouro Direto"""

        args = []
        opts = {'test': True}
        # Roda uma vez para preencher a tabela e outra para verificar o que foi inserido
        call_command('preencher_historico_ano_atual_td', *args, **opts)
        call_command('preencher_historico_ano_atual_td', *args, **opts)

        self.assertTrue(Titulo.objects.filter().exists())
        self.assertTrue(HistoricoTitulo.objects.filter().exists())
        
class CalculoImpostoRendaTDTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='tester')
        
        titulo_1 = Titulo.objects.create(tipo='LTN', data_vencimento=datetime.date(2017, 1, 1), data_inicio=datetime.date(2013, 1, 1))
        
        titulo_2 = Titulo.objects.create(tipo='LTN', data_vencimento=datetime.date(2018, 1, 1), data_inicio=datetime.date(2014, 1, 1))
        
        # TODO Criar operações
        
        # TODO Verificar valores que devem ser testados
        
        # 02/01/2015 Tesouro D. Taxa Semestral 18,81 D
        # 01/07/2015 Tesouro D. Taxa Semestral 13,69 D
	    # 04/01/2016 Tesouro D. Taxa Semestral 18,18 D
        # 01/07/2016 Tesouro D. Taxa Semestral 1,89 D
        # 02/01/2017 Tesouro Direto-Resgate 5.756,60 C
        # 02/01/2017 Tesouro D. Taxa Semestral 26,69 D


        
    def test_imposto_renda_2017(self):
        """Testar valor de imposto de renda para 2017"""
        pass
        
    def test_imposto_renda_2018(self):
        """Testar valor de imposto de renda para 2018"""
        pass
        
class CalcularValorVencimentoIPCATestCase(TestCase):
    def setUp(self):
        # Preparar título IPCA
        Titulo.objects.create(tipo=Titulo.TIPO_OFICIAL_IPCA, data_vencimento=datetime.date(2024, 8, 15), data_inicio=datetime.date(2008, 8, 15))
        
        # Preparar histórico de IPCA
        buscar_historico_ipca()
        
    def test_vencimento_no_dia_9_5_2018(self):
        """Testa o valor de vencimento do IPCA para 09/05/2018"""
        titulo = Titulo.objects.get(tipo=Titulo.TIPO_OFICIAL_IPCA)
        self.assertAlmostEqual(titulo.valor_vencimento(datetime.date(2018, 5, 9), Decimal('3073.191850'), delta=Decimal('0.000001'))

    def test_vencimento_no_dia_8_5_2018(self):
        """Testa o valor de vencimento do IPCA para 08/05/2018"""
        titulo = Titulo.objects.get(tipo=Titulo.TIPO_OFICIAL_IPCA)
        self.assertAlmostEqual(titulo.valor_vencimento(datetime.date(2018, 5, 8), Decimal('3072.762234'), delta=Decimal('0.000001'))
        
    def test_vencimento_no_dia_15_5_2018(self):
        """Testa o valor de vencimento do IPCA para 15/05/2018"""
        titulo = Titulo.objects.get(tipo=Titulo.TIPO_OFICIAL_IPCA)
        self.assertAlmostEqual(titulo.valor_vencimento(datetime.date(2018, 5, 15), Decimal('3073.069824'), delta=Decimal('0.000001'))
        
    def test_vencimento_com_valor_projetado(self):
        """Testa o valor de vencimento do IPCA com valor projetado"""
        # Apagar valores oficiais do IPCA após 15 de Maio de 2018
        HistoricoIPCA.objects.filter(data_inicio__gt=datetime.date(2018, 5, 15)).delete()
        
        # Adicionar projetados
        HistoricoIPCA.objects.create(data_inicio=datetime.date(2018, 5, 16), data_fim=datetime.date(2018, 6, 15), valor=Decimal('0.0037')
        
        titulo = Titulo.objects.get(tipo=Titulo.TIPO_OFICIAL_IPCA)
        self.assertAlmostEqual(titulo.valor_vencimento(datetime.date(2018, 5, 16), Decimal('3073.585747'), delta=Decimal('0.000001'))

class CalcularValorVencimentoSelicTestCase(TestCase):
    def setUp(self):
        # Preparar título Selic
        Titulo.objects.create(tipo=Titulo.TIPO_OFICIAL_SELIC, data_vencimento=datetime.date(2024, 8, 1), data_inicio=datetime.date(2008, 8, 1))
        
        # Preparar histórico de Selic
#         buscar_historico_selic()
        
    def test_vencimento_no_dia_9_5_2018(self):
        """Testa o valor de vencimento do IPCA para 09/05/2018"""
        titulo = Titulo.objects.get(tipo=Titulo.TIPO_OFICIAL_SELIC)
        self.assertAlmostEqual(titulo.valor_vencimento(datetime.date(2018, 5, 15), Decimal('9503.531384'), delta=Decimal('0.000001'))
