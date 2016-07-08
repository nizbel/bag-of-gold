# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import LetraCredito, OperacaoLetraCredito, \
    OperacaoVendaLetraCredito, HistoricoPorcentagemLetraCredito, \
    HistoricoCarenciaLetraCredito, HistoricoValorMinimoInvestimento, HistoricoTaxaDI
from django.contrib import admin

admin.site.register(LetraCredito)
    
admin.site.register(OperacaoLetraCredito)
    
admin.site.register(OperacaoVendaLetraCredito)
    
admin.site.register(HistoricoPorcentagemLetraCredito)
    
admin.site.register(HistoricoCarenciaLetraCredito)
            
admin.site.register(HistoricoValorMinimoInvestimento)
    
admin.site.register(HistoricoTaxaDI)
