# -*- coding: utf-8 -*-
from django.contrib import admin

from bagogold.lci_lca.models import LetraCredito, OperacaoLetraCredito, \
    OperacaoVendaLetraCredito, HistoricoPorcentagemLetraCredito, \
    HistoricoCarenciaLetraCredito, HistoricoValorMinimoInvestimento, \
    HistoricoVencimentoLetraCredito


admin.site.register(LetraCredito)
    
admin.site.register(OperacaoLetraCredito)
    
class OperacaoVendaLetraCreditoAdmin(admin.ModelAdmin):
    list_display = ('operacao_venda', 'operacao_compra')
    
admin.site.register(OperacaoVendaLetraCredito, OperacaoVendaLetraCreditoAdmin)
    
class HistoricoPorcentagemLetraCreditoAdmin(admin.ModelAdmin):
    list_display = ('letra_credito', 'data', 'porcentagem')
    
admin.site.register(HistoricoPorcentagemLetraCredito, HistoricoPorcentagemLetraCreditoAdmin)
    
class HistoricoCarenciaLetraCreditoAdmin(admin.ModelAdmin):
    list_display = ('letra_credito', 'data', 'carencia')
    
admin.site.register(HistoricoCarenciaLetraCredito, HistoricoCarenciaLetraCreditoAdmin)
            
admin.site.register(HistoricoValorMinimoInvestimento)

class HistoricoVencimentoLetraCreditoAdmin(admin.ModelAdmin):
    list_display = ('letra_credito', 'data', 'vencimento')
    
admin.site.register(HistoricoVencimentoLetraCredito, HistoricoVencimentoLetraCreditoAdmin)
