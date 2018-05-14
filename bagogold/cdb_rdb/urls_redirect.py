# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^detalhar_cdb_rdb/(?P<cdb_rdb_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:detalhar_cdb_rdb', permanent=True)),
    url(r'^editar_cdb_rdb/(?P<cdb_rdb_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:editar_cdb_rdb', permanent=True)),
    url(r'^editar_historico_carencia/(?P<historico_carencia_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:editar_historico_carencia', permanent=True)),
    url(r'^editar_historico_porcentagem/(?P<historico_porcentagem_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:editar_historico_porcentagem', permanent=True)),
    url(r'^editar_historico_vencimento/(?P<historico_vencimento_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:editar_historico_vencimento', permanent=True)),
    url(r'^editar_operacao/(?P<operacao_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:editar_operacao_cdb_rdb', permanent=True)),
    url(r'^historico/$', RedirectView.as_view(pattern_name='cdb_rdb:historico_cdb_rdb', permanent=True)),
    url(r'^inserir_cdb_rdb/$', RedirectView.as_view(pattern_name='cdb_rdb:inserir_cdb_rdb', permanent=True)),
    url(r'^inserir_operacao_cdb_rdb/$', RedirectView.as_view(pattern_name='cdb_rdb:inserir_operacao_cdb_rdb', permanent=True)),
    url(r'^listar_cdb_rdb/$', RedirectView.as_view(pattern_name='cdb_rdb:listar_cdb_rdb', permanent=True)),
    url(r'^inserir_historico_carencia_cdb_rdb/(?P<cdb_rdb_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:inserir_historico_carencia_cdb_rdb', permanent=True)),
    url(r'^inserir_historico_porcentagem_cdb_rdb/(?P<cdb_rdb_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:inserir_historico_porcentagem_cdb_rdb', permanent=True)),
    url(r'^inserir_historico_vencimento_cdb_rdb/(?P<cdb_rdb_id>\d+)/$', RedirectView.as_view(pattern_name='cdb_rdb:inserir_historico_vencimento_cdb_rdb', permanent=True)),
    url(r'^painel/$', RedirectView.as_view(pattern_name='cdb_rdb:painel_cdb_rdb', permanent=True)),
    url(r'^sobre/$', RedirectView.as_view(pattern_name='cdb_rdb:sobre_cdb_rdb', permanent=True)),
    ]