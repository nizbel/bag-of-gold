# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo
from bagogold.pendencias.models.pendencias import \
    PendenciaVencimentoTesouroDireto
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse

@login_required
def painel_pendencias(request):
    investidor = request.user.investidor
    
    return TemplateResponse(request, 'pendencias/painel_pendencias.html', {})