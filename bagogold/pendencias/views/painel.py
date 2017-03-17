# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo
from bagogold.pendencias.models.pendencias import \
    PendenciaVencimentoTesouroDireto, Pendencia,\
    PendenciaDocumentoGeradorProventos
from bagogold.pendencias.utils.investidor import buscar_pendencias_investidor, \
    verificar_pendencias_investidor
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse

@login_required
def painel_pendencias(request):
    investidor = request.user.investidor
    
    # Garante que as pendencias são corretas atualmente
    verificar_pendencias_investidor(investidor)
    
    pendencias = buscar_pendencias_investidor(investidor)
    pendencias_tesouro_direto = [pendencia for pendencia in pendencias if hasattr(pendencia, 'tipo_investimento') and pendencia.tipo_investimento() == Pendencia.TESOURO_DIRETO]
    pendencia_doc_gerador_proventos = [pendencia for pendencia in pendencias if isinstance(pendencia, PendenciaDocumentoGeradorProventos)]
    
    return TemplateResponse(request, 'pendencias/painel_pendencias.html', {'qtd_pendencias': len(pendencias), 'pendencias_tesouro_direto': pendencias_tesouro_direto, 
                                                                           'pendencia_doc_gerador_proventos': pendencia_doc_gerador_proventos})