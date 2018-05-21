# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^detalhar-debenture/(?P<debenture_id>\d+)/$', views.detalhar_debenture, name='detalhar_debenture'),
    url(r'^editar-operacao/(?P<operacao_id>\d+)/$', views.editar_operacao_debenture, name='editar_operacao_debenture'),
    url(r'^historico/$', views.historico, name='historico_debenture'),
    url(r'^inserir-operacao-debenture/$', views.inserir_operacao_debenture, name='inserir_operacao_debenture'),
    url(r'^listar-debentures/$', views.listar_debentures, name='listar_debentures'),
    url(r'^listar-debentures-validas-na-data/$', views.listar_debentures_validas_na_data, name='listar_debentures_validas_na_data'),
    url(r'^painel/$', views.painel, name='painel_debenture'),
    url(r'^sobre/$', views.sobre, name='sobre_debenture'),
    ]
