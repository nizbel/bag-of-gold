# -*- coding: utf-8 -*-
from bagogold.bagogold.models.cdb_rdb import CDB_RDB, OperacaoCDB_RDB, \
    OperacaoVendaCDB_RDB, HistoricoPorcentagemCDB_RDB, HistoricoCarenciaCDB_RDB, \
    HistoricoValorMinimoInvestimentoCDB_RDB
from django.contrib import admin

admin.site.register(CDB_RDB)
    
admin.site.register(OperacaoCDB_RDB)
    
admin.site.register(OperacaoVendaCDB_RDB)
    
admin.site.register(HistoricoPorcentagemCDB_RDB)
    
admin.site.register(HistoricoCarenciaCDB_RDB)
            
admin.site.register(HistoricoValorMinimoInvestimentoCDB_RDB)
