# -*- coding: utf-8 -*-

from bagogold.forms.lc import OperacaoLetraCreditoForm, \
    HistoricoPorcentagemLetraCreditoForm
from bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import calendar

@login_required
def editar_operacao_lc(request, id):
    print '1'

    
@login_required
def historico(request):
    operacoes = OperacaoLetraCredito.objects.exclude(data__isnull=True).order_by('data') 
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.all() 
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        operacao.taxa = historico_porcentagem.filter(data__lte=operacao.data).order_by('-data')[0].porcentagem_di
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
        else:
            operacao.tipo = 'Venda'
    
    # Pegar data inicial
    data_inicial = operacoes[0].data
    
    # Pegar data final
    data_final = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    letras_credito = {}
    total_gasto = 0
    total_patrimonio = 0
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    graf_gasto_total = list()
    graf_patrimonio = list()
    
    while data_iteracao <= data_final:
        # Processar operações
        operacoes_do_dia = operacoes.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            if operacao.letra_credito not in letras_credito.keys():
                letras_credito[operacao.letra_credito] = 0
            # Verificar se se trata de compra ou venda
            if operacao.tipo_operacao == 'C':
                operacao.total = operacao.quantidade
                total_gasto += operacao.total
                letras_credito[operacao.letra_credito] += operacao.quantidade
                    
            elif operacao.tipo_operacao == 'V':
                operacao.total = operacao.quantidade
                total_gasto -= operacao.total
                letras_credito[operacao.letra_credito] -= operacao.quantidade
                
        taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
        # Calcular o valor atualizado do patrimonio diariamente
        total_patrimonio = 0
        # Calcular o valor atualizado para cada operacao
        for operacao in operacoes:
            if (operacao.data <= data_iteracao):
                operacao.atual = Decimal((pow((float(1) + float(taxa_do_dia)/float(100)), float(1)/float(252)) - float(1)) * float(operacao.taxa/100) + float(1)) * operacao.atual
                # Arredondar na última iteração
                if (data_iteracao == data_final):
                    str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                    operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                total_patrimonio += operacao.atual
        
                
        if len(operacoes_do_dia) > 0 or data_iteracao == data_final:
            graf_gasto_total += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_gasto)]]
            graf_patrimonio += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_patrimonio)]]
        
        # Proximo dia útil
        proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
        if len(proximas_datas) > 0:
            data_iteracao = proximas_datas[0].data
        else:
            break
                 
    dados = {}
    dados['total_gasto'] = total_gasto
    dados['patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio - total_gasto
    dados['lucro_percentual'] = (total_patrimonio - total_gasto) / total_gasto * 100
    
    return render_to_response('lc/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio},
                               context_instance=RequestContext(request))
    

@login_required
def inserir_lc(request):
    print '1'

@login_required
def inserir_operacao_lc(request):
    if request.method == 'POST':
        form = OperacaoLetraCreditoForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('historico_lc'))
    else:
        form = OperacaoLetraCreditoForm()
            
    return render_to_response('lc/inserir_operacao_lc.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def modificar_porcentagem_di_lc(request):
    if request.method == 'POST':
        form = HistoricoPorcentagemLetraCreditoForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('historico_lc'))
    else:
        form = HistoricoPorcentagemLetraCreditoForm()
            
    return render_to_response('lc/modificar_porcentagem_di_lc.html', {'form': form}, context_instance=RequestContext(request))