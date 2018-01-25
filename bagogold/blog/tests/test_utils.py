# -*- coding: utf-8 -*-
from bagogold.blog.models import Post
from bagogold.blog.utils import criar_slug_post_valido
from django.test.testcases import TestCase
from django.utils.text import slugify

class CriacaoSlugs(TestCase):
    
    def test_criacao_slug_titulo_simples(self):
        """Testa criação de slug de Post com tamanho certo e sem posts"""
        post = Post(titulo=u'E assim começa', conteudo='teste', chamada_facebook='teste')
        post.slug = criar_slug_post_valido(post.titulo)
        post.save()
        self.assertEqual(Post.objects.all().count(), 1)
        self.assertEqual(post.slug, slugify(post.titulo))
        
    def test_criacao_slug_titulo_existente(self):
        """Testa criação de slug para Post com mesmo título"""
        Post.objects.create(titulo=u'E assim começa', conteudo='teste', chamada_facebook='teste', slug=slugify(u'E assim começa'))
        post = Post(titulo=u'E assim começa', conteudo='teste', chamada_facebook='teste')
        post.slug = criar_slug_post_valido(post.titulo)
        post.save()
        self.assertEqual(Post.objects.all().count(), 2)
        self.assertEqual(post.slug, slugify(post.titulo) + '-1')
    
    def test_criacao_slug_titulo_existente_maior_30_chars(self):
        """Testa criação de slug para Post com mesmo título que fique com mais de 30 caracteres"""
        pass
    
    def test_criacao_slug_titulo_varios_existentes(self):
        """Testa criação de slug de Post com título igual a 100 outros existentes"""
        for _ in xrange(100):
            titulo = u'E assim começa'
            Post.objects.create(titulo=titulo, conteudo='teste', chamada_facebook='teste', slug=criar_slug_post_valido(titulo))
        post = Post(titulo=u'E assim começa', conteudo='teste', chamada_facebook='teste')
        post.slug = criar_slug_post_valido(post.titulo)
        post.save()
        self.assertEqual(Post.objects.all().count(), 101)
        self.assertEqual(post.slug, slugify(post.titulo) + '-100')
        for _ in xrange(1,100):
            self.assertTrue(Post.objects.filter(slug='%s-%s' % (slugify(titulo), _)).exists(), msg='Erro no indice %s' % _)