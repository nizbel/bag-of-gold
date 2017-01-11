# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    ProventoAcaoDocumento, ProventoFIIDocumento, PendenciaDocumentoProvento
from django.contrib import admin



class DocumentoProventoBovespaAdmin(admin.ModelAdmin):
    search_fields = ['empresa__nome', 'protocolo']
    list_display = ('nome_documento', 'data_referencia', 'protocolo', 'empresa')
    
    def nome_documento(self, obj):
        return obj.documento.name.split('/')[-1]
    nome_documento.short_description = 'Nome'
    
admin.site.register(DocumentoProventoBovespa, DocumentoProventoBovespaAdmin)
    
class ProventoAcaoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('provento', 'documento', 'versao')
    
admin.site.register(ProventoAcaoDocumento, ProventoAcaoDocumentoAdmin)
    
class ProventoFIIDocumentoAdmin(admin.ModelAdmin):
    list_display = ('provento', 'documento', 'versao')
    
admin.site.register(ProventoFIIDocumento, ProventoFIIDocumentoAdmin)

class PendenciaDocumentoProventoAdmin(admin.ModelAdmin):
    search_fields = ['empresa__nome', 'protocolo']
    list_display = ('documento', 'data_criacao', 'tipo_completo', 'responsavel')
    
    def tipo_completo(self, obj):
        return 'Leitura' if obj.tipo == 'L' else 'Validação'
    tipo_completo.short_description = 'Tipo de pendência'

admin.site.register(PendenciaDocumentoProvento, PendenciaDocumentoProventoAdmin)
