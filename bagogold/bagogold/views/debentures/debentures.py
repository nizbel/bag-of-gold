# -*- coding: utf-8 -*-

from bagogold.bagogold.models.debentures import OperacaoDebenture, Debenture
from bagogold.bagogold.utils.misc import \
    formatar_zeros_a_direita_apos_2_casas_decimais
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
import calendar
import datetime


def detalhar_debenture(request, debenture_id):
    
    return TemplateResponse(request, 'debentures/detalhar_debenture.html', {})

@login_required
def editar_operacao_debenture(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_debenture = OperacaoDebenture.objects.get(pk=operacao_id)
    if operacao_debenture.investidor != investidor:
        raise PermissionDenied
    
    return TemplateResponse(request, 'debentures/editar_operacao_debenture.html', {})  

    
@login_required
def historico(request):
    investidor = request.user.investidor
    
    return TemplateResponse(request, 'debentures/historico.html', {})
    

@login_required
def inserir_operacao_debenture(request):
    investidor = request.user.investidor
    
    return TemplateResponse(request, 'cdb_rdb/inserir_operacao_debenture.html', {})

def listar_debentures(request):
    debentures = Debenture.objects.all()
    
    for debenture in debentures:
        debenture.porcentagem = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.porcentagem))
        
        if hasattr(debenture, 'jurosdebenture'):
            debenture.jurosdebenture.taxa = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.jurosdebenture.taxa))
        if hasattr(debenture, 'amortizacaodebenture'):
            debenture.amortizacaodebenture.taxa = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.amortizacaodebenture.taxa))
        if hasattr(debenture, 'premiodebenture'):
            debenture.premiodebenture.taxa = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.premiodebenture.taxa))
    
    return TemplateResponse(request, 'debentures/listar_debentures.html', {'debentures': debentures})

@login_required
def painel(request):
    investidor = request.user.investidor
    
    return TemplateResponse(request, 'debentures/painel.html', {})