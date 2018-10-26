# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.utils.investidores import is_superuser
from bagogold.blog.forms import PostForm
from bagogold.blog.models import Post, Tag, TagPost
from bagogold.blog.utils import criar_slug_post_valido, postar_facebook
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import mail_admins
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
import json
import re
import traceback
from django.db.models.query import Prefetch

@adiciona_titulo_descricao('Detalhar post', '')
def detalhar_post(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)

    # Preparar preview para o facebook
    post.conteudo_fb = post.conteudo[:post.conteudo.find('</p>')]
    post.conteudo_fb = re.sub('<[^<\s]+?>', '', post.conteudo_fb)
    
    if Post.objects.filter(data__lt=post.data).order_by('-data').exists():
        post.post_anterior = Post.objects.filter(data__lt=post.data).order_by('-data')[0].slug
    if Post.objects.filter(data__gt=post.data).order_by('data').exists():
        post.proximo_post = Post.objects.filter(data__gt=post.data).order_by('data')[0].slug
    
    posts_recentes = Post.objects.all().order_by('-data')[:6]
    
    tags = Tag.objects.all()
    
    return TemplateResponse(request, 'blog/detalhar_post.html', {'post': post, 'tags': tags, 'posts_recentes': posts_recentes})  

@login_required
@user_passes_test(is_superuser)
@adiciona_titulo_descricao('Editar post', '')
def editar_post(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)

    if request.POST:
        post_form = PostForm(request.POST, instance=post)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            try:
                with transaction.atomic():
                    post.save()
                    for tag in post_form.cleaned_data['tags']:
                        if not TagPost.objects.filter(tag=tag, post=post).exists():
                            TagPost.objects.create(tag=tag, post=post)
                    for tag in TagPost.objects.filter(post=post).exclude(tag__in=post_form.cleaned_data['tags']):
                        tag.delete()
                    
                return HttpResponseRedirect(reverse('blog:detalhar_post', kwargs={'post_slug': post.slug}))
                    
            except:
                messages.error(request, u'Erro ao editar post')
                if settings.ENV == 'DEV':
                    print traceback.format_exc()
                elif settings.ENV == 'PROD':
                    mail_admins(u'Erro ao editar post', traceback.format_exc().decode('utf-8'))
    else:
        post_form = PostForm(instance=post, initial={'tags': [tag.id for tag in post.tags]})
    
    return TemplateResponse(request, 'blog/editar_post.html', {'post_form': post_form, 'sem_menu_lateral': True}) 

@login_required
@user_passes_test(is_superuser)
@adiciona_titulo_descricao('Criar novo post', '')
def inserir_post(request):
    if request.POST:
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.slug = criar_slug_post_valido(post.titulo)
            
            # TODO linkar com facebook
            try:
                with transaction.atomic():
                    post.save()
                    for tag in post_form.cleaned_data['tags']:
                        TagPost.objects.create(tag=tag, post=post)
                        
                post.url_facebook = 'https://bagofgold.com.br%s' % reverse('blog:detalhar_post', kwargs={'post_slug': post.slug})
                
                sucesso = postar_facebook(mensagem=post.chamada_facebook, link=post.url_facebook)
                if not sucesso:
                    raise ValueError('Erro ao postar no facebook')
                
                return HttpResponseRedirect(reverse('blog:detalhar_post', kwargs={'post_slug': post.slug}))
            except:
                post.delete()
                messages.error(request, u'Erro ao criar post')
                if settings.ENV == 'DEV':
                    print traceback.format_exc()
                elif settings.ENV == 'PROD':
                    mail_admins(u'Erro ao criar post', traceback.format_exc().decode('utf-8'))
    else:
        post_form = PostForm()
    
    return TemplateResponse(request, 'blog/inserir_post.html', {'post_form': post_form, 'sem_menu_lateral': True})  
    
@adiciona_titulo_descricao('Listar posts', '')
def listar_posts(request):
    # Verificar pagina para paginação
    try:
        pagina = int(request.GET.get('pagina', 1))
    except:
        pagina = 1

    # Buscar posts
    posts = Post.objects.all().order_by('-data').prefetch_related(Prefetch('tagpost_set__tag', queryset=Tag.objects.order_by('nome')))
    # Paginar posts
    paginador_posts = Paginator(posts, 9)
    if pagina > paginador_posts.num_pages:
        pagina = paginador_posts.num_pages
    paginador_posts.pagina = pagina
    
    # Verificar se é requisição ajax (atualizar apenas lista de posts
    if request.is_ajax():
        return HttpResponse(json.dumps(render_to_string('blog/utils/lista_posts.html', {'posts': paginador_posts.page(pagina).object_list})), content_type = "application/json")
    else:
        posts_recentes = Post.objects.all().order_by('-data')[:6]
    
        tags = Tag.objects.all().order_by('nome')
        
        return TemplateResponse(request, 'blog/listar_posts.html', {'posts': paginador_posts.page(pagina).object_list, 'paginador': paginador_posts,
                                                                    'tags': tags, 'posts_recentes': posts_recentes})  

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
    # Paginar posts
    paginador_posts = Paginator(posts, 9)
    if pagina > paginador_posts.num_pages:
        pagina = paginador_posts.num_pages
    paginador_posts.pagina = pagina
    
    # Verificar se é requisição ajax (atualizar apenas lista de posts
    if request.is_ajax():
        return HttpResponse(json.dumps(render_to_string('blog/utils/lista_posts.html', {'posts': paginador_posts.page(pagina).object_list, 
                                                                                        'tag_filtro': tag})), content_type = "application/json")
    else:
        posts_recentes = Post.objects.all().order_by('-data')[:6]
    
        tags = Tag.objects.all().order_by('nome')
        
        return TemplateResponse(request, 'blog/listar_posts.html', {'posts': paginador_posts.page(pagina).object_list, 'paginador': paginador_posts,
                                                                    'tags': tags, 'posts_recentes': posts_recentes, 'tag_filtro': tag})  


# Views para URLs do app do facebook
def privacy_policy(request):
    return TemplateResponse(request, 'fb/privacy_policy.html', {})

def tos(request):
    return TemplateResponse(request, 'fb/tos.html', {})