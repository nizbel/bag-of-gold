# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.views.generic.base import RedirectView
import bagogold.acoes.views as views


acoes_geral_patterns = [
    url(r'^detalhar-acao/(?P<ticker>\w+)/$', views.geral.estatisticas_acao, name='detalhar_acao'),
    url(r'^detalhar-provento/(?P<provento_id>\d+)/$', views.geral.detalhar_provento, name='detalhar_provento_acao'),
    url(r'^estatisticas-acao/(?P<ticker>\w+)/$', views.geral.estatisticas_acao, name='estatisticas_acao_bh'),
    # Redirecionamento
    url(r'^estatisticas_acao/(?P<ticker>\w+)/$', RedirectView.as_view(pattern_name='acoes:geral:estatisticas_acao_bh', permanent=True)),
    # Redirecionamento
    url(r'^buyandhold/estatisticas_acao/(?P<ticker>\w+)/$', RedirectView.as_view(pattern_name='acoes:geral:estatisticas_acao_bh', permanent=True)),
    url(r'^listar-acoes/$', views.geral.listar_acoes, name='listar_acoes'),
    # Redirecionamento
    url(r'^listar_acoes/$',  RedirectView.as_view(pattern_name='acoes:geral:listar_acoes', permanent=True)),
    url(r'^listar-tickers-acoes/$', views.geral.listar_tickers_acoes, name='listar_tickers_acoes'),
    url(r'^listar-proventos/$', views.geral.listar_proventos, name='listar_proventos_acao'),
    # Redirecionamento
    url(r'^listar_proventos/$',  RedirectView.as_view(pattern_name='acoes:geral:listar_proventos_acao', permanent=True)),
    url(r'^sobre/$', views.geral.sobre, name='sobre_acoes'),
    ]

acoes_bh_patterns = [
    url(r'^calcular-poupanca-proventos-na-data/$', views.buyandhold.calcular_poupanca_proventos_na_data, name='calcular_poupanca_proventos_na_data'),
    url(r'^editar-operacao-acao/(?P<id_operacao>\d+)/$', views.buyandhold.editar_operacao_acao, name='editar_operacao_bh'),
    url(r'^evolucao-posicao/$', views.buyandhold.evolucao_posicao, name='evolucao_posicao_bh'),
    url(r'^historico/$', views.buyandhold.historico, name='historico_bh'),
    url(r'^inserir-operacao-acao/$', views.buyandhold.inserir_operacao_acao, name='inserir_operacao_bh'),
    url(r'^inserir-taxa-custodia-acao/$', views.buyandhold.inserir_taxa_custodia_acao, name='inserir_taxa_custodia_acao'),
    url(r'^listar-taxas-custodia-acao/$', views.buyandhold.listar_taxas_custodia_acao, name='listar_taxas_custodia_acao'),
    url(r'^painel/$', views.buyandhold.painel, name='painel_bh'),
    url(r'^remover-taxa-custodia-acao/(?P<taxa_id>\d+)/$', views.buyandhold.remover_taxa_custodia_acao, name='remover_taxa_custodia_acao'),
    ]

acoes_trading_patterns = [
    url(r'^acompanhamento-mensal/$', views.trade.acompanhamento_mensal, name='acompanhamento_mensal'),
    # Redirecionamento
    url(r'^acompanhamento_mensal/$',  RedirectView.as_view(pattern_name='acoes:trading:acompanhamento_mensal', permanent=True)),
    url(r'^editar-operacao/(?P<id_operacao>\d+)/$', views.trade.editar_operacao, name='editar_operacao_t'),
    url(r'^editar-operacao-acao/(?P<id_operacao>\d+)/$', views.trade.editar_operacao_acao, name='editar_operacao_acao_t'),
    url(r'^historico-operacoes/$', views.trade.historico_operacoes, name='historico_operacoes'),
    # Redirecionamento
    url(r'^historico_operacoes/$',  RedirectView.as_view(pattern_name='acoes:trading:historico_operacoes', permanent=True)),
    url(r'^historico-operacoes-cv/$', views.trade.historico_operacoes_cv, name='historico_operacoes_cv'),
    # Redirecionamento
    url(r'^historico_operacoes_cv/$',  RedirectView.as_view(pattern_name='acoes:trading:historico_operacoes_cv', permanent=True)),
    url(r'^inserir-operacao/$', views.trade.inserir_operacao, name='inserir_operacao_t'),
    url(r'^inserir-operacao-acao/$', views.trade.inserir_operacao_acao, name='inserir_operacao_acao_t'),
    ]

acoes_patterns = [
    url(r'^', include(acoes_geral_patterns, namespace='geral')),
    url(r'^buy-and-hold/', include(acoes_bh_patterns, namespace='bh')),
    url(r'^trading/', include(acoes_trading_patterns, namespace='trading')),
    ]
