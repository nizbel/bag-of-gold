# -*- coding: utf-8 -*-
from bagogold.debentures.models import Debenture, AmortizacaoDebenture, \
    JurosDebenture, PremioDebenture, OperacaoDebenture, HistoricoValorDebenture
from django.contrib import admin
  
admin.site.register(Debenture)
     
admin.site.register(AmortizacaoDebenture)
     
admin.site.register(JurosDebenture)
     
admin.site.register(PremioDebenture)
         
admin.site.register(OperacaoDebenture)
     
admin.site.register(HistoricoValorDebenture)