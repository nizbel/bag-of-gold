# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^detalhar-cdb-rdb/(?P<cdb_rdb_id>\d+)/$', views.detalhar_cdb_rdb, name='detalhar_cdb_rdb'),
    url(r'^editar-cdb-rdb/(?P<cdb_rdb_id>\d+)/$', views.editar_cdb_rdb, name='editar_cdb_rdb'),
    url(r'^editar-historico-carencia/(?P<historico_carencia_id>\d+)/$', views.editar_historico_carencia, name='editar_historico_carencia'),
    url(r'^editar-historico-porcentagem/(?P<historico_porcentagem_id>\d+)/$', views.editar_historico_porcentagem, name='editar_historico_porcentagem'),
    url(r'^editar-historico-vencimento/(?P<historico_vencimento_id>\d+)/$', views.editar_historico_vencimento, name='editar_historico_vencimento'),
    url(r'^editar-operacao/(?P<id_operacao>\d+)/$', views.editar_operacao_cdb_rdb, name='editar_operacao_cdb_rdb'),
    url(r'^historico/$', views.historico, name='historico_cdb_rdb'),
    url(r'^inserir-cdb-rdb/$', views.inserir_cdb_rdb, name='inserir_cdb_rdb'),
    url(r'^inserir-operacao-cdb-rdb/$', views.inserir_operacao_cdb_rdb, name='inserir_operacao_cdb_rdb'),
    url(r'^listar-cdb-rdb/$', views.listar_cdb_rdb, name='listar_cdb_rdb'),
    url(r'^inserir-historico-carencia-cdb-rdb/(?P<cdb_rdb_id>\d+)/$', views.inserir_historico_carencia_cdb_rdb, name='inserir_historico_carencia_cdb_rdb'),
    url(r'^inserir-historico-porcentagem-cdb-rdb/(?P<cdb_rdb_id>\d+)/$', views.inserir_historico_porcentagem_cdb_rdb, name='inserir_historico_porcentagem_cdb_rdb'),
    url(r'^inserir-historico-vencimento-cdb-rdb/(?P<cdb_rdb_id>\d+)/$', views.inserir_historico_vencimento_cdb_rdb, name='inserir_historico_vencimento_cdb_rdb'),
    url(r'^painel/$', views.painel, name='painel_cdb_rdb'),
    url(r'^sobre/$', views.sobre, name='sobre_cdb_rdb'),
    ]