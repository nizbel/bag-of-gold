# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^detalhar-investimento/(?P<id_investimento>\d+)/$', views.detalhar_investimento, name='detalhar_investimento'),
    url(r'^editar-amortizacao/(?P<id_amortizacao>\d+)/$', views.editar_amortizacao, name='editar_amortizacao'),
    url(r'^editar-investimento/(?P<id_investimento>\d+)/$', views.editar_investimento, name='editar_investimento'),
    url(r'^editar-rendimento/(?P<id_rendimento>\d+)/$', views.editar_rendimento, name='editar_rendimento'),
    url(r'^encerrar-investimento/(?P<id_investimento>\d+)/$', views.encerrar_investimento, name='encerrar_investimento'),
    url(r'^historico/$', views.historico, name='historico_outros_invest'),
    url(r'^inserir-amortizacao/(?P<investimento_id>\d+)/$', views.inserir_amortizacao, name='inserir_amortizacao'),
    url(r'^inserir-investimento/$', views.inserir_investimento, name='inserir_investimento'),
    url(r'^inserir-rendimento/(?P<investimento_id>\d+)/$', views.inserir_rendimento, name='inserir_rendimento'),
    url(r'^listar-investimentos/$', views.listar_investimentos, name='listar_investimentos'),
    url(r'^painel/$', views.painel, name='painel_outros_invest'),
    url(r'^sobre/$', views.sobre, name='sobre_outros_invest'),
    ]