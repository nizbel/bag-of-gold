# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    # Pendências
    url(r'^painel-pendencias/$', views.painel.painel_pendencias, name='painel_pendencias'),
    url(r'^resolver-pendencia-vencimento-td/$', views.resolver.resolver_pendencia_vencimento_td, name='resolver_pendencia_vencimento_td'),
]
