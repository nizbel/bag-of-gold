# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test.testcases import TestCase

from django.core.urlresolvers import reverse


class AcessarTimelineTestCase(TestCase):
    def test_acesso_usuario_deslogado(self):
        """Testa acesso de usuário deslogado, deve ser redirecionado a tela de login"""
        response = self.client.get(reverse('divisoes:linha_do_tempo', kwargs={'divisao_id': 1}))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_acesso_usuario_logado_sem_operacoes_sucesso(self):
        """Testa acesso de usuário logado sem operações cadastradas"""
        User.objects.create(username='test', password='test')
        
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('divisoes:linha_do_tempo', kwargs={'divisao_id': 1}))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['investimentos'], {'A': u'Letra de Câmbio', 'C': u'CDB/RDB', 'L': u'LCI/LCA', 'M': u'Criptomoeda'})
        
        # Buscar timelines por AJAX
        response = self.client.get(reverse('divisoes:linha_do_tempo', kwargs={'divisao_id': 1}), {'investimento': 'C'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    def test_acesso_usuario_logado_divisao_alheia(self):
        """Testa acesso de usuário logado em divisão que não é dele"""
        User.objects.create(username='test1', password='test1')
        User.objects.create(username='test2', password='test2')
        
        self.client.login(username='test1', password='test1')
        response = self.client.get(reverse('divisoes:linha_do_tempo', kwargs={'divisao_id': 2}))
        
        self.assertEqual(response.status_code, 403)
    
    def test_acesso_usuario_logado_divisao_inexistente(self):
        """Testa acesso de usuário logado em divisão que não existe"""
        User.objects.create(username='test', password='test')
        
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('divisoes:linha_do_tempo', kwargs={'divisao_id': 2}))
        
        self.assertEqual(response.status_code, 302)
        # TODO  testar se foi redirecionado para listar divisões
        
    def test_acesso_usuario_logado_com_operacoes(self):
        """Testa acesso de usuário logado com operações"""
        nizbel = User.objects.create(username='nizbel', password='nizbel')
        
        # TODO Criar operações para usuário nizbel
        adicionar_operacoes_teste(nizbel.investidor)
        
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('divisoes:linha_do_tempo', kwargs={'divisao_id': 1}))
        
        self.assertEqual(response.status_code, 200)
        
        # Buscar timelines por AJAX
        response = self.client.get(reverse('divisoes:linha_do_tempo', kwargs={'divisao_id': 1}), {'investimento': 'C'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        
    # EXEMPLO DE AJAX
    # r = self.client.post('/ratings/vote/', {'value': '1',},
    #                           HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    