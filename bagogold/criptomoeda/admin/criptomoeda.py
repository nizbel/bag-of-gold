# -*- coding: utf-8 -*-
from bagogold.criptomoeda.models import Criptomoeda, OperacaoCriptomoeda, HistoricoValorCriptomoeda,\
    OperacaoCriptomoedaMoeda, OperacaoCriptomoedaTaxa, TransferenciaCriptomoeda
from django.contrib import admin

class CriptomoedaAdmin(admin.ModelAdmin):
    search_fields = ['nome', 'ticker']
    list_display = ('nome', 'ticker')
    
admin.site.register(Criptomoeda, CriptomoedaAdmin)
    
admin.site.register(OperacaoCriptomoeda)

admin.site.register(OperacaoCriptomoedaTaxa)

admin.site.register(OperacaoCriptomoedaMoeda)
    
class HistoricoValorCriptomoedaAdmin(admin.ModelAdmin):
    search_fields = ['criptomoeda']
    list_display = ('criptomoeda', 'data', 'valor')
    
admin.site.register(HistoricoValorCriptomoeda, HistoricoValorCriptomoedaAdmin)

admin.site.register(TransferenciaCriptomoeda)