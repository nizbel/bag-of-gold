# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^detalhar_fundo/(?P<id_fundo>\d+)/$', RedirectView.as_view(pattern_name='fundo_investimento:detalhar_fundo_id', permanent=True)),
    url(r'^detalhar_fundo/(?P<slug_fundo>[-\w]+)/$', RedirectView.as_view(pattern_name='fundo_investimento:detalhar_fundo', permanent=True)),
    url(r'^editar_operacao/(?P<id_operacao>\d+)/$', RedirectView.as_view(pattern_name='fundo_investimento:editar_operacao_fundo_investimento', permanent=True)),
    url(r'^historico/$', RedirectView.as_view(pattern_name='fundo_investimento:historico_fundo_investimento', permanent=True)),
    url(r'^inserir_operacao_fundo_investimento/$', RedirectView.as_view(pattern_name='fundo_investimento:inserir_operacao_fundo_investimento', permanent=True)),
    url(r'^listar_fundos/$', RedirectView.as_view(pattern_name='fundo_investimento:listar_fundo_investimento', permanent=True)),
    url(r'^listar_fundos_por_nome/$', RedirectView.as_view(pattern_name='fundo_investimento:listar_fundos_por_nome', permanent=True)),
    url(r'^listar_historico_fundo_investimento/(?P<id_fundo>\d+)/$', RedirectView.as_view(pattern_name='fundo_investimento:listar_historico_fundo_investimento', permanent=True)),
    url(r'^painel/$', RedirectView.as_view(pattern_name='fundo_investimento:painel_fundo_investimento', permanent=True)),
    url(r'^sobre/$', RedirectView.as_view(pattern_name='fundo_investimento:sobre_fundo_investimento', permanent=True)),
    url(r'^verificar_historico_fundo_na_data/$', RedirectView.as_view(pattern_name='fundo_investimento:verificar_historico_fundo_na_data', permanent=True)),
    ]