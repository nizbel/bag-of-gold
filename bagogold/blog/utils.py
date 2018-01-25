# -*- coding: utf-8 -*-
from bagogold.blog.models import Post
from django.db import transaction
from django.utils.text import slugify
from urllib2 import urlopen
import datetime
import json

def criar_slug_tag_valido():
    pass

def criar_slug_post_valido(titulo):
    slug = slugify(titulo)
    # Verifica se já existe o slug de Post criado
    if Post.objects.filter(slug=slug).exists():
        # Adicionar numeral ao final do slug, mantendo o limite de 30 caracteres
        
        # Buscar último post com esse título
        ultimo_post_mesmo_titulo = Post.objects.filter(titulo=titulo).order_by('-data')[0]
        slug_ultimo_post = ultimo_post_mesmo_titulo.slug
        final_slug = slug_ultimo_post[slug_ultimo_post.rfind('-')+1:]
        # Número do slug
        numero_slug = 1 if not final_slug.isdigit() else int(final_slug)+1
        
        # Criar slug temporário para verificar tamanho
        slug_temp = u'%s-%s' % (slug, numero_slug)
        while len(slug_temp) > 30:
            slug = slug[:-1]
            slug_temp = u'%s-%s' % (slug, numero_slug)
        slug = slug_temp
    return slug

def postar_facebook():
    pass
