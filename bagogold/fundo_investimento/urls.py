# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^detalhar-fundo/(?P<id_fundo>\d+)/$', views.detalhar_fundo, name='detalhar_fundo'),
    url(r'^editar-operacao/(?P<id_operacao>\d+)/$', views.editar_operacao_fundo_investimento, name='editar_operacao_fundo_investimento'),
    url(r'^historico/$', views.historico, name='historico_fundo_investimento'),
    url(r'^inserir-operacao-fundo-investimento/$', views.inserir_operacao_fundo_investimento, name='inserir_operacao_fundo_investimento'),
    url(r'^listar-fundos/$', views.listar_fundos, name='listar_fundo_investimento'),
    url(r'^listar-fundos-por-nome/$', views.listar_fundos_por_nome, name='listar_fundos_por_nome'),
    url(r'^listar-historico-fundo-investimento/(?P<id_fundo>\d+)/$', views.listar_historico_fundo_investimento, name='listar_historico_fundo_investimento'),
    url(r'^painel/$', views.painel, name='painel_fundo_investimento'),
    url(r'^sobre/$', views.sobre, name='sobre_fundo_investimento'),
    url(r'^verificar-historico-fundo-na-data/$', views.verificar_historico_fundo_na_data, name='verificar_historico_fundo_na_data'),
    ]