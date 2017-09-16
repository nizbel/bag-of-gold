# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^detalhar_investimento/(?P<id_investimento>\d+)/$', views.detalhar_investimento, name='detalhar_investimento'),
    url(r'^historico/$', views.historico, name='historico_outros_invest'),
    url(r'^inserir_investimento/$', views.inserir_investimento, name='inserir_investimento'),
    url(r'^listar_investimentos/$', views.listar_investimentos, name='listar_investimentos'),
    url(r'^painel/$', views.painel, name='painel_outros_invest'),
    url(r'^sobre/$', views.sobre, name='sobre_outros_invest'),
    ]