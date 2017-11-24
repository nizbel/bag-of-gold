# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.investidor import ExtendedAuthForm, \
    ExtendedUserCreationForm, ExtendedPasswordChangeForm,\
    ExtendedSetPasswordForm
from bagogold.bagogold.views.investidores.investidores import logout
from django.conf.urls import include, url
from django.contrib.auth.views import PasswordChangeView, \
    PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, \
    PasswordResetCompleteView, PasswordResetCompleteView, LoginView,\
    PasswordResetConfirmView
from django.views.generic.base import RedirectView, TemplateView
from registration import validators
from registration.backends.hmac import views as registration_views
import views

# Altera valor para constante de email duplicado no Django-registration
validators.DUPLICATE_EMAIL = 'Já existe um usuário cadastrado com esse email'

inicio_patterns = [
    url(r'^$', RedirectView.as_view(url='/painel_geral/')),
    url(r'^calendario/$', views.home.calendario, name='calendario'),
    url(r'^detalhar_acumulados_mensais/$', views.home.detalhar_acumulados_mensais, name='detalhar_acumulados_mensais'),
    url(r'^detalhar_acumulado_mensal/$', views.home.detalhar_acumulado_mensal, name='detalhar_acumulado_mensal'),
    url(r'^detalhamento_investimentos/$', views.home.detalhamento_investimentos, name='detalhamento_investimentos'),
    url(r'^renda_fixa/$', views.home.grafico_renda_fixa_painel_geral, name='grafico_renda_fixa_painel_geral'),
    url(r'^painel_geral/$', views.home.painel_geral, name='painel_geral'),
    url(r'^sobre/$', views.home.sobre, name='sobre'),
    ]

acoes_geral_patterns = [
    url(r'^detalhar_provento/(?P<provento_id>\d+)/$', views.acoes.acoes.detalhar_provento, name='detalhar_provento'),
    url(r'^estatisticas_acao/(?P<ticker>\w+)/$', views.acoes.acoes.estatisticas_acao, name='estatisticas_acao_bh'),
    url(r'^listar_acoes/$', views.acoes.acoes.listar_acoes, name='listar_acoes'),
    url(r'^listar_proventos/$', views.acoes.acoes.listar_proventos, name='listar_proventos'),
    url(r'^sobre/$', views.acoes.acoes.sobre, name='sobre_acoes'),
    ]

acoes_bh_patterns = [
    url(r'^calcular_poupanca_proventos_na_data/$', views.acoes.buyandhold.calcular_poupanca_proventos_na_data, name='calcular_poupanca_proventos_na_data'),
    url(r'^editar_operacao_acao/(?P<operacao_id>\d+)/$', views.acoes.buyandhold.editar_operacao_acao, name='editar_operacao_bh'),
    url(r'^evolucao_posicao/$', views.acoes.buyandhold.evolucao_posicao, name='evolucao_posicao_bh'),
    url(r'^historico/$', views.acoes.buyandhold.historico, name='historico_bh'),
    url(r'^inserir_operacao_acao/$', views.acoes.buyandhold.inserir_operacao_acao, name='inserir_operacao_bh'),
    url(r'^inserir_taxa_custodia_acao/$', views.acoes.buyandhold.inserir_taxa_custodia_acao, name='inserir_taxa_custodia_acao'),
    url(r'^listar_taxas_custodia_acao/$', views.acoes.buyandhold.listar_taxas_custodia_acao, name='listar_taxas_custodia_acao'),
    url(r'^painel/$', views.acoes.buyandhold.painel, name='painel_bh'),
    url(r'^remover_taxa_custodia_acao/(?P<taxa_id>\d+)/$', views.acoes.buyandhold.remover_taxa_custodia_acao, name='remover_taxa_custodia_acao'),
    ]

acoes_trading_patterns = [
    url(r'^acompanhamento_mensal/$', views.acoes.trade.acompanhamento_mensal, name='acompanhamento_mensal'),
    url(r'^editar_operacao/(?P<operacao_id>\d+)/$', views.acoes.trade.editar_operacao, name='editar_operacao_t'),
    url(r'^editar_operacao_acao/(?P<operacao_id>\d+)/$', views.acoes.trade.editar_operacao_acao, name='editar_operacao_acao_t'),
    url(r'^historico_operacoes/$', views.acoes.trade.historico_operacoes, name='historico_operacoes'),
    url(r'^historico_operacoes_cv/$', views.acoes.trade.historico_operacoes_cv, name='historico_operacoes_cv'),
    url(r'^inserir_operacao/$', views.acoes.trade.inserir_operacao, name='inserir_operacao_t'),
    url(r'^inserir_operacao_acao/$', views.acoes.trade.inserir_operacao_acao, name='inserir_operacao_acao_t'),
    ]

acoes_patterns = [
    url(r'^', include(acoes_geral_patterns, namespace='geral')),
    url(r'^buyandhold/', include(acoes_bh_patterns, namespace='bh')),
    url(r'^trading/', include(acoes_trading_patterns, namespace='trading')),
    ]

debentures_patterns = [
    url(r'^detalhar_debenture/(?P<debenture_id>\d+)/$', views.debentures.debentures.detalhar_debenture, name='detalhar_debenture'),
    url(r'^editar_operacao/(?P<operacao_id>\d+)/$', views.debentures.debentures.editar_operacao_debenture, name='editar_operacao_debenture'),
    url(r'^historico/$', views.debentures.debentures.historico, name='historico_debenture'),
    url(r'^inserir_operacao_debenture/$', views.debentures.debentures.inserir_operacao_debenture, name='inserir_operacao_debenture'),
    url(r'^listar_debentures/$', views.debentures.debentures.listar_debentures, name='listar_debentures'),
    url(r'^listar_debentures_validas_na_data/$', views.debentures.debentures.listar_debentures_validas_na_data, name='listar_debentures_validas_na_data'),
    url(r'^painel/$', views.debentures.debentures.painel, name='painel_debenture'),
    url(r'^sobre/$', views.debentures.debentures.sobre, name='sobre_debenture'),
    ]

divisoes_patterns = [
    url(r'^criar_transferencias/$', views.divisoes.divisoes.criar_transferencias, name='criar_transferencias'),
    url(r'^detalhar_divisao/(?P<divisao_id>\d+)/$', views.divisoes.divisoes.detalhar_divisao, name='detalhar_divisao'),
    url(r'^editar_divisao/(?P<divisao_id>\d+)/$', views.divisoes.divisoes.editar_divisao, name='editar_divisao'),
    url(r'^editar_transferencia/(?P<divisao_id>\d+)/$', views.divisoes.divisoes.editar_transferencia, name='editar_transferencia'),
    url(r'^inserir_divisao/$', views.divisoes.divisoes.inserir_divisao, name='inserir_divisao'),
    url(r'^inserir_transferencia/$', views.divisoes.divisoes.inserir_transferencia, name='inserir_transferencia'),
    url(r'^linha_do_tempo/(?P<divisao_id>\d+)/$', views.divisoes.linha_do_tempo.linha_do_tempo, name='linha_do_tempo'),
    url(r'^listar_divisoes/$', views.divisoes.divisoes.listar_divisoes, name='listar_divisoes'),
    url(r'^listar_transferencias/$', views.divisoes.divisoes.listar_transferencias, name='listar_transferencias'),
    ]

fiis_patterns = [
#     url(r'^acompanhamento_mensal/$', views.fii.fii.acompanhamento_mensal_fii, name='acompanhamento_mensal_fii'),
    url(r'^acompanhamento/$', views.fii.fii.acompanhamento_fii, name='acompanhamento_fii'),
    url(r'^calcular_resultado_corretagem/$', views.fii.fii.calcular_resultado_corretagem, name='calcular_resultado_corretagem'),
    url(r'^detalhar_provento/(?P<provento_id>\d+)/$', views.fii.fii.detalhar_provento, name='detalhar_provento_fii'),
    url(r'^editar_operacao/(?P<operacao_id>\d+)/$', views.fii.fii.editar_operacao_fii, name='editar_operacao_fii'),
    url(r'^historico/$', views.fii.fii.historico_fii, name='historico_fii'),
    url(r'^inserir_operacao_fii/$', views.fii.fii.inserir_operacao_fii, name='inserir_operacao_fii'),
    url(r'^listar_proventos/$', views.fii.fii.listar_proventos, name='listar_proventos_fii'),
    url(r'^painel/$', views.fii.fii.painel, name='painel_fii'),
    url(r'^sobre/$', views.fii.fii.sobre, name='sobre_fii'),
    ]

gerador_proventos_patterns = [
    url(r'^baixar_documento_provento/(?P<id_documento>\d+)/$', views.gerador_proventos.gerador_proventos.baixar_documento_provento, name='baixar_documento_provento'),
    url(r'^detalhar_documento/(?P<id_documento>\d+)/$', views.gerador_proventos.gerador_proventos.detalhar_documento, name='detalhar_documento'),
    url(r'^detalhar_pendencias_usuario/(?P<id_usuario>\d+)/$', views.gerador_proventos.investidores.detalhar_pendencias_usuario, name='detalhar_pendencias_usuario'),
    url(r'^detalhar_provento_acao/(?P<id_provento>\d+)/$', views.gerador_proventos.gerador_proventos.detalhar_provento_acao, name='detalhar_provento_acao'),
    url(r'^detalhar_provento_fii/(?P<id_provento>\d+)/$', views.gerador_proventos.gerador_proventos.detalhar_provento_fii, name='detalhar_provento_fii'),
    url(r'^ler_documento_provento/(?P<id_pendencia>\d+)/$', views.gerador_proventos.gerador_proventos.ler_documento_provento, name='ler_documento_provento'),
    url(r'^listar_documentos/$', views.gerador_proventos.gerador_proventos.listar_documentos, name='listar_documentos'),
    url(r'^manual_gerador/(?P<tipo_documento>[a-z]+)/$', views.gerador_proventos.gerador_proventos.manual_gerador, name='manual_gerador'),
    url(r'^listar_pendencias/$', views.gerador_proventos.gerador_proventos.listar_pendencias, name='listar_pendencias'),
    url(r'^listar_proventos/$', views.gerador_proventos.gerador_proventos.listar_proventos, name='listar_proventos'),
    url(r'^listar_usuarios/$', views.gerador_proventos.investidores.listar_usuarios, name='listar_usuarios'),
    url(r'^puxar_responsabilidade_documento_provento/$', views.gerador_proventos.gerador_proventos.puxar_responsabilidade_documento_provento, name='puxar_responsabilidade_documento_provento'),
    url(r'^relacionar_proventos_fii/(?P<id_provento_a_relacionar>\d+)/(?P<id_provento_relacionado>\d+)/$', views.gerador_proventos.gerador_proventos.relacionar_proventos_fii_add_pelo_sistema, 
        name='relacionar_proventos_fii'),
    url(r'^remover_responsabilidade_documento_provento/$', views.gerador_proventos.gerador_proventos.remover_responsabilidade_documento_provento, name='remover_responsabilidade_documento_provento'),
    url(r'^validar_documento_provento/(?P<id_pendencia>\d+)/$', views.gerador_proventos.gerador_proventos.validar_documento_provento, name='validar_documento_provento'),
    ]

imposto_renda_patterns = [
    url(r'^detalhar_imposto_renda/(?P<ano>\d+)/$', views.imposto_renda.imposto_renda.detalhar_imposto_renda, name='detalhar_imposto_renda'),
    url(r'^listar_anos/$', views.imposto_renda.imposto_renda.listar_anos, name='listar_anos_imposto_renda'),
    ]

lci_lca_patterns = [
    url(r'^detalhar_lci_lca/(?P<lci_lca_id>\d+)/$', views.lc.lc.detalhar_lci_lca, name='detalhar_lci_lca'),
    url(r'^editar_historico_carencia/(?P<historico_carencia_id>\d+)/$', views.lc.lc.editar_historico_carencia, name='editar_historico_carencia_lci_lca'),
    url(r'^editar_historico_porcentagem/(?P<historico_porcentagem_id>\d+)/$', views.lc.lc.editar_historico_porcentagem, name='editar_historico_porcentagem_lci_lca'),
    url(r'^editar_lci_lca/(?P<lci_lca_id>\d+)/$', views.lc.lc.editar_lci_lca, name='editar_lci_lca'),
    url(r'^editar_operacao/(?P<id>\d+)/$', views.lc.lc.editar_operacao_lc, name='editar_operacao_lci_lca'),
    url(r'^historico/$', views.lc.lc.historico, name='historico_lci_lca'),
    url(r'^inserir_letra_credito/$', views.lc.lc.inserir_lc, name='inserir_lci_lca'),
    url(r'^inserir_operacao_lc/$', views.lc.lc.inserir_operacao_lc, name='inserir_operacao_lci_lca'),
    url(r'^listar_letras_credito/$', views.lc.lc.listar_lc, name='listar_lci_lca'),
    url(r'^listar_operacoes_passada_carencia/$', views.lc.lc.listar_operacoes_passada_carencia, name='listar_operacoes_passada_carencia'),
    url(r'^inserir_historico_carencia_lci_lca/(?P<lci_lca_id>\d+)/$', views.lc.lc.inserir_historico_carencia, name='inserir_historico_carencia_lci_lca'),
    url(r'^inserir_historico_porcentagem_lci_lca/(?P<lci_lca_id>\d+)/$', views.lc.lc.inserir_historico_porcentagem, name='inserir_historico_porcentagem_lci_lca'),
    url(r'^painel/$', views.lc.lc.painel, name='painel_lci_lca'),
    url(r'^sobre/$', views.lc.lc.sobre, name='sobre_lci_lca'),
    ]

td_patterns = [
    url(r'^acompanhamento/$', views.td.td.acompanhamento_td, name='acompanhamento_td'),
    url(r'^buscar_titulos_validos_na_data/$', views.td.td.buscar_titulos_validos_na_data, name='buscar_titulos_validos_na_data'),
    url(r'^detalhar_titulo/(?P<titulo_id>\d+)/$', views.td.td.detalhar_titulo_td, name='detalhar_titulo_td'),
    url(r'^editar_operacao/(?P<operacao_id>\d+)/$', views.td.td.editar_operacao_td, name='editar_operacao_td'),
    url(r'^historico/$', views.td.td.historico_td, name='historico_td'),
    url(r'^inserir_operacao_td/$', views.td.td.inserir_operacao_td, name='inserir_operacao_td'),
    url(r'^listar_historico_titulo/(?P<titulo_id>\d+)/$', views.td.td.listar_historico_titulo, name='listar_historico_titulo'),
    url(r'^listar_titulos_td/$', views.td.td.listar_titulos_td, name='listar_titulos_td'),
    url(r'^painel/$', views.td.td.painel, name='painel_td'),
    url(r'^sobre/$', views.td.td.sobre, name='sobre_td'),
    ]

urlpatterns = [
    # Páginas de início
    
    url(r'^', include(inicio_patterns, namespace='inicio')),
    
    # Investidores
    url(r'^login/$', LoginView.as_view(template_name='login.html', authentication_form=ExtendedAuthForm), name='login'),
    url(r'^logout/$', logout, {'next_page': '/login'}, name='logout'),
    url(r'^minha_conta/alterar_senha/$', PasswordChangeView.as_view(template_name='registration/alterar_senha.html', form_class=ExtendedPasswordChangeForm, \
                                                                    extra_context={'pagina_titulo': 'Alteração de senha', 'pagina_descricao': 'Criar uma nova senha para a conta informando a atual'}), name='password_change'),
    url(r'^minha_conta/alterar_senha/sucesso/$', PasswordChangeDoneView.as_view(extra_context={'pagina_titulo': 'Alteração de senha', 'pagina_descricao': 'Criar uma nova senha para a conta informando a atual'}, 
                                                                    template_name='registration/senha_alterada.html'), name='password_change_done'),
    url(r'^senha_esquecida/$', PasswordResetView.as_view(template_name='registration/confirmar_redefinir_senha.html', email_template_name='registration/redefinir_senha_email.html',
                                                                         subject_template_name='registration/redefinir_senha_email_assunto.txt'), name='password_reset'),
    url(r'^senha_esquecida/email_enviado/$', PasswordResetDoneView.as_view(template_name='registration/redefinir_senha_email_enviado.html'), name='password_reset_done'),
    url(r'^redefinicao_senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', PasswordResetConfirmView.as_view(template_name='registration/redefinir_senha.html',
                                                                                                                                             form_class=ExtendedSetPasswordForm, post_reset_login=True), name='password_reset_confirm'),
    url(r'^redefinicao_senha/completa/$', PasswordResetCompleteView.as_view(template_name='registration/senha_redefinida.html'), name='password_reset_complete'),
    # Django-registration
    url(r'^cadastro/$', registration_views.RegistrationView.as_view(form_class=ExtendedUserCreationForm), name='cadastro'),
    url(r'^ativacao/completa/$', TemplateView.as_view(template_name='registration/activation_complete.html'), name='registration_activation_complete'),
    # The activation key can make use of any character from the
    # URL-safe base64 alphabet, plus the colon as a separator.
    url(r'^ativacao/(?P<activation_key>[-:\w]+)/$', registration_views.ActivationView.as_view(), name='ativar_cadastro'),
    url(r'^cadastro/completo/$', TemplateView.as_view(template_name='registration/registration_complete.html'), name='registration_complete'),
#     url(r'^cadastro/fechado/$', TemplateView.as_view(template_name='registration/registration_closed.html'), name='registration_closed'),
    url(r'^minha_conta/$', views.investidores.investidores.minha_conta, name='minha_conta'),
#     url(r'^minha_conta/editar_dados_cadastrais/(?P<id>\d+)/$', views.investidores.investidores.editar_dados_cadastrais, name='editar_dados_cadastrais'),

    # Gerador de proventos
    url(r'^gerador_proventos/', include(gerador_proventos_patterns, namespace='gerador_proventos')),
    
    # Ações
    url(r'^acoes/', include(acoes_patterns, namespace='acoes')),
    
    # Divisões
    url(r'^divisoes/', include(divisoes_patterns, namespace='divisoes')),
    
    # FII
    url(r'^fii/', include(fiis_patterns, namespace='fii')),

    # Tesouro direto
    url(r'^td/', include(td_patterns, namespace='td')),

    # Poupança
    
    # LCA e LCI
    url(r'^lci_lca/', include(lci_lca_patterns, namespace='lci_lca')),
    
    # CDB e RDB
#     url(r'^cdb_rdb/', include(cdb_rdb_patterns, namespace='cdb_rdb')),
    
    # Debêntures
    url(r'^debentures/', include(debentures_patterns, namespace='debentures')),
    
    # Imposto de renda
    url(r'^imposto_renda/', include(imposto_renda_patterns, namespace='imposto_renda')),
]
