# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo, HistoricoTitulo, Titulo, \
    ValorDiarioTitulo, HistoricoIPCA
from django.contrib import admin
 
class TituloAdmin(admin.ModelAdmin):
    search_fields = ['tipo', 'data_vencimento']
    list_display = ('tipo', 'data_inicio', 'data_vencimento')
    
admin.site.register(Titulo, TituloAdmin)
    
admin.site.register(OperacaoTitulo)

class HistoricoTituloAdmin(admin.ModelAdmin):
    search_fields = ['titulo__tipo', 'titulo__data_vencimento']
    list_display = ('titulo', 'data', 'preco_compra', 'taxa_compra', 'preco_venda', 'taxa_venda')
    
admin.site.register(HistoricoTitulo, HistoricoTituloAdmin)
            
admin.site.register(ValorDiarioTitulo)
            
admin.site.register(HistoricoIPCA)
