# -*- coding: utf-8 -*-
from bagogold.blog.forms import PostForm
from bagogold.blog.models import Tag
from django.test.testcases import TestCase

class FormPostTestCase(TestCase):
    
    def setUp(self):
        Tag.objects.create(nome=u'Alterações', slug='alteracoes')
        Tag.objects.create(nome=u'Investimentos', slug='investimentos')
    
    def test_sucesso(self):
        """Testar o formulário de post no caso de conteúdo OK"""
        form = PostForm({'titulo': 'Teste', 'chamada_facebook': 'Veja teste', 'conteudo': u'<p>Isso é um teste</p>', 'tags': [u'1', u'2']})
        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data['tags'], list(Tag.objects.filter(id__in=[1, 2])))
    
    def test_tags_vazias(self):
        """Testar o formulário não passando tags"""
        form = PostForm({'titulo': 'Teste', 'chamada_facebook': 'Veja teste', 'conteudo': u'<p>Isso é um teste</p>'})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('tags' in form.errors)
    
    def test_tag_invalida(self):
        """Testar o formulário enviando uma tag que não existe"""
        form = PostForm({'titulo': 'Teste', 'chamada_facebook': 'Veja teste', 'conteudo': u'<p>Isso é um teste</p>', 'tags': [u'1', u'3']})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('tags' in form.errors)
        
