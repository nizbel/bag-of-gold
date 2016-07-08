# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo, HistoricoTitulo, Titulo, \
    ValorDiarioTitulo, HistoricoIPCA
from django.contrib import admin
 
admin.site.register(Titulo)
    
admin.site.register(OperacaoTitulo)
    
admin.site.register(HistoricoTitulo)
            
admin.site.register(ValorDiarioTitulo)
            
admin.site.register(HistoricoIPCA)
