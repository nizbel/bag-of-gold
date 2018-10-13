# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test.testcases import TestCase

from django.core.urlresolvers import reverse


class AcessarTimelineTestCase(TestCase):
    def setUp(self):
        User.objects.create(username='test', password='test')
        nizbel = User.objects.create(username='nizbel', password='nizbel')
        
        # TODO Criar operações para usuário nizbel
        
    def test_acesso_usuario_deslogado(self):
        """Testa acesso de usuário deslogado, deve ser redirecionado a tela de login"""
        response = self.client.get(reverse('divisoes:linha_do_tempo', kwargs={'divisao_id': 1}))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_acesso_usuario_logado_sem_operacoes(self):
        """Testa acesso de usuário logado sem operações cadastradas"""
        pass
        
    def test_acesso_usuario_logado_com_operacoes(self):
        """Testa acesso de usuário logado com operações"""
        pass
        
    # EXEMPLO DE AJAX
    # r = self.client.post('/ratings/vote/', {'value': '1',},
    #                           HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    