# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
#     url(r'^acompanhamento-mensal/$', views.fii.fii.acompanhamento_mensal_fii, name='acompanhamento_mensal_fii'),
    url(r'^acompanhamento/$', views.fii.fii.acompanhamento_fii, name='acompanhamento_fii'),
    url(r'^calcular-resultado-corretagem/$', views.fii.fii.calcular_resultado_corretagem, name='calcular_resultado_corretagem'),
    url(r'^detalhar-provento/(?P<provento_id>\d+)/$', views.fii.fii.detalhar_provento, name='detalhar_provento_fii'),
    url(r'^editar-operacao/(?P<operacao_id>\d+)/$', views.fii.fii.editar_operacao_fii, name='editar_operacao_fii'),
    url(r'^historico/$', views.fii.fii.historico_fii, name='historico_fii'),
    url(r'^inserir-operacao-fii/$', views.fii.fii.inserir_operacao_fii, name='inserir_operacao_fii'),
    url(r'^listar-proventos/$', views.fii.fii.listar_proventos, name='listar_proventos_fii'),
    url(r'^listar-tickers-fiis/$', views.fii.fii.listar_tickers_fiis, name='listar_tickers_fii'),
    url(r'^painel/$', views.fii.fii.painel, name='painel_fii'),
    url(r'^sobre/$', views.fii.fii.sobre, name='sobre_fii'),
    ]