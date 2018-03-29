# -*- coding: utf-8 -*-
from bagogold.outros_investimentos.models import Investimento, InvestimentoTaxa, \
    Rendimento, PeriodoRendimentos, Amortizacao, ImpostoRendaRendimento, \
    ImpostoRendaValorEspecifico
from django.contrib import admin


admin.site.register(Investimento)

admin.site.register(InvestimentoTaxa)

admin.site.register(Rendimento)

admin.site.register(PeriodoRendimentos)

admin.site.register(Amortizacao)

admin.site.register(ImpostoRendaRendimento)
    
admin.site.register(ImpostoRendaValorEspecifico)
    