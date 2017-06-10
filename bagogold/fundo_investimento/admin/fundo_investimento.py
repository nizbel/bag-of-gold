# -*- coding: utf-8 -*-
from django.contrib import admin
from bagogold.fundo_investimento.models import FundoInvestimento,\
    OperacaoFundoInvestimento, Administrador, HistoricoValorCotas,\
    DocumentoCadastro, LinkDocumentoCadastro

admin.site.register(FundoInvestimento)
    
admin.site.register(OperacaoFundoInvestimento)
    
admin.site.register(Administrador)
    
admin.site.register(HistoricoValorCotas)

admin.site.register(DocumentoCadastro)

admin.site.register(LinkDocumentoCadastro)
    
