# -*- coding: utf-8 -*-
from bagogold.urls import urlpatterns
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern,\
    NoReverseMatch
from django.test import Client, TestCase

class UrlsTestCase(TestCase):
    
    def setUp(self):
        User.objects.create_user('teste', 'teste@teste.com', 'teste')
    
#     def test_ver_tela(self):
#         """Testa ver a tela de login"""
#         c = Client()
#         response = c.get(reverse('login'))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, 'href="%s"' % reverse("password_reset"))
#         self.assertContains(response, 'href="%s"' % reverse("cadastro"))
#         
#     def test_realizar_login(self):
#         """Testa realizar login"""
#         c = Client()
#         response = c.post(reverse('login'), {'username': 'tester', 'password': 'tester'})
#         self.assertFormError(response, 'form', None, u'Usuário não encontrado.')
#         
#         response = c.post(reverse('login'), {'username': 'teste', 'password': 'tester'})
#         self.assertFormError(response, 'form', None, u'Senha inválida para o usuário.')
#         
#         response = c.post(reverse('login'), {'username': 'teste', 'password': 'teste'}, follow=True)
#         self.assertEqual(response.request['PATH_INFO'], reverse('inicio:painel_geral'))
        
    def test_responses_deslogado(self):
        """Testa respostas das páginas, deslogado"""
        url_list = [(url, '') for url in urlpatterns if url.app_name != 'admin']
        while len(url_list) > 0:
            tupla_atual = url_list.pop(0)
            url_atual = tupla_atual[0]
            namespace_atual = '%s:' % (tupla_atual[1]) if tupla_atual[1] != '' else ''
#             print tupla_atual
            if isinstance(url_atual, RegexURLResolver):
                for url_grupo in url_atual.url_patterns:
                    url_list.insert(0, (url_grupo, '%s%s' % (namespace_atual, (url_atual.namespace or ''))))
            elif isinstance(url_atual, RegexURLPattern):
                try:
                    response = self.client.get(reverse('%s%s' % (namespace_atual, url_atual.name)))
                    self.assertIn(response.status_code, [200, 302])
                except NoReverseMatch:
                    pass

    def test_responses_logado(self):
        """Testa respostas das páginas, deslogado"""
        self.client.login(username='teste', password='teste')
        url_list = [(url, '') for url in urlpatterns if url.app_name != 'admin']
        while len(url_list) > 0:
            tupla_atual = url_list.pop(0)
            url_atual = tupla_atual[0]
            namespace_atual = '%s:' % (tupla_atual[1]) if tupla_atual[1] != '' else ''
#             print tupla_atual
            if isinstance(url_atual, RegexURLResolver):
                for url_grupo in url_atual.url_patterns:
                    url_list.insert(0, (url_grupo, '%s%s' % (namespace_atual, (url_atual.namespace or ''))))
            elif isinstance(url_atual, RegexURLPattern):
                try:
                    response = self.client.get(reverse('%s%s' % (namespace_atual, url_atual.name)))
                    self.assertEqual(response.status_code, 200)
                except NoReverseMatch:
                    pass
