# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    ProventoAcaoDocumento, ProventoFIIDocumento, PendenciaDocumentoProvento, \
    ProventoAcaoDescritoDocumentoBovespa, ProventoFIIDescritoDocumentoBovespa, \
    InvestidorLeituraDocumento, InvestidorRecusaDocumento, \
    InvestidorResponsavelPendencia, InvestidorValidacaoDocumento, PagamentoLeitura
from bagogold.bagogold.models.investidores import Investidor
from django.contrib import admin



class DocumentoProventoBovespaAdmin(admin.ModelAdmin):
    search_fields = ['protocolo', 'tipo_documento']
    list_display = ('nome_documento', 'data_referencia', 'protocolo', 'empresa', 'tipo_documento')
    
    def nome_documento(self, obj):
        return unicode(obj)
    nome_documento.short_description = 'Nome'
    
admin.site.register(DocumentoProventoBovespa, DocumentoProventoBovespaAdmin)
    
class InvestidorLeituraDocumentoAdmin(admin.ModelAdmin):
    list_display = ('investidor', 'documento', 'decisao', 'data_leitura')

admin.site.register(InvestidorLeituraDocumento, InvestidorLeituraDocumentoAdmin)

class InvestidorRecusaDocumentoAdmin(admin.ModelAdmin):
    list_display = ('investidor', 'documento', 'responsavel_leitura', 'data_recusa')

admin.site.register(InvestidorRecusaDocumento, InvestidorRecusaDocumentoAdmin)
    
class InvestidorResponsavelPendenciaAdmin(admin.ModelAdmin):
    search_fields = ['investidor__user__username', 'pendencia__documento__protocolo']
    list_display = ('investidor', 'documento')

    def documento(self, obj):
        return obj.pendencia.documento
    documento.short_description = 'Documento'

admin.site.register(InvestidorResponsavelPendencia, InvestidorResponsavelPendenciaAdmin)
        
class InvestidorValidacaoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('investidor', 'documento', 'data_validacao')

admin.site.register(InvestidorValidacaoDocumento, InvestidorValidacaoDocumentoAdmin)
    
class ProventoAcaoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('provento', 'documento', 'versao')
    
admin.site.register(ProventoAcaoDocumento, ProventoAcaoDocumentoAdmin)

class ProventoAcaoDescritoDocumentoBovespaAdmin(admin.ModelAdmin):
    list_display = ('acao', 'valor_unitario', 'tipo_provento', 'data_ex', 'data_pagamento')
    
admin.site.register(ProventoAcaoDescritoDocumentoBovespa, ProventoAcaoDescritoDocumentoBovespaAdmin)
    
class ProventoFIIDocumentoAdmin(admin.ModelAdmin):
    list_display = ('provento', 'documento', 'versao')
    
admin.site.register(ProventoFIIDocumento, ProventoFIIDocumentoAdmin)

class ProventoFIIDescritoDocumentoBovespaAdmin(admin.ModelAdmin):
    list_display = ('fii', 'valor_unitario', 'data_ex', 'data_pagamento')
    
admin.site.register(ProventoFIIDescritoDocumentoBovespa, ProventoFIIDescritoDocumentoBovespaAdmin)

class PendenciaDocumentoProventoAdmin(admin.ModelAdmin):
    search_fields = ['documento__protocolo', 'data_criacao']
    list_display = ('documento', 'data_criacao', 'tipo_completo', 'responsavel')
    
    def tipo_completo(self, obj):
        return 'Leitura' if obj.tipo == 'L' else 'Validação'
    tipo_completo.short_description = 'Tipo de pendência'
    
admin.site.register(PendenciaDocumentoProvento, PendenciaDocumentoProventoAdmin)

class PagamentoLeituraAdmin(admin.ModelAdmin):
    search_fields = ['investidor', 'data', 'valor']
    list_display = ('investidor', 'valor', 'data')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "investidor":
            kwargs["queryset"] = Investidor.objects.filter(user__groups__name='Equipe de leitura')
        return super(PagamentoLeituraAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    
admin.site.register(PagamentoLeitura, PagamentoLeituraAdmin)