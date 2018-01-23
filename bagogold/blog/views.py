# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.blog.models import Post, Tag
from django.template.response import TemplateResponse

def criar_post(request):
    pass

@adiciona_titulo_descricao('Detalhar post', '')
def detalhar_post(request, post_slug):
    post = Post.objects.get(slug=post_slug)
    
    posts_recentes = Post.objects.all().order_by('-data')[:6]
    
    tags = Tag.objects.all()
    
    return TemplateResponse(request, 'blog/detalhar_post.html', {'post': post, 'tags': tags, 'posts_recentes': posts_recentes})  

def listar_posts(request):
    pass

def listar_posts_por_tag(request, tag_slug):
    pass

def listar_tags(request):
    pass