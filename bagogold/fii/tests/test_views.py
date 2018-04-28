# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from django.test.testcases import TestCase

from django.core.urlresolvers import reverse

from bagogold.bagogold.models.empresa import Empresa
from bagogold.fii.models import FII, HistoricoFII, ProventoFII, \
    EventoAgrupamentoFII, OperacaoFII


class DetalharFIITestCase (TestCase):
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        user_vendido = User.objects.create_user('vendido', 'vendido@teste.com', 'vendido')

        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
        
        fii_1 = FII.objects.create(ticker='TEST11', empresa=empresa)
        fii_2 = FII.objects.create(ticker='TSTE11', empresa=empresa)
        
        for data in [datetime.date.today() - datetime.timedelta(days=x) for x in range(365)]:
            if data >= datetime.date.today() - datetime.timedelta(days=3):
                HistoricoFII.objects.create(fii=fii_2, preco_unitario=1200, data=data)
            else:
                HistoricoFII.objects.create(fii=fii_2, preco_unitario=120, data=data)
        
        for data in [datetime.date.today() - datetime.timedelta(days=30*x) for x in range(1, 7)]:
            ProventoFII.objects.create(fii=fii_2, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
                                       oficial_bovespa=True)
        
        EventoAgrupamentoFII.objects.create(fii=fii_2, data=datetime.date.today() - datetime.timedelta(days=3), proporcao=Decimal('0.1'))
        
        OperacaoFII.objects.create(fii=fii_2, investidor=nizbel.investidor, data=datetime.date.today() - datetime.timedelta(days=130),
                                   quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
        OperacaoFII.objects.create(fii=fii_2, investidor=nizbel.investidor, data=datetime.date.today() - datetime.timedelta(days=80),
                                   quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
        
        OperacaoFII.objects.create(fii=fii_2, investidor=user_vendido.investidor, data=datetime.date.today() - datetime.timedelta(days=130),
                                   quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
        OperacaoFII.objects.create(fii=fii_2, investidor=user_vendido.investidor, data=datetime.date.today() - datetime.timedelta(days=80),
                                   quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='V')
    
    def test_usuario_deslogado_fii_vazio(self):
        """Testa o acesso a view para um fii sem infos com um usuário deslogado"""
        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TEST11'}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['historico']), 0)
        self.assertEqual(len(response.context_data['proventos']), 0)
        self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TEST11'))
        
    def test_usuario_logado_fii_vazio(self):
        """Testa o acesso a view para um fii sem infos com um usuário logado"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TEST11'}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['historico']), 0)
        self.assertEqual(len(response.context_data['proventos']), 0)
        self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TEST11'))
        
    def test_usuario_deslogado_fii_com_infos(self):
        """Testa o acesso a view para um fii com infos com um usuário deslogado"""
        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTE11'}))
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['historico']), 365)
        self.assertEqual(len(response.context_data['proventos']), 6)
        self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TSTE11'))
        
    def test_usuario_logado_fii_com_infos(self):
        """Testa o acesso a view para um fii com infos com um usuário logado"""
        self.client.login(username='nizbel', password='nizbel')

        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTE11'}))      
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 2)
        self.assertEqual(len(response.context_data['historico']), 365)
        self.assertEqual(len(response.context_data['proventos']), 6)
        self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TSTE11'))
        # Quantidade de cotas atual é 1 devido ao agrupamento
        self.assertEqual(response.context_data['fii'].qtd_cotas, 1)
        
        
    def test_usuario_logado_fii_com_infos_vendido(self):
        """Testa o acesso a view para um fii com infos com um usuário logado, que já tinha liquidado sua posição"""
        self.client.login(username='vendido', password='vendido')

        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTE11'}))      
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 2)
        self.assertEqual(len(response.context_data['historico']), 365)
        self.assertEqual(len(response.context_data['proventos']), 6)
        self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TSTE11'))
        self.assertEqual(response.context_data['fii'].qtd_cotas, 0)
        
    def test_fii_nao_encontrado(self):
        """Testa o retorno caso o FII não seja encontrado"""
        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTS11'}))      
        self.assertEqual(response.status_code, 404)
        