# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from django.test.testcases import TestCase

from django.core.urlresolvers import reverse

class DetalharDebentureTestCase (TestCase):
    def setUp(self):
        # Usuário sem operações
        User.objects.create(username='nizbel', password='nizbel')
        
        # Usuário com operações
        tester = User.objects.create(username='tester', password='tester')
    
        # TODO Criar debenture
        debenture = Debenture.objects.create(codigo='CMIG15')
        
        # TODO Criar histórico de juros
        
        # TODO Criar histórico de amortizações
        
        # TODO Criar histórico de premio
        
        # Operações do usuário tester
        OperacaoDebenture.objects.create(investidor=tester.investidor, debenture=debenture, preco_unitario=Decimal(10000),
                                         quantidade=5, data=datetime.date.today(), taxa=0, tipo_operacao='C')
        
        
    def test_usuario_deslogado(self):
        """Testa acesso de usuário deslogado"""
        response = self.client.get(reverse('debentures:detalhar_debenture'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['debenture'].codigo, Debenture.objects.get(codigo='CMIG15').codigo)
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['juros']), 0)
        self.assertEqual(len(response.context_data['amortizacoes']), 0)
        self.assertEqual(len(response.context_data['premios']), 0)
        
    def test_usuario_logado_sem_operacoes(self):
        """Testa acesso de usuário logado sem operações na debenture"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('debentures:detalhar_debenture'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['debenture'].codigo, Debenture.objects.get(codigo='CMIG15').codigo)
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['juros']), 0)
        self.assertEqual(len(response.context_data['amortizacoes']), 0)
        self.assertEqual(len(response.context_data['premios']), 0)
        
    def test_usuario_logado_com_operacoes(self):
        """Testa acesso de usuário logado com operações na debenture"""
        self.client.login(username='tester', password='tester')
        
        response = self.client.get(reverse('debentures:detalhar_debenture'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['debenture'].codigo, Debenture.objects.get(codigo='CMIG15').codigo)
        self.assertEqual(len(response.context_data['operacoes']), 1)
        self.assertEqual(len(response.context_data['juros']), 0)
        self.assertEqual(len(response.context_data['amortizacoes']), 0)
        self.assertEqual(len(response.context_data['premios']), 0)