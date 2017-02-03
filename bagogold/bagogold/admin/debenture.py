# -*- coding: utf-8 -*-
from bagogold.bagogold.models.debentures import Debenture,  OperacaoDebenture, HistoricoValorDebenture
from django.contrib import admin
 
admin.site.register(Debenture)
    
# admin.site.register(AmortizacaoDebenture)
    
# admin.site.register(JurosDebenture)
    
# admin.site.register(PremioDebenture)
        
admin.site.register(OperacaoDebenture)
    
admin.site.register(HistoricoValorDebenture)