# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^detalhar-lci-lca/(?P<lci_lca_id>\d+)/$', views.detalhar_lci_lca, name='detalhar_lci_lca'),
    url(r'^editar-historico-carencia/(?P<historico_carencia_id>\d+)/$', views.editar_historico_carencia, name='editar_historico_carencia_lci_lca'),
    url(r'^editar-historico-porcentagem/(?P<historico_porcentagem_id>\d+)/$', views.editar_historico_porcentagem, name='editar_historico_porcentagem_lci_lca'),
    url(r'^editar-lci-lca/(?P<lci_lca_id>\d+)/$', views.editar_lci_lca, name='editar_lci_lca'),
    url(r'^editar-operacao/(?P<id>\d+)/$', views.editar_operacao_lci_lca, name='editar_operacao_lci_lca'),
    url(r'^historico/$', views.historico, name='historico_lci_lca'),
    url(r'^inserir-lci-lca/$', views.inserir_lci_lca, name='inserir_lci_lca'),
    url(r'^inserir-operacao-lci-lca/$', views.inserir_operacao_lci_lca, name='inserir_operacao_lci_lca'),
    url(r'^listar-letras-credito/$', views.listar_lci_lca, name='listar_lci_lca'),
    url(r'^listar-operacoes-passada-carencia/$', views.listar_operacoes_passada_carencia, name='listar_operacoes_passada_carencia'),
    url(r'^inserir-historico-carencia-lci-lca/(?P<lci_lca_id>\d+)/$', views.inserir_historico_carencia, name='inserir_historico_carencia_lci_lca'),
    url(r'^inserir-historico-porcentagem-lci-lca/(?P<lci_lca_id>\d+)/$', views.inserir_historico_porcentagem, name='inserir_historico_porcentagem_lci_lca'),
    url(r'^painel/$', views.painel, name='painel_lci_lca'),
    url(r'^sobre/$', views.sobre, name='sobre_lci_lca'),
    ]