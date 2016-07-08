# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII, ProventoFII, OperacaoFII, \
    UsoProventosOperacaoFII, HistoricoFII, ValorDiarioFII
from django.contrib import admin
 
admin.site.register(FII)
    
admin.site.register(ProventoFII)
    
admin.site.register(OperacaoFII)
    
admin.site.register(UsoProventosOperacaoFII)
    
admin.site.register(HistoricoFII)
        
admin.site.register(ValorDiarioFII)
    