# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'bagogold.views.home'', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', admin.site.urls),
    
    # App bagogold
    url(r'', include('bagogold.bagogold.urls')),
    # App CDB/RDB
    url(r'^cdb-rdb/', include('bagogold.cdb_rdb.urls', namespace='cdb_rdb')),
    # App CRI/CRA
    url(r'^cri-cra/', include('bagogold.cri_cra.urls', namespace='cri_cra')),
    # App Criptomoedas
    url(r'^criptomoeda/', include('bagogold.criptomoeda.urls', namespace='criptomoeda')),
    # App Fundos de investimento
    url(r'^fundo-investimento/', include('bagogold.fundo_investimento.urls', namespace='fundo_investimento')),
    # App Outros investimentos
    url(r'^outros-investimentos/', include('bagogold.outros_investimentos.urls', namespace='outros_investimentos')),
    # App pendencias
    url(r'', include('bagogold.pendencias.urls')),
]
