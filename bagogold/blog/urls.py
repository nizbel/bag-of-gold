# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^editar-post/(?P<post_slug>[\w-]+)/$', views.editar_post, name='editar_post'),
    url(r'^novo-post/$', views.inserir_post, name='novo_post'),
    url(r'^posts/$', views.listar_posts, name='listar_posts'),
    url(r'^post/(?P<post_slug>[\w-]+)/$', views.detalhar_post, name='detalhar_post'),
    url(r'^tag/(?P<tag_slug>[\w-]+)/posts/$', views.listar_posts_por_tag, name='listar_posts_por_tag'),
    ]