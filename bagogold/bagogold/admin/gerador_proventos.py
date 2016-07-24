# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoBovespa, \
    ProventoAcaoDocumento, ProventoFIIDocumento, Pendencia
from django.contrib import admin


admin.site.register(DocumentoBovespa)
    
admin.site.register(ProventoAcaoDocumento)
    
admin.site.register(ProventoFIIDocumento)

admin.site.register(Pendencia)
