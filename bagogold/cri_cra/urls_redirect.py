# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^detalhar_cri_cra/(?P<id_cri_cra>\d+)/$', RedirectView.as_view(pattern_name='detalhar_cri_cra', permanent=True)),
    url(r'^editar_cri_cra/(?P<id_cri_cra>\d+)/$', RedirectView.as_view(pattern_name='editar_cri_cra', permanent=True)),
    url(r'^editar_operacao/(?P<id_operacao>\d+)/$', RedirectView.as_view(pattern_name='editar_operacao_cri_cra', permanent=True)),
    url(r'^historico/$', RedirectView.as_view(pattern_name='historico_cri_cra', permanent=True)),
    url(r'^inserir_cri_cra/$', RedirectView.as_view(pattern_name='inserir_cri_cra', permanent=True)),
    url(r'^inserir_operacao_cri_cra/$', RedirectView.as_view(pattern_name='inserir_operacao_cri_cra', permanent=True)),
    url(r'^listar_cri_cra/$', RedirectView.as_view(pattern_name='listar_cri_cra', permanent=True)),
    url(r'^painel/$', RedirectView.as_view(pattern_name='painel_cri_cra', permanent=True)),
    url(r'^sobre/$', RedirectView.as_view(pattern_name='sobre_cri_cra', permanent=True)),
]
