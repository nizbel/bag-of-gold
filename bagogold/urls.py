# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin

import settings


admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'bagogold.views.home'', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', admin.site.urls),
    
    # App bagogold
    url(r'', include('bagogold.bagogold.urls')),
    # App Blog
    url(r'^blog/', include('bagogold.blog.urls', namespace='blog')),
    # App CDB/RDB
    url(r'^cdb-rdb/', include('bagogold.cdb_rdb.urls', namespace='cdb_rdb')),
    # App CRI/CRA
    url(r'^cri-cra/', include('bagogold.cri_cra.urls', namespace='cri_cra')),
    # App Criptomoedas
    url(r'^criptomoeda/', include('bagogold.criptomoeda.urls', namespace='criptomoeda')),
    # App LC
    url(r'^lc/', include('bagogold.lc.urls', namespace='lc')),
    # App FII
    url(r'^fii/', include('bagogold.fii.urls', namespace='fii')),
    # App Fundos de investimento
    url(r'^fundo-investimento/', include('bagogold.fundo_investimento.urls', namespace='fundo_investimento')),
    # App LCI/LCA
    url(r'^lci-lca/', include('bagogold.lci_lca.urls', namespace='lci_lca')),
    # App Outros investimentos
    url(r'^outros-investimentos/', include('bagogold.outros_investimentos.urls', namespace='outros_investimentos')),
    # App Tesouro Direto
    url(r'^tesouro-direto/', include('bagogold.tesouro_direto.urls', namespace='tesouro_direto')),
    # App pendencias
    url(r'', include('bagogold.pendencias.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns