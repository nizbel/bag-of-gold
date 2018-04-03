# -*- coding: utf-8 -*-
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic, \
    HistoricoTaxaDI, HistoricoIPCA
from django.contrib import admin
 
admin.site.register(HistoricoTaxaSelic)

class HistoricoTaxaDIAdmin(admin.ModelAdmin):
    list_display = ('data', 'taxa')
    search_fields = ['data']
    
admin.site.register(HistoricoTaxaDI, HistoricoTaxaDIAdmin)


admin.site.register(HistoricoIPCA)