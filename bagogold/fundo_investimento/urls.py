# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^detalhar_fundo/(?P<id_fundo>\d+)/$', views.detalhar_fundo, name='detalhar_fundo'),
    url(r'^editar_operacao/(?P<id_operacao>\d+)/$', views.editar_operacao_fundo_investimento, name='editar_operacao_fundo_investimento'),
    url(r'^historico/$', views.historico, name='historico_fundo_investimento'),
    url(r'^inserir_operacao_fundo_investimento/$', views.inserir_operacao_fundo_investimento, name='inserir_operacao_fundo_investimento'),
    url(r'^listar_fundos/$', views.listar_fundos, name='listar_fundo_investimento'),
    url(r'^painel/$', views.painel, name='painel_fundo_investimento'),
    url(r'^sobre/$', views.sobre, name='sobre_fundo_investimento'),
    ]