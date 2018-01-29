# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.utils.investidores import is_superuser
from bagogold.blog.forms import PostForm
from bagogold.blog.models import Post, Tag, TagPost
from bagogold.blog.utils import criar_slug_post_valido
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import mail_admins
from django.core.paginator import Paginator
from django.db import transaction
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
import json
import traceback

@login_required
@adiciona_titulo_descricao('Detalhar post', '')
def detalhar_post(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)
    
    if Post.objects.filter(data__lt=post.data).order_by('-data').exists():
        post.post_anterior = Post.objects.filter(data__lt=post.data).order_by('-data')[0].slug
    if Post.objects.filter(data__gt=post.data).order_by('data').exists():
        post.proximo_post = Post.objects.filter(data__gt=post.data).order_by('data')[0].slug
    
    posts_recentes = Post.objects.all().order_by('-data')[:6]
    
    tags = Tag.objects.all()
    
    return TemplateResponse(request, 'blog/detalhar_post.html', {'post': post, 'tags': tags, 'posts_recentes': posts_recentes})  

@login_required
@adiciona_titulo_descricao('Listar posts', '')
def listar_posts(request):
#     # TODO APAGAR TESTE
#     Post.objects.filter(titulo='Lorem').delete()
#     while Post.objects.all().count() < 30:
#         titulo = 'Lorem'
#         novo_post = Post.objects.create(conteudo="""Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi elit diam, dignissim vel massa sed, eleifend rutrum eros. Etiam vehicula, dolor eget consequat malesuada, lacus nulla congue sem, sit amet luctus dolor urna eget dui. Quisque ultricies hendrerit ante, eu pulvinar orci rhoncus sed. Sed ut maximus risus. Sed et odio magna. Duis aliquam est finibus ligula molestie posuere. Nulla gravida condimentum dui, a consectetur nulla dignissim vitae. Etiam quam purus, accumsan non tincidunt quis, hendrerit sed metus. Nullam ipsum est, semper ut nibh non, consectetur bibendum arcu. Vestibulum at gravida tortor. Vivamus justo neque, cursus rhoncus mi eget, porta lobortis ipsum. Aenean dignissim nisl et dolor porta, non ornare leo viverra. Nulla ullamcorper leo in lacus facilisis porta. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.
# 
# Nam mattis quam ut dolor hendrerit lobortis. Proin condimentum dolor a risus placerat, vulputate accumsan sem vulputate. Aliquam ornare, eros nec volutpat pretium, dui felis hendrerit elit, sit amet congue nulla magna et mi. Curabitur interdum, justo a mollis viverra, magna purus congue nisl, vitae tempor ipsum lacus id eros. Aliquam erat volutpat. Etiam ultrices sit amet nibh quis faucibus. Nunc vestibulum iaculis laoreet. Etiam vitae hendrerit lacus, vitae scelerisque justo. Pellentesque metus massa, egestas non nibh et, ornare eleifend neque. Vestibulum porttitor lectus a ex vestibulum commodo. In vel lacus ac urna pellentesque dapibus nec ac augue.
# 
# Pellentesque molestie gravida tellus id eleifend. Integer erat odio, ultricies eget volutpat quis, luctus id elit. Sed vel sem semper, tincidunt lorem vel, lobortis ligula. Cras rhoncus imperdiet enim, sed accumsan odio blandit at. Integer dui sapien, lacinia sagittis enim id, dictum congue purus. Fusce eleifend interdum augue, sed aliquam enim sagittis a. Donec est nisi, euismod a orci sed, vehicula viverra sapien. Aliquam scelerisque efficitur aliquet. Fusce ornare ultrices felis convallis luctus. Ut ut condimentum neque. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Etiam vitae est ac enim maximus dignissim. Curabitur condimentum nec lectus quis posuere. Proin nibh odio, consequat at porta bibendum, laoreet eget nisi. Phasellus tempor sapien in arcu rhoncus, ac aliquam augue mattis.
# 
# Mauris egestas elit vel nisl porta fringilla. In hac habitasse platea dictumst. Curabitur ullamcorper lacinia neque, sit amet sodales metus finibus ut. Ut justo neque, vulputate vitae ante in, ultricies molestie leo. Duis non auctor ipsum. Sed pharetra nulla in felis aliquet, ut convallis ligula scelerisque. Suspendisse non libero porttitor, volutpat orci non, rutrum velit. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Mauris ac mattis mauris. Nulla facilisi.
# 
# Aliquam volutpat egestas auctor. Morbi nulla lectus, porttitor in viverra at, finibus at nisl. Donec ut leo at dui dictum tempus at quis nisl. Fusce sit amet mollis est. Maecenas sed erat pellentesque sapien ultrices tincidunt. Maecenas sed ex condimentum libero pellentesque ultrices ac eget dolor. Nunc pulvinar eget elit sed pulvinar. Pellentesque ut odio turpis. Cras gravida commodo ex, a rhoncus libero aliquet at.""",
# chamada_facebook='lorem', slug=criar_slug_post_valido(titulo), titulo=titulo)
#         test = randint(1, 3)
#         if test == 1:
#             TagPost.objects.create(tag=Tag.objects.get(nome=u'Alterações'), post=novo_post)
#             TagPost.objects.create(tag=Tag.objects.get(nome=u'Investimentos'), post=novo_post)
#         elif test == 2:
#             TagPost.objects.create(tag=Tag.objects.get(nome=u'Alterações'), post=novo_post)
#         elif test == 3:
#             TagPost.objects.create(tag=Tag.objects.get(nome=u'Investimentos'), post=novo_post)
    
    
    # Verificar pagina para paginação
    try:
        pagina = int(request.GET.get('pagina', 1))
    except:
        pagina = 1

    # Buscar posts
    posts = Post.objects.all().order_by('-data')
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
                        
                    raise ValueError('TESTE')
                        
                    # TODO criar post no facebook
                    # post.url_facebook = retorno_post_facebook(url=reverse('blog:detalhar_post', post.slug))
                    # if falha:
                    #    raise ValueError('erro ao postar no facebook')
            except:
                messages.error(request, u'Erro ao criar post')
                if settings.ENV == 'DEV':
                    print traceback.format_exc()
                elif settings.ENV == 'PROD':
                    mail_admins(u'Erro ao criar post', traceback.format_exc().decode('utf-8'))
    else:
        post_form = PostForm()
    
    return TemplateResponse(request, 'blog/inserir_post.html', {'post_form': post_form, 'sem_menu_lateral': True})  
    
@login_required
@user_passes_test(is_superuser)
@adiciona_titulo_descricao('Editar post', '')
def editar_post(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)

    if request.POST:
        post_form = PostForm(request.POST, instance=post)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.slug = criar_slug_post_valido(post.titulo)
            try:
                with transaction.atomic():
                    post.save()
            except:
                messages.error(request, u'Erro ao editar post')
                if settings.ENV == 'DEV':
                    print traceback.format_exc()
                elif settings.ENV == 'PROD':
                    mail_admins(u'Erro ao editar post', traceback.format_exc().decode('utf-8'))
    else:
        post_form = PostForm(instance=post)
    
    return TemplateResponse(request, 'blog/editar_post.html', {'post_form': post_form, 'sem_menu_lateral': True}) 