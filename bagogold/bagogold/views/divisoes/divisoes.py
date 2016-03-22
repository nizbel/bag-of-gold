# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.divisoes import DivisaoForm
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC
from bagogold.bagogold.models.lc import HistoricoTaxaDI, HistoricoPorcentagemLetraCredito, \
    LetraCredito
from bagogold.bagogold.utils.lc import calcular_valor_lc_ate_dia
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
        lc_divisao = DivisaoOperacaoLC.objects.filter(divisao__id=divisao.id)
        for lc in lc_divisao:
            # Pegar taxa da época da operação
            lc.operacao.taxa = HistoricoPorcentagemLetraCredito.objects.filter(data__lte=lc.operacao.data).order_by('-data')[0].porcentagem_di
            lc.total = lc.quantidade
            taxas = HistoricoTaxaDI.objects.filter(data__gte=lc.operacao.data)
            # Calcular o valor atualizado do patrimonio diariamente
            for item in taxas:
                lc.total = Decimal((pow((float(1) + float(item.taxa)/float(100)), float(1)/float(252)) - float(1)) * float(lc.operacao.taxa/100) + float(1)) * lc.total
                # Arredondar na última iteração
                if (item.data == taxas[len(taxas) - 1].data):
                    str_auxiliar = str(lc.total.quantize(Decimal('.0001')))
                    lc.total = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            divisao.valor_atual += lc.total
        
        if not divisao.objetivo_indefinido():
            divisao.quantidade_percentual = divisao.valor_atual / divisao.valor_objetivo * 100
        else:
            divisao.quantidade_percentual = 100
    
    return render_to_response('divisoes/listar_divisoes.html', {'divisoes': divisoes}, context_instance=RequestContext(request))