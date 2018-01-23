# -*- coding: utf-8 -*-k
from django.db import models

class Postagem (models.Model):
    titulo = models.CharField(u'Título', max_length=30, unique=True)
    slug = models.CharField(u'Slug', max_length=30, unique=True)
    conteudo = models.TextField(u'Conteúdo')
    data = models.DateTimeField(u'Data', auto_now_add=True)
    
    class Meta():
        unique_together=('slug',)
    
class Categoria (models.Model):
    nome = models.CharField(u'Nome', max_length=30)
    slug = models.CharField(u'Slug', max_length=30, unique=True)
    
    class Meta():
        unique_together=(('nome',), ('slug',))

class CategoriaPostagem (models.Model):
    postagem = models.ForeignKey('Postagem')
    categoria = models.ForeignKey('Categoria')
    
    class Meta():
        unique_together=('postagem', 'categoria')