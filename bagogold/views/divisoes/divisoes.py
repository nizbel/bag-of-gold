# -*- coding: utf-8 -*-
from bagogold.forms.divisoes import DivisaoForm
from bagogold.models.divisoes import Divisao, DivisaoOperacaoLC
from bagogold.models.lc import HistoricoTaxaDI, HistoricoPorcentagemLetraCredito
from decimal import Decimal
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext

def detalhar_divisao(request, id):
    divisao = Divisao.objects.filter(id=id)
    
    return render_to_response('divisoes/detalhar_divisao.html', {'divisao': divisao},
                               context_instance=RequestContext(request))
    
def inserir_divisao(request):
    if request.method == 'POST':
        form = DivisaoForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('listar_divisoes'))
    else:
        form = DivisaoForm()
            
    return render_to_response('divisoes/inserir_divisao.html', {'form': form}, context_instance=RequestContext(request))

def listar_divisoes(request):
    divisoes = Divisao.objects.all()
    
    for divisao in divisoes:
        divisao.valor_atual = 0
        # TODO calcular valor atual
        lc_divisao = DivisaoOperacaoLC.objects.filter(divisao__id=divisao.id)
        for lc in lc_divisao:
            # Pegar taxa da época da operação
            lc.operacao.taxa = HistoricoPorcentagemLetraCredito.objects.filter(data__lte=lc.operacao.data).order_by('-data')[0].porcentagem_di
            lc.total = lc.quantidade
            taxas = HistoricoTaxaDI.objects.filter(data__gte=lc.operacao.data).values('taxa')
            # Calcular o valor atualizado do patrimonio diariamente
            for item in taxas:
                lc.total = Decimal((pow((float(1) + float(item['taxa'])/float(100)), float(1)/float(252)) - float(1)) * float(lc.operacao.taxa/100) + float(1)) * lc.total
                # TODO arredondar
            divisao.valor_atual += lc.total
        
        if divisao.valor_objetivo is not None:
            divisao.quantidade_percentual = divisao.valor_atual / divisao.valor_objetivo * 100
        else:
            divisao.quantidade_percentual = 100
    
    return render_to_response('divisoes/listar_divisoes.html', {'divisoes': divisoes}, context_instance=RequestContext(request))