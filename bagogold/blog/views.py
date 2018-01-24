# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.blog.models import Post, Tag
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
import json

def criar_post(request):
    pass

@login_required
@adiciona_titulo_descricao('Detalhar post', '')
def detalhar_post(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)
    
    posts_recentes = Post.objects.all().order_by('-data')[:6]
    
    tags = Tag.objects.all()
    
    return TemplateResponse(request, 'blog/detalhar_post.html', {'post': post, 'tags': tags, 'posts_recentes': posts_recentes})  

@login_required
@adiciona_titulo_descricao('Listar posts', '')
def listar_posts(request):
    # Verificar pagina para paginação
    try:
        pagina = int(request.GET.get('pagina', 1))
    except:
        pagina = 1

    # Buscar posts
    posts = Post.objects.all().order_by('-data')
    # Paginar fundos
    paginador_posts = Paginator(posts, 9)
    if pagina > paginador_posts.num_pages:
        pagina = paginador_posts.num_pages
    
    # Verificar se é requisição ajax (atualizar apenas lista de posts
    if request.is_ajax():
        return HttpResponse(json.dumps(render_to_string('blog/utils/lista_posts.html', {'posts': paginador_posts.page(pagina).object_list, 
                                                                                        'paginador': paginador_posts})), content_type = "application/json")
    else:
        posts_recentes = Post.objects.all().order_by('-data')[:6]
    
        tags = Tag.objects.all()
        
        return TemplateResponse(request, 'blog/listar_posts.html', {'posts': paginador_posts.page(pagina).object_list, 'paginador': paginador_posts,
                                                                    'tags': tags, 'posts_recentes': posts_recentes})  

@login_required
@adiciona_titulo_descricao('Listar posts por tag', '')
def listar_posts_por_tag(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    
    # Verificar pagina para paginação
    try:
        pagina = int(request.GET.get('pagina', 1))
    except:
        pagina = 1

    # Buscar posts
    
    posts = Post.objects.filter(tagpost__tag=tag).order_by('-data')
    # Paginar fundos
    paginador_posts = Paginator(posts, 9)
    if pagina > paginador_posts.num_pages:
        pagina = paginador_posts.num_pages
    
    # Verificar se é requisição ajax (atualizar apenas lista de posts
    if request.is_ajax():
        return HttpResponse(json.dumps(render_to_string('blog/utils/lista_posts.html', {'posts': paginador_posts.page(pagina).object_list, 
                                                                                        'paginador': paginador_posts})), content_type = "application/json")
    else:
        posts_recentes = Post.objects.all().order_by('-data')[:6]
    
        tags = Tag.objects.all()
        return TemplateResponse(request, 'blog/listar_posts.html', {'posts': paginador_posts.page(pagina).object_list, 'paginador': paginador_posts,
                                                                    'tags': tags, 'posts_recentes': posts_recentes})  

@login_required
@require('is_superuser)
@adiciona_titulo_descricao('Criar novo post', '')
def inserir_post(request):
    if request.POST:
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            post = post_form.save(false)
            post.slug = gerar_slug_post(post.titulo)
            
            # TODO linkar com facebook
            try:
                with transaction.atomic():
                    post.save()
                    # TODO criar post no facebook
                    # post.url_facebook = retorno_post_facebook(url=reverse('blog:detalhar_post', post.slug))
                    # if falha:
                    #    raise ValueError('erro ao postar no facebook')
            except:
                messages.error(request, u'Erro ao criar post')
                if settings.ENV == 'DEV':
                    print traceback.format_exc()
                elif settings.ENV == 'PROD':
                    mail_admins(erro)
    else:
        post_form = PostForm()
    
    return TemplateResponse(request, 'blog/inserir_post.html', {'post_form': post_form})  
    
@login_required
@require('is_superuser)
@adiciona_titulo_descricao('Editar post', '')
def editar_post(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)

    if request.POST:
        post_form = PostForm(request.POST, instance=post)
        if post_form.is_valid():
            post = post_form.save(false)
            post.slug = gerar_slug_post(post.titulo)
            
            # TODO linkar com facebook
            try:
                with transaction.atomic():
                    post.save()
                    # TODO criar post no facebook
                    # post.url_facebook = retorno_post_facebook(url=reverse('blog:detalhar_post', post.slug))
                    # if falha:
                    #    raise ValueError('erro ao postar no facebook')
            except:
                messages.error(request, u'Erro ao editar post')
                if settings.ENV == 'DEV':
                    print traceback.format_exc()
                elif settings.ENV == 'PROD':
                    mail_admins(erro)
    else:
        post_form = PostForm(instance=post)
    
    return TemplateResponse(request, 'blog/inserir_post.html', {'post_form': post_form}) 