# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoPrincipal, \
    DivisaoOperacaoLC, DivisaoOperacaoCDB_RDB, DivisaoOperacaoAcao, \
    DivisaoOperacaoTD, DivisaoOperacaoFII, TransferenciaEntreDivisoes
from django.contrib import admin

admin.site.register(Divisao)
    
admin.site.register(DivisaoPrincipal)
    
admin.site.register(DivisaoOperacaoLC)
    
admin.site.register(DivisaoOperacaoCDB_RDB)
    
admin.site.register(DivisaoOperacaoAcao)
    
admin.site.register(DivisaoOperacaoTD)
    
admin.site.register(DivisaoOperacaoFII)
    
admin.site.register(TransferenciaEntreDivisoes)
