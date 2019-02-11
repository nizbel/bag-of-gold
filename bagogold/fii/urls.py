# -*- coding: utf-8 -*-
from django.conf.urls import url
import bagogold.fii.views as views

urlpatterns = [
#     url(r'^acompanhamento-mensal/$', views.acompanhamento_mensal_fii, name='acompanhamento_mensal_fii'),
    url(r'^acompanhamento/$', views.acompanhamento_fii, name='acompanhamento_fii'),
    url(r'^calcular-resultado-corretagem/$', views.calcular_resultado_corretagem, name='calcular_resultado_corretagem'),
    url(r'^detalhar-fii/(?P<fii_id>\d+)/$', views.detalhar_fii_id, name='detalhar_fii_id'),
    url(r'^detalhar-fii/(?P<fii_ticker>[\w\d]+)/$', views.detalhar_fii, name='detalhar_fii'),
    url(r'^detalhar-provento/(?P<provento_id>\d+)/$', views.detalhar_provento, name='detalhar_provento_fii'),
    url(r'^editar-operacao/(?P<id_operacao>\d+)/$', views.editar_operacao_fii, name='editar_operacao_fii'),
    url(r'^historico/$', views.historico_fii, name='historico_fii'),
    url(r'^inserir-operacao-fii/$', views.inserir_operacao_fii, name='inserir_operacao_fii'),
    url(r'^listar-proventos/$', views.listar_proventos, name='listar_proventos_fii'),
    url(r'^listar-tickers-fiis/$', views.listar_tickers_fiis, name='listar_tickers_fii'),
    url(r'^painel/$', views.painel, name='painel_fii'),
    url(r'^sobre/$', views.sobre, name='sobre_fii'),
    ]
