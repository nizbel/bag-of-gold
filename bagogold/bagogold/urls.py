# -*- coding: utf-8 -*-
from bagogold.bagogold.views.investidores.investidores import logout
from django.conf.urls import url
from django.contrib.auth.views import login, password_change, \
    password_change_done, password_reset, password_reset_done, \
    password_reset_confirm, password_reset_complete
from django.views.generic.base import RedirectView
import views



urlpatterns = [
    # Geral
    url(r'^$', RedirectView.as_view(url='/home/')),
    url(r'^home/$', views.home.home, name='home'),
    
    # Investidores
    url(r'^cadastrar/$',  views.investidores.investidores.cadastrar, name='cadastrar'),
    url(r'^login/$', login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', logout, {'next_page': '/login'}, name='logout'),
    url(r'^password_change/$', password_change, name='password_change'),
    url(r'^password_change/done/$', password_change_done, name='password_change_done'),
    url(r'^password_reset/$', password_reset, name='password_reset'),
    url(r'^password_reset/done/$', password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', password_reset_complete, name='password_reset_complete'),
    
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
    url(r'^cdb_rdb/detalhar_cdb_rdb/(?P<id>\d+)/$', views.cdb_rdb.cdb_rdb.detalhar_cdb_rdb, name='detalhar_cdb_rdb'),
    url(r'^cdb_rdb/editar_cdb_rdb/(?P<id>\d+)/$', views.cdb_rdb.cdb_rdb.editar_cdb_rdb, name='editar_cdb_rdb'),
    url(r'^cdb_rdb/editar_historico_carencia/(?P<id>\d+)/$', views.cdb_rdb.cdb_rdb.editar_historico_carencia, name='editar_historico_carencia'),
    url(r'^cdb_rdb/editar_historico_porcentagem/(?P<id>\d+)/$', views.cdb_rdb.cdb_rdb.editar_historico_porcentagem, name='editar_historico_porcentagem'),
    url(r'^cdb_rdb/editar_operacao/(?P<id>\d+)/$', views.cdb_rdb.cdb_rdb.editar_operacao_cdb_rdb, name='editar_operacao_cdb_rdb'),
    url(r'^cdb_rdb/historico/$', views.cdb_rdb.cdb_rdb.historico, name='historico_cdb_rdb'),
    url(r'^cdb_rdb/inserir_cdb_rdb/$', views.cdb_rdb.cdb_rdb.inserir_cdb_rdb, name='inserir_cdb_rdb'),
    url(r'^cdb_rdb/inserir_operacao_cdb_rdb/$', views.cdb_rdb.cdb_rdb.inserir_operacao_cdb_rdb, name='inserir_operacao_cdb_rdb'),
    url(r'^cdb_rdb/listar_cdb_rdb/$', views.cdb_rdb.cdb_rdb.listar_cdb_rdb, name='listar_cdb_rdb'),
    url(r'^cdb_rdb/modificar_carencia_cdb_rdb/(?P<id>\d+)/$', views.cdb_rdb.cdb_rdb.modificar_carencia_cdb_rdb, name='modificar_carencia_cdb_rdb'),
    url(r'^cdb_rdb/modificar_porcentagem_cdb_rdb/(?P<id>\d+)/$', views.cdb_rdb.cdb_rdb.modificar_porcentagem_cdb_rdb, name='modificar_porcentagem_cdb_rdb'),
    url(r'^cdb_rdb/painel/$', views.cdb_rdb.cdb_rdb.painel, name='painel_cdb_rdb'),
    
    # Fundo de investimento
    url(r'^fundo_investimento/adicionar_valor_cota_historico/$', views.fundo_investimento.fundo_investimento.adicionar_valor_cota_historico, name='adicionar_valor_cota_historico'),
    url(r'^fundo_investimento/editar_operacao/(?P<id>\d+)/$', views.fundo_investimento.fundo_investimento.editar_operacao_fundo_investimento, name='editar_operacao_fundo_investimento'),
    url(r'^fundo_investimento/historico/$', views.fundo_investimento.fundo_investimento.historico, name='historico_fundo_investimento'),
    url(r'^fundo_investimento/inserir_fundo_investimento/$', views.fundo_investimento.fundo_investimento.inserir_fundo_investimento, name='inserir_fundo_investimento'),
    url(r'^fundo_investimento/inserir_operacao_fundo_investimento/$', views.fundo_investimento.fundo_investimento.inserir_operacao_fundo_investimento, name='inserir_operacao_fundo_investimento'),
    url(r'^fundo_investimento/listar_fundo_investimento/$', views.fundo_investimento.fundo_investimento.listar_fundo_investimento, name='listar_fundo_investimento'),
    url(r'^fundo_investimento/modificar_carencia_fundo_investimento/$', views.fundo_investimento.fundo_investimento.modificar_carencia_fundo_investimento, name='modificar_carencia_fundo_investimento'),
    url(r'^fundo_investimento/painel/$', views.fundo_investimento.fundo_investimento.painel, name='painel_fundo_investimento'),

    # Imposto de renda
    url(r'^imposto_renda/detalhar_imposto_renda/(?P<ano>\d+)/$', views.imposto_renda.imposto_renda.detalhar_imposto_renda, name='detalhar_imposto_renda'),
    url(r'^imposto_renda/listar_anos/$', views.imposto_renda.imposto_renda.listar_anos, name='listar_anos_imposto_renda'),

]
