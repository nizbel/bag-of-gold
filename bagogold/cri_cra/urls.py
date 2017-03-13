# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^detalhar_cri_cra/(?P<id_cri_cra>\d+)/$', views.cri_cra.detalhar_cri_cra, name='detalhar_cri_cra'),
    url(r'^editar_cri_cra/(?P<id_cri_cra>\d+)/$', views.cri_cra.editar_cri_cra, name='editar_cri_cra'),
#     url(r'^editar_operacao/(?P<id_operacao>\d+)/$', views.cri_cra.editar_operacao_cri_cra, name='editar_operacao_cri_cra'),
    url(r'^historico/$', views.cri_cra.historico, name='historico_cri_cra'),
    url(r'^inserir_cri_cra$', views.cri_cra.inserir_cri_cra, name='inserir_cri_cra'),
    url(r'^inserir_operacao_cri_cra$', views.cri_cra.inserir_operacao_cri_cra, name='inserir_operacao_cri_cra'),
    url(r'^listar_cri_cra$', views.cri_cra.listar_cri_cra, name='listar_cri_cra'),
    url(r'^painel/$', views.cri_cra.painel, name='painel_cri_cra'),
]
