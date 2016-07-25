# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoBovespa, \
    ProventoAcaoDocumento, ProventoFIIDocumento, Pendencia
from django.contrib import admin



class DocumentoBovespaAdmin(admin.ModelAdmin):
    search_fields = ['empresa__nome', 'protocolo']
    list_display = ('nome_documento', 'data_referencia', 'protocolo', 'empresa')
    
    def nome_documento(self, obj):
        return obj.documento.name.split('/')[-1]
    nome_documento.short_description = 'Nome'
    
admin.site.register(DocumentoBovespa, DocumentoBovespaAdmin)
    
admin.site.register(ProventoAcaoDocumento)
    
admin.site.register(ProventoFIIDocumento)

admin.site.register(Pendencia)
