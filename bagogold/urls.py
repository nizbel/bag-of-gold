# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    # Examples:
    # url(r'^$', 'bagogold.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    
    # Geral
    url(r'^home/$', 'bagogold.views.home.home', name='home'),
    
    # Ações
    url(r'^acoes/$', 'bagogold.views.acoes.home.home', name='home_acoes'),
#     url(r'^$', 'bagogold.views.acoes.buyandhold.listar_acoes', name='listar_acoes'),
    url(r'^acoes/buyandhold/editar_operacao_acao/(?P<id>\d+)/$', 'bagogold.views.acoes.buyandhold.editar_operacao_acao', name='editar_operacao_bh'),
    url(r'^acoes/buyandhold/editar_provento_acao/(?P<id>\d+)/$', 'bagogold.views.acoes.buyandhold.editar_provento_acao', name='editar_provento_bh'),
    url(r'^acoes/buyandhold/estatisticas_acao/(?P<ticker>\w+)/$', 'bagogold.views.acoes.buyandhold.estatisticas_acao', name='estatisticas_acao_bh'),
    url(r'^acoes/buyandhold/historico/$', 'bagogold.views.acoes.buyandhold.historico', name='historico_bh'),
    url(r'^acoes/buyandhold/inserir_operacao_acao/$', 'bagogold.views.acoes.buyandhold.inserir_operacao_acao', name='inserir_operacao_bh'),
    url(r'^acoes/buyandhold/inserir_provento_acao/$', 'bagogold.views.acoes.buyandhold.inserir_provento_acao', name='inserir_provento_bh'),
    url(r'^acoes/buyandhold/inserir_taxa_custodia_acao/$', 'bagogold.views.acoes.buyandhold.inserir_taxa_custodia_acao', name='inserir_taxa_custodia_acao'),
    url(r'^acoes/buyandhold/painel/$', 'bagogold.views.acoes.buyandhold.painel', name='painel_bh'),
    url(r'^acoes/buyandhold/ver_taxas_custodia_acao/$', 'bagogold.views.acoes.buyandhold.ver_taxas_custodia_acao', name='ver_taxas_custodia_acao'),
    
    url(r'^acoes/trading/acompanhamento_mensal/$', 'bagogold.views.acoes.trade.acompanhamento_mensal', name='acompanhamento_mensal'),
    url(r'^acoes/trading/editar_operacao/(?P<id>\d+)/$', 'bagogold.views.acoes.trade.editar_operacao', name='editar_operacao_t'),
    url(r'^acoes/trading/editar_operacao_acao/(?P<id>\d+)/$', 'bagogold.views.acoes.trade.editar_operacao_acao', name='editar_operacao_acao_t'),
    url(r'^acoes/trading/historico_operacoes/$', 'bagogold.views.acoes.trade.historico_operacoes', name='historico_operacoes'),
    url(r'^acoes/trading/historico_operacoes_cv/$', 'bagogold.views.acoes.trade.historico_operacoes_cv', name='historico_operacoes_cv'),
    url(r'^acoes/trading/inserir_operacao/$', 'bagogold.views.acoes.trade.inserir_operacao', name='inserir_operacao_t'),
    url(r'^acoes/trading/inserir_operacao_acao/$', 'bagogold.views.acoes.trade.inserir_operacao_acao', name='inserir_operacao_acao_t'),
    
    # Divisões
    url(r'^divisoes/detalhar_divisao/(?P<id>\d+)/$', 'bagogold.views.divisoes.divisoes.detalhar_divisao', name='detalhar_divisao'),
    url(r'^divisoes/inserir_divisao/$', 'bagogold.views.divisoes.divisoes.inserir_divisao', name='inserir_divisao'),
    url(r'^divisoes/listar_divisoes/$', 'bagogold.views.divisoes.divisoes.listar_divisoes', name='listar_divisoes'),
    
    # FII
    url(r'^fii/acompanhamento_mensal/$', 'bagogold.views.fii.fii.acompanhamento_mensal_fii', name='acompanhamento_mensal_fii'),
    url(r'^fii/aconselhamento/$', 'bagogold.views.fii.fii.aconselhamento_fii', name='aconselhamento_fii'),
    url(r'^fii/editar_operacao/(?P<id>\d+)/$', 'bagogold.views.fii.fii.editar_operacao_fii', name='editar_operacao_fii'),
    url(r'^fii/historico/$', 'bagogold.views.fii.fii.historico_fii', name='historico_fii'),
    url(r'^fii/inserir_operacao_fii/$', 'bagogold.views.fii.fii.inserir_operacao_fii', name='inserir_operacao_fii'),
    url(r'^fii/editar_provento/(?P<id>\d+)/$', 'bagogold.views.fii.fii.editar_provento_fii', name='editar_provento_fii'),
    url(r'^fii/inserir_provento_fii/$', 'bagogold.views.fii.fii.inserir_provento_fii', name='inserir_provento_fii'),
    
    # Tesouro direto
    url(r'^td/editar_operacao/(?P<id>\d+)/$', 'bagogold.views.td.td.editar_operacao_td', name='editar_operacao_td'),
    url(r'^td/historico/$', 'bagogold.views.td.td.historico_td', name='historico_td'),
    url(r'^td/inserir_operacao_td/$', 'bagogold.views.td.td.inserir_operacao_td', name='inserir_operacao_td'),
    
    # Poupança
    
    # LCA e LCI
    url(r'^lc/editar_operacao/(?P<id>\d+)/$', 'bagogold.views.lc.lc.editar_operacao_lc', name='editar_operacao_lc'),
    url(r'^lc/historico/$', 'bagogold.views.lc.lc.historico', name='historico_lc'),
    url(r'^lc/modificar_porcentagem_di_lc/$', 'bagogold.views.lc.lc.modificar_porcentagem_di_lc', name='modificar_porcentagem_di_lc'),
    url(r'^lc/inserir_operacao_lc/$', 'bagogold.views.lc.lc.inserir_operacao_lc', name='inserir_operacao_lc'),
]
