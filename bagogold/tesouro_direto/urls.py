# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^acompanhamento/$', views.acompanhamento_td, name='acompanhamento_td'),
    url(r'^buscar-titulos-validos-na-data/$', views.buscar_titulos_validos_na_data, name='buscar_titulos_validos_na_data'),
    url(r'^detalhar-titulo/(?P<titulo_id>\d+)/$', views.detalhar_titulo_td_id, name='detalhar_titulo_td_id'),
    url(r'^detalhar-titulo/(?P<titulo_tipo>[-\w]+)-(?P<titulo_ano>\d+)/$', views.detalhar_titulo_td_id, name='detalhar_titulo_td'),
    url(r'^editar-operacao/(?P<operacao_id>\d+)/$', views.editar_operacao_td, name='editar_operacao_td'),
    url(r'^historico/$', views.historico_td, name='historico_td'),
    url(r'^inserir-operacao-td/$', views.inserir_operacao_td, name='inserir_operacao_td'),
    url(r'^listar-historico-titulo/(?P<titulo_id>\d+)/$', views.listar_historico_titulo, name='listar_historico_titulo'),
    url(r'^listar-titulos-td/$', views.listar_titulos_td, name='listar_titulos_td'),
    url(r'^painel/$', views.painel, name='painel_td'),
    url(r'^sobre/$', views.sobre, name='sobre_td'),
    ]

