# -*- coding: utf-8 -*-

from bagogold.bagogold.models.debentures import OperacaoDebenture, Debenture,\
    HistoricoValorDebenture
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


@login_required
def detalhar_debenture(request, debenture_id):
    try:
        debenture = Debenture.objects.get(id=debenture_id)
    except Debenture.DoesNotExist:
        messages.error(request, 'Debênture selecionado é inválido')
        return HttpResponseRedirect(reverse('listar_debentures'))
    
    debenture.valor_emissao = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.valor_emissao))
    if debenture.data_fim:
        debenture.valor_atual = Decimal('0.00') 
    else:
        historico = HistoricoValorDebenture.objects.filter(debenture=debenture).order_by('-data')[0]
        debenture.valor_atual = historico.valor_nominal + historico.juros
        debenture.valor_atual = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.valor_atual))
    
    return TemplateResponse(request, 'debentures/detalhar_debenture.html', {'debenture': debenture})

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
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoDebenture, DivisaoOperacaoDebenture, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoDebentureFormSet)
    
    if request.method == 'POST':
        form_operacao_debenture = OperacaoDebentureForm(request.POST)
        formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        if form_operacao_debenture.is_valid():
            operacao_debenture = form_operacao_debenture.save(commit=False)
            operacao_debenture.investidor = investidor
            if varias_divisoes:
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_debenture, investidor=investidor)
                if formset_divisao.is_valid():
                    operacao_debenture.save()
                    formset_divisao.save()
                        
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('historico_debenture'))
                
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
                    
            else:
                operacao_debenture.save()
                divisao_operacao = DivisaoOperacaoDebenture(operacao=operacao_debenture, quantidade=operacao_debenture.quantidade, divisao=investidor.divisaoprincipal.divisao)
                divisao_operacao.save()
                messages.success(request, 'Operação inserida com sucesso')
                return HttpResponseRedirect(reverse('historico_debenture'))
        for erro in formset_divisao.non_form_errors():
            messages.error(request, erro)
            
    else:
        form_operacao_debenture = OperacaoDebentureForm()
        formset_divisao = DivisaoFormSet(investidor=investidor)
            
    return TemplateResponse(request, 'debentures/inserir_operacao_debenture.html', {'form_operacao_debenture': form_operacao_debenture, 'form_uso_proventos': form_uso_proventos,
                                                               'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@login_required
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