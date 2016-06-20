# -*- coding: utf-8 -*-
from django.conf.urls import url

import views

urlpatterns = [
    # Geral
    url(r'^home/$', views.home.home, name='home'),
    
    # Ações
    url(r'^acoes/$', views.acoes.home.home, name='home_acoes'),
#     url(r'^$', views.acoes.buyandhold.listar_acoes, name='listar_acoes'),
    url(r'^acoes/buyandhold/calcular_poupanca_proventos_na_data/$', views.acoes.buyandhold.calcular_poupanca_proventos_na_data, name='calcular_poupanca_proventos_na_data'),
    url(r'^acoes/buyandhold/editar_operacao_acao/(?P<id>\d+)/$', views.acoes.buyandhold.editar_operacao_acao, name='editar_operacao_bh'),
    url(r'^acoes/buyandhold/editar_provento_acao/(?P<id>\d+)/$', views.acoes.buyandhold.editar_provento_acao, name='editar_provento_bh'),
    url(r'^acoes/buyandhold/estatisticas_acao/(?P<ticker>\w+)/$', views.acoes.buyandhold.estatisticas_acao, name='estatisticas_acao_bh'),
    url(r'^acoes/buyandhold/historico/$', views.acoes.buyandhold.historico, name='historico_bh'),
    url(r'^acoes/buyandhold/inserir_operacao_acao/$', views.acoes.buyandhold.inserir_operacao_acao, name='inserir_operacao_bh'),
    url(r'^acoes/buyandhold/inserir_provento_acao/$', views.acoes.buyandhold.inserir_provento_acao, name='inserir_provento_bh'),
    url(r'^acoes/buyandhold/inserir_taxa_custodia_acao/$', views.acoes.buyandhold.inserir_taxa_custodia_acao, name='inserir_taxa_custodia_acao'),
    url(r'^acoes/buyandhold/painel/$', views.acoes.buyandhold.painel, name='painel_bh'),
    url(r'^acoes/buyandhold/ver_taxas_custodia_acao/$', views.acoes.buyandhold.ver_taxas_custodia_acao, name='ver_taxas_custodia_acao'),
    
    url(r'^acoes/trading/acompanhamento_mensal/$', views.acoes.trade.acompanhamento_mensal, name='acompanhamento_mensal'),
    url(r'^acoes/trading/editar_operacao/(?P<id>\d+)/$', views.acoes.trade.editar_operacao, name='editar_operacao_t'),
    url(r'^acoes/trading/editar_operacao_acao/(?P<id>\d+)/$', views.acoes.trade.editar_operacao_acao, name='editar_operacao_acao_t'),
    url(r'^acoes/trading/historico_operacoes/$', views.acoes.trade.historico_operacoes, name='historico_operacoes'),
    url(r'^acoes/trading/historico_operacoes_cv/$', views.acoes.trade.historico_operacoes_cv, name='historico_operacoes_cv'),
    url(r'^acoes/trading/inserir_operacao/$', views.acoes.trade.inserir_operacao, name='inserir_operacao_t'),
    url(r'^acoes/trading/inserir_operacao_acao/$', views.acoes.trade.inserir_operacao_acao, name='inserir_operacao_acao_t'),
    
    # Divisões
    url(r'^divisoes/detalhar_divisao/(?P<id>\d+)/$', views.divisoes.divisoes.detalhar_divisao, name='detalhar_divisao'),
    url(r'^divisoes/editar_transferencia/(?P<id>\d+)/$', views.divisoes.divisoes.editar_transferencia, name='editar_transferencia'),
    url(r'^divisoes/inserir_divisao/$', views.divisoes.divisoes.inserir_divisao, name='inserir_divisao'),
    url(r'^divisoes/inserir_transferencia/$', views.divisoes.divisoes.inserir_transferencia, name='inserir_transferencia'),
    url(r'^divisoes/listar_divisoes/$', views.divisoes.divisoes.listar_divisoes, name='listar_divisoes'),
    url(r'^divisoes/listar_transferencias/$', views.divisoes.divisoes.listar_transferencias, name='listar_transferencias'),
    
    # FII
    url(r'^fii/acompanhamento_mensal/$', views.fii.fii.acompanhamento_mensal_fii, name='acompanhamento_mensal_fii'),
    url(r'^fii/aconselhamento/$', views.fii.fii.aconselhamento_fii, name='aconselhamento_fii'),
    url(r'^fii/editar_operacao/(?P<id>\d+)/$', views.fii.fii.editar_operacao_fii, name='editar_operacao_fii'),
    url(r'^fii/historico/$', views.fii.fii.historico_fii, name='historico_fii'),
    url(r'^fii/inserir_operacao_fii/$', views.fii.fii.inserir_operacao_fii, name='inserir_operacao_fii'),
    url(r'^fii/editar_provento/(?P<id>\d+)/$', views.fii.fii.editar_provento_fii, name='editar_provento_fii'),
    url(r'^fii/inserir_provento_fii/$', views.fii.fii.inserir_provento_fii, name='inserir_provento_fii'),
    url(r'^fii/painel/$', views.fii.fii.painel, name='painel_fii'),

    # Tesouro direto
    url(r'^td/aconselhamento/$', views.td.td.aconselhamento_td, name='aconselhamento_td'),
    url(r'^td/editar_operacao/(?P<id>\d+)/$', views.td.td.editar_operacao_td, name='editar_operacao_td'),
    url(r'^td/historico/$', views.td.td.historico_td, name='historico_td'),
    url(r'^td/inserir_operacao_td/$', views.td.td.inserir_operacao_td, name='inserir_operacao_td'),
    url(r'^td/painel/$', views.td.td.painel, name='painel_td'),

    # Poupança
    
    # LCA e LCI
    url(r'^lc/editar_operacao/(?P<id>\d+)/$', views.lc.lc.editar_operacao_lc, name='editar_operacao_lc'),
    url(r'^lc/historico/$', views.lc.lc.historico, name='historico_lc'),
    url(r'^lc/inserir_letra_credito/$', views.lc.lc.inserir_lc, name='inserir_lc'),
    url(r'^lc/inserir_operacao_lc/$', views.lc.lc.inserir_operacao_lc, name='inserir_operacao_lc'),
    url(r'^lc/listar_letras_credito/$', views.lc.lc.listar_lc, name='listar_lc'),
    url(r'^lc/modificar_carencia_lc/$', views.lc.lc.modificar_carencia_lc, name='modificar_carencia_lc'),
    url(r'^lc/modificar_porcentagem_di_lc/$', views.lc.lc.modificar_porcentagem_di_lc, name='modificar_porcentagem_di_lc'),
    url(r'^lc/painel/$', views.lc.lc.painel, name='painel_lc'),
    
    # CDB e RDB
    url(r'^cdb_rdb/editar_operacao/(?P<id>\d+)/$', views.cdb_rdb.cdb_rdb.editar_operacao_cdb_rdb, name='editar_operacao_cdb_rdb'),
    url(r'^cdb_rdb/historico/$', views.cdb_rdb.cdb_rdb.historico, name='historico_cdb_rdb'),
    url(r'^cdb_rdb/inserir_letra_credito/$', views.cdb_rdb.cdb_rdb.inserir_cdb_rdb, name='inserir_cdb_rdb'),
    url(r'^cdb_rdb/inserir_operacao_cdb_rdb/$', views.cdb_rdb.cdb_rdb.inserir_operacao_cdb_rdb, name='inserir_operacao_cdb_rdb'),
    url(r'^cdb_rdb/listar_cdb_rdb/$', views.cdb_rdb.cdb_rdb.listar_cdb_rdb, name='listar_cdb_rdb'),
    url(r'^cdb_rdb/modificar_carencia_cdb_rdb/$', views.cdb_rdb.cdb_rdb.modificar_carencia_cdb_rdb, name='modificar_carencia_cdb_rdb'),
    url(r'^cdb_rdb/modificar_porcentagem_cdb_rdb/$', views.cdb_rdb.cdb_rdb.modificar_porcentagem_di_cdb_rdb, name='modificar_porcentagem_cdb_rdb'),
    url(r'^cdb_rdb/painel/$', views.cdb_rdb.cdb_rdb.painel, name='painel_cdb_rdb'),
]
