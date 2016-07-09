# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fundo_investimento import FundoInvestimento, \
    OperacaoFundoInvestimento, HistoricoValorCotas, \
    HistoricoCarenciaFundoInvestimento, \
    HistoricoValorMinimoInvestimentoFundoInvestimento
from django.contrib import admin

admin.site.register(FundoInvestimento)
    
admin.site.register(OperacaoFundoInvestimento)

admin.site.register(HistoricoValorCotas)

admin.site.register(HistoricoCarenciaFundoInvestimento)
            
admin.site.register(HistoricoValorMinimoInvestimentoFundoInvestimento)
    
