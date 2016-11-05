# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.provento_acao import ProventoAcaoForm
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento
from bagogold.bagogold.testFII import ler_documento_proventos
from bagogold.bagogold.utils.gerador_proventos import \
    alocar_pendencia_para_investidor
from bagogold.bagogold.utils.investidores import is_superuser
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.formsets import formset_factory
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.response import TemplateResponse


@login_required
@user_passes_test(is_superuser)
def ler_documento_provento(request, id):
    pendencia = PendenciaDocumentoProvento.objects.get(id=id)
    
    texto_documento = ler_documento_proventos(pendencia.documento.documento)
    
    # Preparar formset de proventos
    if pendencia.documento.tipo == 'A':
        formset = formset_factory(ProventoAcaoForm, extra=1)
    
    return TemplateResponse(request, 'gerador_proventos/ler_documento_provento.html', {'pendencia': pendencia, 'texto_documento': texto_documento, 'formset': formset})
    
@login_required
@user_passes_test(is_superuser)
def listar_documentos(request):
    empresa_id = 1
    if request.method == 'POST':
        if request.POST.get("busca_empresa"):
            empresa_id = Acao.objects.filter(ticker__istartswith=request.POST['busca_empresa'])[0].empresa.id
    
    # Mostrar empresa atual
    empresa_atual = Empresa.objects.get(id=empresa_id)
    empresa_atual.ticker = empresa_atual.ticker_empresa()
    
    empresas = [empresa.ticker_empresa() for empresa in Empresa.objects.all().order_by('id')]
#     empresas = map(str, empresas)
    empresas = '["' + '","'.join(empresas) + '"]'
    documentos = DocumentoProventoBovespa.objects.filter(empresa__id=empresa_id).order_by('data_referencia')
    
    for documento in documentos:
        documento.nome = documento.documento.name.split('/')[-1]
        
        documento.pendente = documento.pendente()
        
        if documento.tipo == 'A':
            documento.ha_proventos_vinculados = False
            
        # Preparar descrição de tipos
        documento.tipo = 'Ação' if documento.tipo == 'A' else 'FII'
            
    return TemplateResponse(request, 'gerador_proventos/listar_documentos.html', {'documentos': documentos, 'empresas': empresas, 'empresa_atual': empresa_atual})

@login_required
@user_passes_test(is_superuser)
def listar_pendencias(request):
    pendencias = PendenciaDocumentoProvento.objects.all()
    
    for pendencia in pendencias:
        pendencia.nome = pendencia.documento.documento.name.split('/')[-1]
        pendencia.tipo = 'Ação' if pendencia.documento.tipo == 'A' else 'FII'
        pendencia.responsavel = pendencia.responsavel()
        
    return TemplateResponse(request, 'gerador_proventos/listar_pendencias.html', {'pendencias': pendencias})


@login_required
@user_passes_test(is_superuser)
def listar_proventos(request):
    pass

@login_required
@user_passes_test(is_superuser)
def puxar_responsabilidade_documento_provento(request, id_pendencia):
    retorno, mensagem = alocar_pendencia_para_investidor(request.user.investidor, PendenciaDocumentoProvento.objects.get(id=id_pendencia))
    if retorno:
        messages.success(request, mensagem)
    else:
        messages.error(request, mensagem)

@login_required
@user_passes_test(is_superuser)
def validar_documento_provento(request):
    pass