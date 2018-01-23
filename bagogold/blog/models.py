# -*- coding: utf-8 -*-k
from django.db import models

class Post (models.Model):
    titulo = models.CharField(u'Título', max_length=30, unique=True)
    slug = models.SlugField(u'Slug', max_length=30, unique=True)
    conteudo = models.TextField(u'Conteúdo')
    data = models.DateTimeField(u'Data', auto_now_add=True)
    chamada_facebook = models.CharField(u'Chamada no Facebook', max_length=250)
    
    class Meta():
        unique_together=('slug',)
        
    def __unicode__(self):
        return self.titulo
    
    def Tags(self):
        return [Tag_post.Tag for Tag_post in self.Tagpost_set.all()]
    
class Tag (models.Model):
    nome = models.CharField(u'Nome', max_length=30)
    slug = models.SlugField(u'Slug', max_length=30, unique=True)
    
    class Meta():
        unique_together=(('nome',), ('slug',))
        
    def __unicode__(self):
        return self.nome

class TagPost (models.Model):
    post = models.ForeignKey('Post')
    Tag = models.ForeignKey('Tag')
    
    class Meta():
        unique_together=('post', 'Tag')