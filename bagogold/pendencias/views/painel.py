# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo
from bagogold.pendencias.models.pendencias import \
    PendenciaVencimentoTesouroDireto, Pendencia
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
    pendencias_tesouro_direto = [pendencia for pendencia in pendencias if pendencia.tipo_investimento() == Pendencia.TESOURO_DIRETO]
    
    return TemplateResponse(request, 'pendencias/painel_pendencias.html', {'pendencias_tesouro_direto': pendencias_tesouro_direto})