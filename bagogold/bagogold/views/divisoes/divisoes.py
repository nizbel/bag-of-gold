# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.divisoes import DivisaoForm
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC, \
    DivisaoOperacaoFII
from bagogold.bagogold.models.lc import HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito, LetraCredito
from bagogold.bagogold.utils.lc import calcular_valor_lc_ate_dia, \
    calcular_valor_lc_ate_dia_por_divisao
from decimal import Decimal
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import datetime

def detalhar_divisao(request, id):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    divisao = Divisao.objects.filter(id=id)
    divisao.valor_total = 0
    
    composicao = {}
    
    # Adicionar letras de crédito
    composicao['lc'] = Object()
    composicao['lc'].nome = 'Letras de Crédito'
    composicao['lc'].patrimonio = 0
    composicao['lc'].composicao = {}
    valores_letras_credito_dia = calcular_valor_lc_ate_dia(datetime.date.today())
    for lc_id in valores_letras_credito_dia.keys():
        composicao['lc'].patrimonio += valores_letras_credito_dia[lc_id]
        composicao['lc'].composicao[lc_id] = Object()
        lc_nome = LetraCredito.objects.get(id=lc_id).nome
        composicao['lc'].composicao[lc_id].nome = lc_nome
        composicao['lc'].composicao[lc_id].valor = valores_letras_credito_dia[lc_id]
    
    # Calcular valor total da divisão
    for item in composicao.values():
        divisao.valor_total += item.patrimonio
        
    # Calcular valor percentual para cada item da composição da divisão
    for item in composicao.values():
        item.percentual = item.patrimonio / divisao.valor_total * 100
        
    return render_to_response('divisoes/detalhar_divisao.html', {'divisao': divisao, 'composicao': composicao},
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
        # Fundos de investimento imobiliário
        fii_divisao = DivisaoOperacaoFII.objects.filter(divisao__id=divisao.id)
        for fii in fii_divisao:
            print 'oi'
        # Letras de crédito
        lc_divisao = calcular_valor_lc_ate_dia_por_divisao(datetime.date.today(), divisao.id)
        for total_lc in lc_divisao.values():
            print total_lc
            divisao.valor_atual += total_lc
        
        if not divisao.objetivo_indefinido():
            divisao.quantidade_percentual = divisao.valor_atual / divisao.valor_objetivo * 100
        else:
            divisao.quantidade_percentual = 100
    
    return render_to_response('divisoes/listar_divisoes.html', {'divisoes': divisoes}, context_instance=RequestContext(request))