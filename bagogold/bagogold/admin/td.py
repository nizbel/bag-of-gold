# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo, HistoricoTitulo, Titulo, \
    ValorDiarioTitulo, HistoricoIPCA
from django.contrib import admin
 
admin.site.register(Titulo)
    
admin.site.register(OperacaoTitulo)

class HistoricoTituloAdmin(admin.ModelAdmin):
    search_fields = ['titulo__tipo']
    list_display = ('titulo', 'data', 'preco_compra', 'taxa_compra', 'preco_venda', 'taxa_venda')
    
admin.site.register(HistoricoTitulo, HistoricoTituloAdmin)
            
admin.site.register(ValorDiarioTitulo)
            
admin.site.register(HistoricoIPCA)
