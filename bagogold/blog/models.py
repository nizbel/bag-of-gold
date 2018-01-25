# -*- coding: utf-8 -*-k
from django.db import models

class Post (models.Model):
    titulo = models.CharField(u'Título', max_length=30)
    slug = models.SlugField(u'Slug', max_length=30, unique=True)
    conteudo = models.TextField(u'Conteúdo')
    data = models.DateTimeField(u'Data', auto_now_add=True)
    chamada_facebook = models.CharField(u'Chamada no Facebook', max_length=250)
    
    class Meta():
        unique_together=('slug',)
        
    def __unicode__(self):
        return self.titulo
    
    @property
    def tags(self):
        return [tag_post.tag for tag_post in self.tagpost_set.all()]
    
class Tag (models.Model):
    nome = models.CharField(u'Nome', max_length=30)
    slug = models.SlugField(u'Slug', max_length=30, unique=True)
    
    class Meta():
        unique_together=(('nome',), ('slug',))
        
    def __unicode__(self):
        return self.nome

class TagPost (models.Model):
    post = models.ForeignKey('Post')
    tag = models.ForeignKey('Tag')
    
    class Meta():
        unique_together=('post', 'tag')
        
    def __unicode__(self):
        return u'Post: %s, Tag: %s' % (self.post.slug, self.tag)