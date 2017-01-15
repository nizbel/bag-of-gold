# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    ProventoAcaoDocumento, ProventoFIIDocumento, PendenciaDocumentoProvento, \
    ProventoAcaoDescritoDocumentoBovespa, ProventoFIIDescritoDocumentoBovespa
from django.contrib import admin



class DocumentoProventoBovespaAdmin(admin.ModelAdmin):
    search_fields = ['protocolo']
    list_display = ('nome_documento', 'data_referencia', 'protocolo', 'empresa')
    
    def nome_documento(self, obj):
        return unicode(obj)
    nome_documento.short_description = 'Nome'
    
admin.site.register(DocumentoProventoBovespa, DocumentoProventoBovespaAdmin)
    
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
