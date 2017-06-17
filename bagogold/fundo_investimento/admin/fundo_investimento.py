# -*- coding: utf-8 -*-
from django.contrib import admin
from bagogold.fundo_investimento.models import FundoInvestimento,\
    OperacaoFundoInvestimento, Administrador, HistoricoValorCotas,\
    DocumentoCadastro, LinkDocumentoCadastro

class FundoInvestimentoAdmin(admin.ModelAdmin):
    search_fields = ['nome', 'cnpj']
    list_display = ('nome', 'cnpj', 'administrador', 'data_constituicao', 'situacao', 'classe', 'exclusivo_qualificados', 'ultimo_registro')
    
admin.site.register(FundoInvestimento, FundoInvestimentoAdmin)
    
admin.site.register(OperacaoFundoInvestimento)
    
class AdministradorAdmin(admin.ModelAdmin):
    search_fields = ['nome', 'cnpj']
    list_display = ('nome', 'cnpj')
    
admin.site.register(Administrador, AdministradorAdmin)
    
class HistoricoValorCotasAdmin(admin.ModelAdmin):
    search_fields = ['fundo_investimento']
    list_display = ('fundo_investimento', 'data', 'valor_cota')
    
admin.site.register(HistoricoValorCotas, HistoricoValorCotasAdmin)

class DocumentoCadastroAdmin(admin.ModelAdmin):
    search_fields = ['data_referencia']
    list_display = ('data_referencia', 'data_pedido_cvm', 'leitura_realizada')
    
admin.site.register(DocumentoCadastro, DocumentoCadastroAdmin)

class LinkDocumentoCadastroAdmin(admin.ModelAdmin):
    search_fields = ['documento']
    list_display = ('documento', 'url', 'data_pedido_cvm')
    
    def data_pedido_cvm(self, obj):
        return obj.documento.data_pedido_cvm
    data_pedido_cvm.short_description = 'Data de pedido a CVM'
    
admin.site.register(LinkDocumentoCadastro, LinkDocumentoCadastroAdmin)
    
