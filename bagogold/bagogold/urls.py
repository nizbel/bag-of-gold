# -*- coding: utf-8 -*-
from bagogold.bagogold.views.investidores.investidores import logout
from django.conf.urls import include, url
from django.contrib.auth.views import login, password_change, \
    password_change_done, password_reset, password_reset_done, \
    password_reset_confirm, password_reset_complete
from django.views.generic.base import RedirectView, TemplateView
from registration import validators
from registration.backends.hmac import views as registration_views
from registration.forms import RegistrationFormUniqueEmail
import views

# Altera valor para constante de email duplicado no Django-registration
validators.DUPLICATE_EMAIL = 'Já existe um usuário cadastrado com esse email'

acoes_patterns = [
        url(r'^$', views.acoes.home.home, name='home_acoes'),
#         url(r'^$', views.acoes.buyandhold.listar_acoes, name='listar_acoes'),
        url(r'^buyandhold/calcular_poupanca_proventos_na_data/$', views.acoes.buyandhold.calcular_poupanca_proventos_na_data, name='calcular_poupanca_proventos_na_data'),
        url(r'^buyandhold/editar_operacao_acao/(?P<id>\d+)/$', views.acoes.buyandhold.editar_operacao_acao, name='editar_operacao_bh'),
        url(r'^buyandhold/editar_provento_acao/(?P<id>\d+)/$', views.acoes.buyandhold.editar_provento_acao, name='editar_provento_bh'),
        url(r'^buyandhold/estatisticas_acao/(?P<ticker>\w+)/$', views.acoes.buyandhold.estatisticas_acao, name='estatisticas_acao_bh'),
        url(r'^buyandhold/historico/$', views.acoes.buyandhold.historico, name='historico_bh'),
        url(r'^buyandhold/inserir_operacao_acao/$', views.acoes.buyandhold.inserir_operacao_acao, name='inserir_operacao_bh'),
        url(r'^buyandhold/inserir_provento_acao/$', views.acoes.buyandhold.inserir_provento_acao, name='inserir_provento_bh'),
        url(r'^buyandhold/inserir_taxa_custodia_acao/$', views.acoes.buyandhold.inserir_taxa_custodia_acao, name='inserir_taxa_custodia_acao'),
        url(r'^buyandhold/painel/$', views.acoes.buyandhold.painel, name='painel_bh'),
        url(r'^buyandhold/ver_taxas_custodia_acao/$', views.acoes.buyandhold.ver_taxas_custodia_acao, name='ver_taxas_custodia_acao'),
    
        url(r'^trading/acompanhamento_mensal/$', views.acoes.trade.acompanhamento_mensal, name='acompanhamento_mensal'),
        url(r'^trading/editar_operacao/(?P<id>\d+)/$', views.acoes.trade.editar_operacao, name='editar_operacao_t'),
        url(r'^trading/editar_operacao_acao/(?P<id>\d+)/$', views.acoes.trade.editar_operacao_acao, name='editar_operacao_acao_t'),
        url(r'^trading/historico_operacoes/$', views.acoes.trade.historico_operacoes, name='historico_operacoes'),
        url(r'^trading/historico_operacoes_cv/$', views.acoes.trade.historico_operacoes_cv, name='historico_operacoes_cv'),
        url(r'^trading/inserir_operacao/$', views.acoes.trade.inserir_operacao, name='inserir_operacao_t'),
        url(r'^trading/inserir_operacao_acao/$', views.acoes.trade.inserir_operacao_acao, name='inserir_operacao_acao_t'),
    ]

urlpatterns = [
    # Geral
    url(r'^$', RedirectView.as_view(url='/inicio/')),
    url(r'^inicio/$', views.home.inicio, name='inicio'),
    url(r'^detalhamento_investimentos/$', views.home.detalhamento_investimentos, name='detalhamento_investimentos'),
    
    # Teste de aparência
    url(r'^teste/ver/(?P<url>[\w/]+)/$', views.misc.ver_nova_aparencia, name='ver_nova_aparencia'),
    url(r'^teste/carregar/(?P<url>[\w/]+)/$', views.misc.carregar_nova_aparencia, name='carregar_nova_aparencia'),
    
    # Investidores
    url(r'^login/$', login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', logout, {'next_page': '/login'}, name='logout'),
    url(r'^minha_conta/alterar_senha/$', password_change, {'template_name': 'registration/alterar_senha.html'}, name='password_change'),
    url(r'^minha_conta/alterar_senha/sucesso/$', password_change_done, {'template_name': 'registration/senha_alterada.html'}, name='password_change_done'),
    url(r'^senha_esquecida/$', password_reset, {'template_name': 'registration/confirmar_redefinir_senha.html', 'email_template_name': 'registration/redefinir_senha_email.html', 'subject_template_name': 'registration/redefinir_senha_email_assunto.txt'}, name='password_reset'),
    url(r'^senha_esquecida/email_enviado/$', password_reset_done, {'template_name': 'registration/redefinir_senha_email_enviado.html'}, name='password_reset_done'),
    url(r'^redefinicao_senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm, {'template_name': 'registration/redefinir_senha.html'}, name='password_reset_confirm'),
    url(r'^redefinicao_senha/completa/$', password_reset_complete, {'template_name': 'registration/senha_redefinida.html'}, name='password_reset_complete'),
    # Django-registration
#     url(r'^cadastro/$', registration_views.RegistrationView.as_view(form_class=RegistrationFormUniqueEmail), name='cadastro'),
    url(r'^ativacao/completa/$', TemplateView.as_view(template_name='registration/activation_complete.html'), name='registration_activation_complete'),
    # The activation key can make use of any character from the
    # URL-safe base64 alphabet, plus the colon as a separator.
    url(r'^ativacao/(?P<activation_key>[-:\w]+)/$', registration_views.ActivationView.as_view(), name='ativar_cadastro'),
    url(r'^cadastro/completo/$', TemplateView.as_view(template_name='registration/registration_complete.html'), name='registration_complete'),
    url(r'^cadastro/fechado/$', TemplateView.as_view(template_name='registration/registration_closed.html'), name='registration_closed'),
    url(r'^minha_conta/(?P<id>\d+)/$', views.investidores.investidores.configuracoes_conta_investidor, name='configuracoes_conta_investidor'),
    url(r'^minha_conta/editar_dados_cadastrais/(?P<id>\d+)/$', views.investidores.investidores.editar_dados_cadastrais, name='editar_dados_cadastrais'),
    
    # Gerador de proventos
    url(r'^gerador_proventos/baixar_documento_provento/(?P<id_documento>\d+)/$', views.gerador_proventos.gerador_proventos.baixar_documento_provento, name='baixar_documento_provento'),
    url(r'^gerador_proventos/detalhar_documento/(?P<id_documento>\d+)/$', views.gerador_proventos.gerador_proventos.detalhar_documento, name='detalhar_documento'),
    url(r'^gerador_proventos/detalhar_pendencias_usuario/(?P<id_usuario>\d+)/$', views.gerador_proventos.investidores.detalhar_pendencias_usuario, name='detalhar_pendencias_usuario'),
    url(r'^gerador_proventos/detalhar_provento_acao/(?P<id_provento>\d+)/$', views.gerador_proventos.gerador_proventos.detalhar_provento_acao, name='detalhar_provento_acao'),
    url(r'^gerador_proventos/detalhar_provento_fii/(?P<id_provento>\d+)/$', views.gerador_proventos.gerador_proventos.detalhar_provento_fii, name='detalhar_provento_fii'),
    url(r'^gerador_proventos/ler_documento_provento/(?P<id_pendencia>\d+)/$', views.gerador_proventos.gerador_proventos.ler_documento_provento, name='ler_documento_provento'),
    url(r'^gerador_proventos/listar_documentos/$', views.gerador_proventos.gerador_proventos.listar_documentos, name='listar_documentos'),
    url(r'^gerador_proventos/manual_gerador/(?P<tipo_documento>[a-z]+)/$', views.gerador_proventos.gerador_proventos.manual_gerador, name='manual_gerador'),
    url(r'^gerador_proventos/listar_pendencias/$', views.gerador_proventos.gerador_proventos.listar_pendencias, name='listar_pendencias'),
    url(r'^gerador_proventos/listar_proventos/$', views.gerador_proventos.gerador_proventos.listar_proventos, name='listar_proventos'),
    url(r'^gerador_proventos/listar_usuarios/$', views.gerador_proventos.investidores.listar_usuarios, name='listar_usuarios'),
    url(r'^gerador_proventos/puxar_responsabilidade_documento_provento/$', views.gerador_proventos.gerador_proventos.puxar_responsabilidade_documento_provento, name='puxar_responsabilidade_documento_provento'),
    url(r'^gerador_proventos/remover_responsabilidade_documento_provento/$', views.gerador_proventos.gerador_proventos.remover_responsabilidade_documento_provento, name='remover_responsabilidade_documento_provento'),
    url(r'^gerador_proventos/validar_documento_provento/(?P<id_pendencia>\d+)/$', views.gerador_proventos.gerador_proventos.validar_documento_provento, name='validar_documento_provento'),
    
    # Ações
    url(r'^acoes/', include(acoes_patterns, namespace='acoes')),
    
#     url(r'^acoes/$', views.acoes.home.home, name='home_acoes'),
# #     url(r'^$', views.acoes.buyandhold.listar_acoes, name='listar_acoes'),
#     url(r'^acoes/buyandhold/calcular_poupanca_proventos_na_data/$', views.acoes.buyandhold.calcular_poupanca_proventos_na_data, name='calcular_poupanca_proventos_na_data'),
#     url(r'^acoes/buyandhold/editar_operacao_acao/(?P<id>\d+)/$', views.acoes.buyandhold.editar_operacao_acao, name='editar_operacao_bh'),
#     url(r'^acoes/buyandhold/editar_provento_acao/(?P<id>\d+)/$', views.acoes.buyandhold.editar_provento_acao, name='editar_provento_bh'),
#     url(r'^acoes/buyandhold/estatisticas_acao/(?P<ticker>\w+)/$', views.acoes.buyandhold.estatisticas_acao, name='estatisticas_acao_bh'),
#     url(r'^acoes/buyandhold/historico/$', views.acoes.buyandhold.historico, name='historico_bh'),
#     url(r'^acoes/buyandhold/inserir_operacao_acao/$', views.acoes.buyandhold.inserir_operacao_acao, name='inserir_operacao_bh'),
#     url(r'^acoes/buyandhold/inserir_provento_acao/$', views.acoes.buyandhold.inserir_provento_acao, name='inserir_provento_bh'),
#     url(r'^acoes/buyandhold/inserir_taxa_custodia_acao/$', views.acoes.buyandhold.inserir_taxa_custodia_acao, name='inserir_taxa_custodia_acao'),
#     url(r'^acoes/buyandhold/painel/$', views.acoes.buyandhold.painel, name='painel_bh'),
#     url(r'^acoes/buyandhold/ver_taxas_custodia_acao/$', views.acoes.buyandhold.ver_taxas_custodia_acao, name='ver_taxas_custodia_acao'),
#     
#     url(r'^acoes/trading/acompanhamento_mensal/$', views.acoes.trade.acompanhamento_mensal, name='acompanhamento_mensal'),
#     url(r'^acoes/trading/editar_operacao/(?P<id>\d+)/$', views.acoes.trade.editar_operacao, name='editar_operacao_t'),
#     url(r'^acoes/trading/editar_operacao_acao/(?P<id>\d+)/$', views.acoes.trade.editar_operacao_acao, name='editar_operacao_acao_t'),
#     url(r'^acoes/trading/historico_operacoes/$', views.acoes.trade.historico_operacoes, name='historico_operacoes'),
#     url(r'^acoes/trading/historico_operacoes_cv/$', views.acoes.trade.historico_operacoes_cv, name='historico_operacoes_cv'),
#     url(r'^acoes/trading/inserir_operacao/$', views.acoes.trade.inserir_operacao, name='inserir_operacao_t'),
#     url(r'^acoes/trading/inserir_operacao_acao/$', views.acoes.trade.inserir_operacao_acao, name='inserir_operacao_acao_t'),
    
    # Divisões
    url(r'^divisoes/criar_transferencias/$', views.divisoes.divisoes.criar_transferencias, name='criar_transferencias'),
    url(r'^divisoes/detalhar_divisao/(?P<id>\d+)/$', views.divisoes.divisoes.detalhar_divisao, name='detalhar_divisao'),
    url(r'^divisoes/editar_divisao/(?P<id>\d+)/$', views.divisoes.divisoes.editar_divisao, name='editar_divisao'),
    url(r'^divisoes/editar_transferencia/(?P<id>\d+)/$', views.divisoes.divisoes.editar_transferencia, name='editar_transferencia'),
    url(r'^divisoes/inserir_divisao/$', views.divisoes.divisoes.inserir_divisao, name='inserir_divisao'),
    url(r'^divisoes/inserir_transferencia/$', views.divisoes.divisoes.inserir_transferencia, name='inserir_transferencia'),
    url(r'^divisoes/listar_divisoes/$', views.divisoes.divisoes.listar_divisoes, name='listar_divisoes'),
    url(r'^divisoes/listar_transferencias/$', views.divisoes.divisoes.listar_transferencias, name='listar_transferencias'),
    
    # FII
    url(r'^fii/acompanhamento_mensal/$', views.fii.fii.acompanhamento_mensal_fii, name='acompanhamento_mensal_fii'),
    url(r'^fii/aconselhamento/$', views.fii.fii.aconselhamento_fii, name='aconselhamento_fii'),
    url(r'^fii/calcular_resultado_corretagem/$', views.fii.fii.calcular_resultado_corretagem, name='calcular_resultado_corretagem'),
    url(r'^fii/editar_operacao/(?P<id>\d+)/$', views.fii.fii.editar_operacao_fii, name='editar_operacao_fii'),
    url(r'^fii/historico/$', views.fii.fii.historico_fii, name='historico_fii'),
    url(r'^fii/inserir_operacao_fii/$', views.fii.fii.inserir_operacao_fii, name='inserir_operacao_fii'),
    url(r'^fii/editar_provento/(?P<id>\d+)/$', views.fii.fii.editar_provento_fii, name='editar_provento_fii'),
    url(r'^fii/inserir_provento_fii/$', views.fii.fii.inserir_provento_fii, name='inserir_provento_fii'),
    url(r'^fii/painel/$', views.fii.fii.painel, name='painel_fii'),

    # Tesouro direto
    url(r'^td/aconselhamento/$', views.td.td.aconselhamento_td, name='aconselhamento_td'),
    url(r'^td/buscar_titulos_validos_na_data/$', views.td.td.buscar_titulos_validos_na_data, name='buscar_titulos_validos_na_data'),
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
    url(r'^lc/sobre/$', views.lc.lc.sobre, name='sobre_lc'),
    
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
    
    # Debêntures
    url(r'^debentures/detalhar_debenture/(?P<debenture_id>\d+)/$', views.debentures.debentures.detalhar_debenture, name='detalhar_debenture'),
    url(r'^debentures/editar_operacao/(?P<operacao_id>\d+)/$', views.debentures.debentures.editar_operacao_debenture, name='editar_operacao_debenture'),
    url(r'^debentures/historico/$', views.debentures.debentures.historico, name='historico_debenture'),
    url(r'^debentures/inserir_operacao_debenture/$', views.debentures.debentures.inserir_operacao_debenture, name='inserir_operacao_debenture'),
    url(r'^debentures/listar_debentures/$', views.debentures.debentures.listar_debentures, name='listar_debentures'),
    url(r'^debentures/listar_debentures_validas_na_data/$', views.debentures.debentures.listar_debentures_validas_na_data, name='listar_debentures_validas_na_data'),
    url(r'^debentures/painel/$', views.debentures.debentures.painel, name='painel_debenture'),
    
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
