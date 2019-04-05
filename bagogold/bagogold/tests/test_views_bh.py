# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.contrib.messages.api import get_messages
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from bagogold.bagogold.models.acoes import OperacaoAcao, Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.divisoes import DivisaoOperacaoAcao


class EditarOperacaoTestCase (TestCase):
    @classmethod
    def setUpTestData(cls):
        super(EditarOperacaoTestCase, cls).setUpTestData()
        # Usuário sem operações cadastradas
        User.objects.create_user(username='nizbel', password='nizbel')
        
        # Usuário com operações cadastradas
        cls.tester = User.objects.create_user(username='tester', password='tester')
    
        # Criar ação
        cls.empresa = Empresa.objects.create(nome='Banco do Brasil', nome_pregao='BBAS')
        cls.acao = Acao.objects.create(ticker='BBAS3', empresa=cls.empresa)
        
        # Criar operação
        cls.operacao = OperacaoAcao.objects.create(data=datetime.date.today(), investidor=cls.tester.investidor, quantidade=100,
                                                   preco_unitario=20, consolidada=True, acao=cls.acao, corretagem=10, emolumentos=1,
                                                   tipo_operacao='C', destinacao='B')
        DivisaoOperacaoAcao.objects.create(divisao=cls.tester.investidor.divisaoprincipal.divisao, quantidade=cls.operacao.quantidade, 
                                           operacao=cls.operacao)
        
        # TODO Testar situação de uso de proventos
        
    def test_usuario_deslogado(self):
        """Testa acesso de usuário deslogado"""
        response = self.client.get(reverse('acoes:bh:editar_operacao_bh', kwargs={'id_operacao': self.operacao.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)
        
    def test_usuario_logado_sem_operacao(self):
        """Testa acesso de usuário logado sem operação, deve bloquear acesso"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('acoes:bh:editar_operacao_bh', kwargs={'id_operacao': self.operacao.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_usuario_logado_dono_operacao(self):
        """Testa acesso de usuário logado dono da operação"""
        self.client.login(username='tester', password='tester')
        
        response = self.client.get(reverse('acoes:bh:editar_operacao_bh', kwargs={'id_operacao': self.operacao.id}))
        self.assertEqual(response.status_code, 200)
        
        # Criar outra ação
        nova_acao = Acao.objects.create(empresa=self.empresa, ticker='BBAS4')
        
        response = self.client.post(reverse('acoes:bh:editar_operacao_bh', kwargs={'id_operacao': self.operacao.id}), 
                                    {'data': datetime.date.today() + datetime.timedelta(days=1), 'quantidade': 101,
                                     'preco_unitario': 21, 'consolidada': True, 'acao': nova_acao.id, 'corretagem': 11, 'emolumentos': 2,
                                     'tipo_operacao': 'C', 'save': 1})
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('acoes:bh:historico_bh'))
        
        self.operacao = OperacaoAcao.objects.get(id=self.operacao.id)
        self.assertEqual(self.operacao.data, datetime.date.today() + datetime.timedelta(days=1))
        self.assertEqual(self.operacao.quantidade, 101)
        self.assertEqual(self.operacao.preco_unitario, 21)
        self.assertEqual(self.operacao.corretagem, 11)
        self.assertEqual(self.operacao.emolumentos, 2)
        self.assertEqual(self.operacao.acao, nova_acao)
        
    def test_usuario_logado_dono_lc_excluir(self):
        """Testa exclusão de operação pelo dono"""
        self.client.login(username='tester', password='tester')
        
        response = self.client.post(reverse('acoes:bh:editar_operacao_bh', kwargs={'id_operacao': self.operacao.id}), 
                                    {'delete': 1})
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('acoes:bh:historico_bh'))
        
        self.assertFalse(OperacaoAcao.objects.filter(id=self.operacao.id).exists())
        
