# -*- coding: utf-8 -*-
from django.conf.urls import url
import bagogold.lc.views as views

urlpatterns = [
    url(r'^detalhar-lc/(?P<lc_id>\d+)/$', views.detalhar_lc, name='detalhar_lc'),
    url(r'^editar-lc/(?P<lc_id>\d+)/$', views.editar_lc, name='editar_lc'),
    url(r'^editar-historico-carencia/(?P<historico_carencia_id>\d+)/$', views.editar_historico_carencia, name='editar_historico_carencia'),
    url(r'^editar-historico-porcentagem/(?P<historico_porcentagem_id>\d+)/$', views.editar_historico_porcentagem, name='editar_historico_porcentagem'),
    url(r'^editar-historico-vencimento/(?P<historico_vencimento_id>\d+)/$', views.editar_historico_vencimento, name='editar_historico_vencimento'),
    url(r'^editar-operacao/(?P<id_operacao>\d+)/$', views.editar_operacao_lc, name='editar_operacao_lc'),
    url(r'^historico/$', views.historico, name='historico_lc'),
    url(r'^inserir-lc/$', views.inserir_lc, name='inserir_lc'),
    url(r'^inserir-operacao-lc/$', views.inserir_operacao_lc, name='inserir_operacao_lc'),
    url(r'^listar-lc/$', views.listar_lc, name='listar_lc'),
    url(r'^inserir-historico-carencia-lc/(?P<lc_id>\d+)/$', views.inserir_historico_carencia_lc, name='inserir_historico_carencia_lc'),
    url(r'^inserir-historico-porcentagem-lc/(?P<lc_id>\d+)/$', views.inserir_historico_porcentagem_lc, name='inserir_historico_porcentagem_lc'),
    url(r'^inserir-historico-vencimento-lc/(?P<lc_id>\d+)/$', views.inserir_historico_vencimento_lc, name='inserir_historico_vencimento_lc'),
    url(r'^painel/$', views.painel, name='painel_lc'),
    url(r'^sobre/$', views.sobre, name='sobre_lc'),
    ]
