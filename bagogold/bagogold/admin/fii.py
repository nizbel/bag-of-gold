# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII, ProventoFII, OperacaoFII, \
    UsoProventosOperacaoFII, HistoricoFII, ValorDiarioFII, EventoIncorporacaoFII, \
    EventoAgrupamentoFII, EventoDesdobramentoFII
from django.contrib import admin
 
admin.site.register(FII)

class ProventoFIIAdmin(admin.ModelAdmin):
    search_fields = ['fii__ticker']
    list_display = ('fii', 'valor_unitario', 'data_ex', 'data_pagamento')
    
    def get_queryset(self, request):
        # use our manager, rather than the default one
        qs = self.model.gerador_objects.get_queryset()
    
        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
admin.site.register(ProventoFII, ProventoFIIAdmin)
    
admin.site.register(OperacaoFII)
    
admin.site.register(UsoProventosOperacaoFII)

class HistoricoFIIAdmin(admin.ModelAdmin):
    search_fields = ['fii__ticker']
    list_display = ('fii', 'preco_unitario', 'data')
    
admin.site.register(HistoricoFII, HistoricoFIIAdmin)
        
admin.site.register(ValorDiarioFII)
    
class EventoIncorporacaoFIIAdmin(admin.ModelAdmin):
    search_fields = ['fii__ticker']
    list_display = ('fii', 'data', 'novo_fii')
    
admin.site.register(EventoIncorporacaoFII, EventoIncorporacaoFIIAdmin)
    
class EventoAgrupamentoFIIAdmin(admin.ModelAdmin):
    search_fields = ['fii__ticker']
    list_display = ('fii', 'data', 'proporcao')
    
admin.site.register(EventoAgrupamentoFII, EventoAgrupamentoFIIAdmin)
    
class EventoDesdobramentoFIIAdmin(admin.ModelAdmin):
    search_fields = ['fii__ticker']
    list_display = ('fii', 'data', 'proporcao')
    
admin.site.register(EventoDesdobramentoFII, EventoDesdobramentoFIIAdmin)