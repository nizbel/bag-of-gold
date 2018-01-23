# -*- coding: utf-8 -*-
from bagogold.blog.models import Post
from django.template.response import TemplateResponse

def criar_post(request):
    pass

def detalhar_post(request, post_slug):
    post = Post.objects.get(slug=post_slug)
    
    # Carregar Tags
    Tags = post.Tag
    
    return TemplateResponse(request, 'criptomoedas/editar_operacao_criptomoeda.html', {'post': post})  

def listar_posts(request):
    pass

def listar_posts_por_Tag(request, Tag_slug):
    pass

def listar_Tags(request):
    pass