# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

class LoginTestCase(TestCase):
    
    def setUp(self):
        User.objects.create_user('teste', 'teste@teste.com', 'teste')
    
    def test_ver_tela(self):
        """Testa ver a tela de login"""
        c = Client()
        response = c.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s"' % reverse("password_reset"))
        self.assertContains(response, 'href="%s"' % reverse("cadastro"))
        
    def test_realizar_login(self):
        """Testa realizar login"""
        c = Client()
        response = c.post(reverse('login'), {'username': 'tester', 'password': 'tester'})
        self.assertFormError(response, 'form', None, u'Usuário não encontrado.')
        
        response = c.post(reverse('login'), {'username': 'teste', 'password': 'tester'})
        self.assertFormError(response, 'form', None, u'Senha inválida para o usuário.')
        
        response = c.post(reverse('login'), {'username': 'teste', 'password': 'teste'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], reverse('inicio:painel_geral'))
        
class PasswordResetTestCase(TestCase):
    
    def setUp(self):
        User.objects.create_user('teste', 'teste@teste.com', 'teste')
    
    def test_ver_tela(self):
        """Testa ver a tela de redefinição de senha"""
        c = Client()
        response = c.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s"' % reverse("login"))
        
    def test_enviar_email(self):
        c = Client()
        
        response = c.post(reverse('password_reset'),{'email':'teste@teste.com'})
        self.assertEqual(response.status_code, 302)
        
        # Buscar token
        token = response.context[0]['token']
        uid = response.context[0]['uid']
        
        # Utilizar token para página de redefinição de senha
        response = c.get(reverse('password_reset_confirm', kwargs={'token':token,'uidb64':uid}), follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Alterar senha
        response = c.post(response.request['PATH_INFO'], {'new_password1':'testeteste','new_password2':'testeteste'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], reverse('password_reset_complete'))
        self.assertContains(response, 'href="%s"' % reverse("inicio:painel_geral"))
        
        # Realizar logout
        response = c.get(reverse('logout'), follow=True)
        self.assertEqual(response.request['PATH_INFO'], reverse('login'))
        
        # Testar se senha foi mesmo alterada
        response = c.post(reverse('login'), {'username': 'teste', 'password': 'testeteste'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], reverse('inicio:painel_geral'))