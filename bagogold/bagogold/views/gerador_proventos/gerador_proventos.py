# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, PendenciaDocumentoProvento
from bagogold.bagogold.utils.investidores import is_superuser
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response
from django.template.context import RequestContext


@login_required
@user_passes_test(is_superuser)
def listar_proventos(request):
    pass


@login_required
@user_passes_test(is_superuser)
def resolver_pendencia(request):
    pass


@login_required
@user_passes_test(is_superuser)
def listar_documentos(request):
    documentos = DocumentoProventoBovespa.objects.all()
    
    for documento in documentos:
        documento.nome = documento.documento.name.split('/')[-1]
        
        documento.pendente = documento.pendente()
    return render_to_response('gerador_proventos/listar_documentos.html', {'documentos': documentos},
                              context_instance=RequestContext(request))

@login_required
@user_passes_test(is_superuser)
def listar_pendencias(request):
    pendencias = PendenciaDocumentoProvento.objects.all()
    
    for pendencia in pendencias:
        pendencia.nome = pendencia.documento.documento.name.split('/')[-1]
        
    return render_to_response('gerador_proventos/listar_pendencias.html', {'pendencias': pendencias},
                              context_instance=RequestContext(request))
