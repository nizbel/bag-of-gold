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
        id_tags = list(Tag.objects.all().values_list('id', flat=True))
        form = PostForm({'titulo': 'Teste', 'chamada_facebook': 'Veja teste', 'conteudo': u'<p>Isso é um teste</p>', 'tags': id_tags})
        self.assertTrue(form.is_valid(), msg=form.errors)
        self.assertEqual(form.cleaned_data['tags'], list(Tag.objects.filter(id__in=id_tags)))
    
    def test_tags_vazias(self):
        """Testar o formulário não passando tags"""
        form = PostForm({'titulo': 'Teste', 'chamada_facebook': 'Veja teste', 'conteudo': u'<p>Isso é um teste</p>'})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('tags' in form.errors)
    
    def test_tag_invalida(self):
        """Testar o formulário enviando uma tag que não existe"""
        id_tags = list(Tag.objects.all().values_list('id', flat=True))
        id_invalido = 1
        while id_invalido in id_tags:
            id_invalido += 1
        form = PostForm({'titulo': 'Teste', 'chamada_facebook': 'Veja teste', 'conteudo': u'<p>Isso é um teste</p>', 'tags': [id_tags[0], id_invalido]})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('tags' in form.errors)
        
