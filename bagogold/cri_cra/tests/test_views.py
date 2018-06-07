# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from django.test.testcases import TestCase

from django.core.urlresolvers import reverse

from bagogold.cri_cra.models.cri_cra import CRI_CRA, OperacaoCRI_CRA


class PainelTestCase(TestCase):
    def setUp(self):
        # Criar usuário sem operações
        User.objects.create(username='test', password='test')
        
        # Criar usuário com operações
        nizbel = User.objects.create(username='nizbel', password='nizbel')
        
        # Criar usuário com operações todas vendidas
        vendido = User.objects.create(username='vendido', password='vendido')
        
        # Criar operações para os usuários
        cri_cra1 = CRI_CRA.objects.create(investidor=nizbel, nome='CRI')
        OperacaoCRI_CRA.objects.create(cri_cra=cri_cra1, quantidade=3, preco_unitario=Decimal(1000), data=datetime.date(2018, 5, 15), tipo_operacao='C')
        
        cri_cra2 = CRI_CRA.objects.create(investidor=vendido, nome='CRA')
        OperacaoCRI_CRA.objects.create(cri_cra=cri_cra1, quantidade=3, preco_unitario=Decimal(1000), data=datetime.date(2018, 5, 15), tipo_operacao='C')
        OperacaoCRI_CRA.objects.create(cri_cra=cri_cra1, quantidade=3, preco_unitario=Decimal(1100), data=datetime.date(2018, 5, 25), tipo_operacao='V')
        
    def test_usuario_deslogado(self):
        """Testa usuário deslogado"""
        response = self.client.get(reverse('cri_cra:painel_cri_cra'))
        
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.context, {'cri_cra': list(), 'dados': {}})
        
    def test_usuario_logado_sem_operacoes(self):
        """Testa usuário logado sem operações"""
        self.client.login('test', 'test')
        response = self.client.get(reverse('cri_cra:painel_cri_cra'))
        
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.context, {'cri_cra': list(), 'dados': {}})
        
    def test_usuario_logado_com_operacoes(self):
        """Testa usuário logado com operações"""
        self.client.login('nizbel', 'nizbel')
        response = self.client.get(reverse('cri_cra:painel_cri_cra'))
        
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.context, {'cri_cra': list(), 'dados': {}})
        
    def test_usuario_logado_com_operacoes_vendidas(self):
        """Testa usuário logado com operações vendidas"""
        self.client.login('vendido', 'vendido')
        response = self.client.get(reverse('cri_cra:painel_cri_cra'))
        
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.context, {'cri_cra': list(), 'dados': {}})