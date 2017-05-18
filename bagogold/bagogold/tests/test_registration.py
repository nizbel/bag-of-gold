# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import Client, TestCase

class LoginTestCase(TestCase):
    
    def setUp(self):
        User.objects.create(username='teste', password='teste')
    
    def test_ver_tela(self):
        """Testa ver a tela de login"""
        c = Client()
        response = c.get('/login/')
        self.assertEqual(response.status_code, 200)
        
    def test_realizar_login(self):
        """Testa realizar login"""
        c = Client()
        response = c.post('/login/', {'username': 'tester', 'password': 'tester'})
        self.assertFormError(response, 'form', None, u'Usuário não encontrado.')
        
        response = c.post('/login/', {'username': 'teste', 'password': 'tester'})
        self.assertFormError(response, 'form', None, u'Senha inválida para o usuário.')
        
        response = c.post('/login/', {'username': 'teste', 'password': 'teste'})
        print response.url, response.request
        self.assertEqual(response.url, '/painel_geral/')
        
