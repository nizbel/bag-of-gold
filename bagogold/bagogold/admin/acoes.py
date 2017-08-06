# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, Provento, AcaoProvento, \
    OperacaoAcao, UsoProventosOperacaoAcao, OperacaoCompraVenda, HistoricoAcao, \
    ValorDiarioAcao, TaxaCustodiaAcao
from django.contrib import admin


admin.site.register(Acao)

class ProventoAdmin(admin.ModelAdmin):
    search_fields = ['acao__ticker']
    list_display = ('acao', 'tipo_provento', 'valor_unitario', 'data_ex', 'data_pagamento')
    
    def get_queryset(self, request):
        # use our manager, rather than the default one
        qs = self.model.gerador_objects.get_queryset()
    
        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
admin.site.register(Provento, ProventoAdmin)

admin.site.register(AcaoProvento)
    
admin.site.register(OperacaoAcao)

admin.site.register(UsoProventosOperacaoAcao)

admin.site.register(OperacaoCompraVenda)

class HistoricoAcaoAdmin(admin.ModelAdmin):
    search_fields = ['acao_ticker', 'data']
    lista_display = ('acao', 'preco_unitario', 'data')
    
admin.site.register(HistoricoAcao, HistoricoAcaoAdmin)
    
admin.site.register(ValorDiarioAcao)
    
admin.site.register(TaxaCustodiaAcao)
