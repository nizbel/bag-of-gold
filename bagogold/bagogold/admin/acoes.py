# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, Provento, AcaoProvento, \
    OperacaoAcao, UsoProventosOperacaoAcao, OperacaoCompraVenda, HistoricoAcao, \
    ValorDiarioAcao, TaxaCustodiaAcao
from django.contrib import admin
from django.db import models
import datetime



admin.site.register(Acao)
    
admin.site.register(Provento)

admin.site.register(AcaoProvento)
    
admin.site.register(OperacaoAcao)

admin.site.register(UsoProventosOperacaoAcao)

admin.site.register(OperacaoCompraVenda)
    
admin.site.register(HistoricoAcao)
    
admin.site.register(ValorDiarioAcao)
    
admin.site.register(TaxaCustodiaAcao)
