# -*- coding: utf-8 -*-
from bagogold.debentures.models import Debenture, AmortizacaoDebenture, \
    JurosDebenture, PremioDebenture, OperacaoDebenture, HistoricoValorDebenture
from django.contrib import admin
  
admin.site.register(Debenture)
     
admin.site.register(AmortizacaoDebenture)
     
admin.site.register(JurosDebenture)
     
admin.site.register(PremioDebenture)
         
admin.site.register(OperacaoDebenture)
     
class HistoricoValorDebentureAdmin(admin.ModelAdmin):
    search_fields = ['debenture__codigo']
    list_display = ('debenture', 'valor_nominal', 'juros', 'premio', 'data')
    
admin.site.register(HistoricoValorDebenture, HistoricoValorDebentureAdmin)