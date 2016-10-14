# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII, ProventoFII, OperacaoFII, \
    UsoProventosOperacaoFII, HistoricoFII, ValorDiarioFII
from django.contrib import admin
 
admin.site.register(FII)

class ProventoFIIAdmin(admin.ModelAdmin):
    list_display = ('fii', 'valor_unitario', 'data_ex', 'data_pagamento')
    
admin.site.register(ProventoFII, ProventoFIIAdmin)
    
admin.site.register(OperacaoFII)
    
admin.site.register(UsoProventosOperacaoFII)
    
admin.site.register(HistoricoFII)
        
admin.site.register(ValorDiarioFII)
    