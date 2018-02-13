# -*- coding: utf-8 -*-
from bagogold.lci_lca.models import LetraCredito, OperacaoLetraCredito, \
    OperacaoVendaLetraCredito, HistoricoPorcentagemLetraCredito, \
    HistoricoCarenciaLetraCredito, HistoricoValorMinimoInvestimento
from django.contrib import admin

admin.site.register(LetraCredito)
    
admin.site.register(OperacaoLetraCredito)
    
class OperacaoVendaLetraCreditoAdmin(admin.ModelAdmin):
    list_display = ('operacao_venda', 'operacao_compra')
    
admin.site.register(OperacaoVendaLetraCredito, OperacaoVendaLetraCreditoAdmin)
    
admin.site.register(HistoricoPorcentagemLetraCredito)
    
admin.site.register(HistoricoCarenciaLetraCredito)
            
admin.site.register(HistoricoValorMinimoInvestimento)
