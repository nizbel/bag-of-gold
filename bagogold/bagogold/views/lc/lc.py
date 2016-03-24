# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.divisoes import DivisaoOperacaoLCFormSet
from bagogold.bagogold.forms.lc import OperacaoLetraCreditoForm, \
    HistoricoPorcentagemLetraCreditoForm, LetraCreditoForm, \
    HistoricoCarenciaLetraCreditoForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLC
from bagogold.bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito, LetraCredito, HistoricoCarenciaLetraCredito
from decimal import Decimal, ROUND_DOWN
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import calendar
import datetime

@login_required
def editar_operacao_lc(request, id):
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoLetraCredito, DivisaoOperacaoLC, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoLCFormSet)
    operacao_lc = OperacaoLetraCredito.objects.get(pk=id)
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_lc = OperacaoLetraCreditoForm(request.POST, instance=operacao_lc)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc)
            
            if form_operacao_lc.is_valid():
                if formset_divisao.is_valid():
                    operacao_lc.save()
                    formset_divisao.save()
                    return HttpResponseRedirect(reverse('historico_lc'))
            for erro in formset_divisao.non_form_errors():
                messages.error(request, erro)
            return render_to_response('lc/editar_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao },
                      context_instance=RequestContext(request))
#                         print '%s %s'  % (divisao_lc.quantidade, divisao_lc.divisao)
                
        elif request.POST.get("delete"):
            divisao_lc = DivisaoOperacaoLC.objects.filter(operacao=operacao_lc)
            for divisao in divisao_lc:
                divisao.delete()
            operacao_lc.delete()
            return HttpResponseRedirect(reverse('historico_lc'))
 
    else:
        form_operacao_lc = OperacaoLetraCreditoForm(instance=operacao_lc)
        formset_divisao = DivisaoFormSet(instance=operacao_lc)
            
    return render_to_response('lc/editar_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao},
                              context_instance=RequestContext(request))  

    
@login_required
def historico(request):
    operacoes = OperacaoLetraCredito.objects.exclude(data__isnull=True).order_by('data') 
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.all() 
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        try:
            operacao.taxa = historico_porcentagem.filter(data__lte=operacao.data, letra_credito=operacao.letra_credito)[0].porcentagem_di
        except:
            operacao.taxa = historico_porcentagem.get(data__isnull=True, letra_credito=operacao.letra_credito).porcentagem_di
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
        else:
            operacao.tipo = 'Venda'
    
    # Pegar data inicial
    data_inicial = operacoes[0].data
    
    # Pegar data final
    data_final = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    total_gasto = 0
    total_patrimonio = 0
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    graf_gasto_total = list()
    graf_patrimonio = list()
    
    while data_iteracao <= data_final:
        # Processar operações
        operacoes_do_dia = operacoes.filter(data=data_iteracao)
        for operacao in operacoes_do_dia:          
            # Verificar se se trata de compra ou venda
            if operacao.tipo_operacao == 'C':
                operacao.total = operacao.quantidade
                total_gasto += operacao.total
                    
            elif operacao.tipo_operacao == 'V':
                operacao.total = operacao.quantidade
                total_gasto -= operacao.total
                
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
    # Preparar formsets 
    PorcentagemFormSet = inlineformset_factory(LetraCredito, HistoricoPorcentagemLetraCredito, fields=('porcentagem_di',),
                                            extra=1, can_delete=False, max_num=1, validate_max=True)
    CarenciaFormSet = inlineformset_factory(LetraCredito, HistoricoCarenciaLetraCredito, fields=('carencia',),
                                            extra=1, can_delete=False, max_num=1, validate_max=True)
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_lc = LetraCreditoForm(request.POST)
            if form_lc.is_valid():
                lc = form_lc.save(commit=False)
                formset_porcentagem = PorcentagemFormSet(request.POST, instance=lc)
                formset_porcentagem.forms[0].empty_permitted=False
                formset_carencia = CarenciaFormSet(request.POST, instance=lc)
                formset_carencia.forms[0].empty_permitted=False
                
                if formset_porcentagem.is_valid():
                    if formset_carencia.is_valid():
                        try:
                            lc.save()
                            formset_porcentagem.save()
                            formset_carencia.save()
                        # Capturar erros oriundos da hora de salvar os objetos
                        except Exception as erro:
                            messages.error(request, erro.message)
                            return render_to_response('lc/inserir_lc.html', {'form_lc': form_lc, 'formset_porcentagem': formset_porcentagem,
                                                                         'formset_carencia': formset_carencia}, context_instance=RequestContext(request))
                        return HttpResponseRedirect(reverse('listar_lc'))
            for erros in form_lc.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_porcentagem.non_form_errors():
                messages.error(request, erro)
            for erro in formset_carencia.non_form_errors():
                messages.error(request, erro)
            return render_to_response('lc/inserir_lc.html', {'form_lc': form_lc, 'formset_porcentagem': formset_porcentagem,
                                                                      'formset_carencia': formset_carencia}, context_instance=RequestContext(request))
    else:
        form_lc = LetraCreditoForm()
        formset_porcentagem = PorcentagemFormSet()
        formset_carencia = CarenciaFormSet()
    return render_to_response('lc/inserir_lc.html', {'form_lc': form_lc, 'formset_porcentagem': formset_porcentagem,
                                                              'formset_carencia': formset_carencia}, context_instance=RequestContext(request))

@login_required
def inserir_operacao_lc(request):
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoLetraCredito, DivisaoOperacaoLC, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoLCFormSet)
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_lc = OperacaoLetraCreditoForm(request.POST)
            
            if form_operacao_lc.is_valid():
                operacao_lc = form_operacao_lc.save(commit=False)
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc)
                if formset_divisao.is_valid():
                    operacao_lc.save()
                    formset_divisao.save()
                    return HttpResponseRedirect(reverse('historico_lc'))
            for erro in formset_divisao.non_form_errors():
                messages.error(request, erro)
            return render_to_response('lc/inserir_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao},
                                      context_instance=RequestContext(request))
#                         print '%s %s'  % (divisao_lc.quantidade, divisao_lc.divisao)
                
    else:
        form_operacao_lc = OperacaoLetraCreditoForm()
        formset_divisao = DivisaoFormSet()
    return render_to_response('lc/inserir_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao},
                              context_instance=RequestContext(request))

@login_required
def listar_lc(request):
    lcs = LetraCredito.objects.all()
    
    for lc in lcs:
        # Preparar o valor mais atual para carência
        historico_carencia = HistoricoCarenciaLetraCredito.objects.filter(letra_credito=lc).exclude(data=None).order_by('-data')
        if historico_carencia:
            lc.carencia_atual = historico_carencia[0].carencia
        else:
            lc.carencia_atual = HistoricoCarenciaLetraCredito.objects.get(letra_credito=lc).carencia
        # Preparar o valor mais atual de rendimento
        historico_rendimento = HistoricoPorcentagemLetraCredito.objects.filter(letra_credito=lc).exclude(data=None).order_by('-data')
        print historico_rendimento
        if historico_rendimento:
            lc.rendimento_atual = historico_rendimento[0].porcentagem_di
        else:
            lc.rendimento_atual = HistoricoPorcentagemLetraCredito.objects.get(letra_credito=lc).porcentagem_di

    return render_to_response('lc/listar_lc.html', {'lcs': lcs},
                              context_instance=RequestContext(request))

@login_required
def modificar_carencia_lc(request):
    if request.method == 'POST':
        form = HistoricoCarenciaLetraCreditoForm(request.POST)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de carência para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('historico_lc'))
    else:
        form = HistoricoCarenciaLetraCreditoForm()
            
    return render_to_response('lc/modificar_carencia_lc.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def modificar_porcentagem_di_lc(request):
    if request.method == 'POST':
        form = HistoricoPorcentagemLetraCreditoForm(request.POST)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de porcentagem de rendimento para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('historico_lc'))
    else:
        form = HistoricoPorcentagemLetraCreditoForm()
            
    return render_to_response('lc/modificar_porcentagem_di_lc.html', {'form': form}, context_instance=RequestContext(request))