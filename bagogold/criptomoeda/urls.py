# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
#     url(r'^detalhar-criptomoeda/(?P<id_criptomoeda>\d+)/$', views.detalhar_criptomoeda, name='detalhar_criptomoeda'),
    url(r'^editar-operacao/(?P<id_operacao>\d+)/$', views.editar_operacao_criptomoeda, name='editar_operacao_criptomoeda'),
    url(r'^editar-transferencia/(?P<id_transferencia>\d+)/$', views.editar_transferencia, name='editar_transferencia_criptomoeda'),
    url(r'^historico/$', views.historico, name='historico_criptomoeda'),
    url(r'^inserir-operacao-criptomoeda/$', views.inserir_operacao_criptomoeda, name='inserir_operacao_criptomoeda'),
    url(r'^inserir-transferencia/$', views.inserir_transferencia, name='inserir_transferencia_criptomoeda'),
    url(r'^listar-criptomoedas/$', views.listar_criptomoedas, name='listar_criptomoedas'),
    url(r'^listar-transferencias/$', views.listar_transferencias, name='listar_transferencias_criptomoeda'),
    url(r'^painel/$', views.painel, name='painel_criptomoeda'),
#     url(r'^sobre/$', views.sobre, name='sobre_criptomoeda'),
    ]