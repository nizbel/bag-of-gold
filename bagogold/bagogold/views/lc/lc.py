# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.divisoes import DivisaoOperacaoLCFormSet
from bagogold.bagogold.forms.lc import OperacaoLetraCreditoForm, \
    HistoricoPorcentagemLetraCreditoForm, LetraCreditoForm, \
    HistoricoCarenciaLetraCreditoForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLC
from bagogold.bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito, LetraCredito, HistoricoCarenciaLetraCredito, \
    OperacaoVendaLetraCredito
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa
from decimal import Decimal
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
            operacao_compra = form_operacao_lc.cleaned_data['operacao_compra']
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc, operacao_compra=operacao_compra)
            
            if form_operacao_lc.is_valid():
                if formset_divisao.is_valid():
                    operacao_lc.save()
                    formset_divisao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('historico_lc'))
            for erros in form_operacao_lc.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_divisao.non_form_errors():
                messages.error(request, erro)
            return render_to_response('lc/editar_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao },
                      context_instance=RequestContext(request))
#                         print '%s %s'  % (divisao_lc.quantidade, divisao_lc.divisao)
                
        elif request.POST.get("delete"):
            divisao_lc = DivisaoOperacaoLC.objects.filter(operacao=operacao_lc)
            for divisao in divisao_lc:
                divisao.delete()
            if operacao_lc.tipo_operacao == 'V':
                OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao_lc).delete()
            operacao_lc.delete()
            messages.success(request, 'Operação excluída com sucesso')
            return HttpResponseRedirect(reverse('historico_lc'))
 
    else:
        form_operacao_lc = OperacaoLetraCreditoForm(instance=operacao_lc, initial={'operacao_compra': operacao_lc.operacao_compra_relacionada(),})
        formset_divisao = DivisaoFormSet(instance=operacao_lc)
            
    return render_to_response('lc/editar_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao},
                              context_instance=RequestContext(request))  

    
@login_required
def historico(request):
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoLetraCredito.objects.exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.all() 
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
            operacao.taxa = operacao.porcentagem_di()
        else:
            operacao.tipo = 'Venda'
    
    # Pegar data inicial
    data_inicial = operacoes.order_by('data')[0].data
    
    # Pegar data final
    data_final = max(HistoricoTaxaDI.objects.filter().order_by('-data')[0].data, datetime.date.today())
    
    data_iteracao = data_inicial
    
    total_gasto = 0
    total_patrimonio = 0
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    graf_gasto_total = list()
    graf_patrimonio = list()

    while data_iteracao <= data_final:
        try:
            taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
        except:
            taxa_do_dia = 0
            
        # Calcular o valor atualizado do patrimonio diariamente
        total_patrimonio = 0
        
        # Processar operações
        for operacao in operacoes:     
            if (operacao.data <= data_iteracao):     
                # Verificar se se trata de compra ou venda
                if operacao.tipo_operacao == 'C':
                        if (operacao.data == data_iteracao):
                            operacao.total = operacao.quantidade
                            total_gasto += operacao.total
                        if taxa_do_dia > 0:
                            # Calcular o valor atualizado para cada operacao
                            operacao.atual = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa)
                            # Arredondar na última iteração
                            if (data_iteracao == data_final):
                                str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                                operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                        total_patrimonio += operacao.atual
                        
                elif operacao.tipo_operacao == 'V':
                    if (operacao.data == data_iteracao):
                        operacao.total = operacao.quantidade
                        total_gasto -= operacao.total
                        # Remover quantidade da operação de compra
                        operacao_compra_id = operacao.operacao_compra_relacionada().id
                        for operacao_c in operacoes:
                            if (operacao_c.id == operacao_compra_id):
                                # Configurar taxa para a mesma quantidade da compra
                                operacao.taxa = operacao_c.taxa
                                operacao.atual = (operacao.quantidade/operacao_c.quantidade) * operacao_c.atual
                                operacao_c.atual -= operacao.atual
                                str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                                operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                                break
                
        if len(operacoes.filter(data=data_iteracao)) > 0 or data_iteracao == data_final:
            graf_gasto_total += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_gasto)]]
            graf_patrimonio += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_patrimonio)]]
        
        # Proximo dia útil
        proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
        if len(proximas_datas) > 0:
            data_iteracao = proximas_datas[0].data
        elif data_iteracao < data_final:
            data_iteracao = data_final
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
            formset_divisao = DivisaoFormSet(request.POST)
            
            if form_operacao_lc.is_valid():
                operacao_lc = form_operacao_lc.save(commit=False)
                operacao_compra = form_operacao_lc.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc, operacao_compra=operacao_compra)
                    
                # TODO Validar em caso de venda
                if form_operacao_lc.cleaned_data['tipo_operacao'] == 'V':
                    operacao_compra = form_operacao_lc.cleaned_data['operacao_compra']
                    # Caso de venda total da letra de crédito
                    if form_operacao_lc.cleaned_data['quantidade'] == operacao_compra.quantidade:
                        # Desconsiderar divisões inseridas, copiar da operação de compra
                        operacao_lc.save()
                        for divisao_lc in DivisaoOperacaoLC.objects.filter(operacao=operacao_compra):
                            divisao_lc_venda = DivisaoOperacaoLC(quantidade=divisao_lc.quantidade, divisao=divisao_lc.divisao, \
                                                                 operacao=operacao_lc)
                            divisao_lc_venda.save()
                        operacao_venda_lc = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                        operacao_venda_lc.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('historico_lc'))
                    # Vendas parciais
                    else:
                        if formset_divisao.is_valid():
                            operacao_lc.save()
                            formset_divisao.save()
                            operacao_venda_lc = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                            operacao_venda_lc.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('historico_lc'))
                else:
                    if formset_divisao.is_valid():
                        operacao_lc.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('historico_lc'))
                        
            for erros in form_operacao_lc.errors.values():
                for erro in erros:
                    messages.error(request, erro)
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
#         print historico_rendimento
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

@login_required
def painel(request):
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoLetraCredito.objects.exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.all() 
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
            operacao.taxa = operacao.porcentagem_di()
        else:
            operacao.tipo = 'Venda'
    
    # Pegar data inicial
    data_inicial = operacoes.order_by('data')[0].data
    
    # Pegar data final
    data_final = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    total_atual = 0
    
    while data_iteracao <= data_final:
        taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
        
        # Processar operações
        for operacao in operacoes:     
            if (operacao.data <= data_iteracao):     
                # Verificar se se trata de compra ou venda
                if operacao.tipo_operacao == 'C':
                        if (operacao.data == data_iteracao):
                            operacao.total = operacao.quantidade
                        # Calcular o valor atualizado para cada operacao
                        operacao.atual = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa)
                        # Arredondar na última iteração
                        if (data_iteracao == data_final):
                            str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                            operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                            total_atual += operacao.atual
                        
                elif operacao.tipo_operacao == 'V':
                    if (operacao.data == data_iteracao):
                        operacao.total = operacao.quantidade
                        # Remover quantidade da operação de compra
                        operacao_compra_id = operacao.operacao_compra_relacionada().id
                        for operacao_c in operacoes:
                            if (operacao_c.id == operacao_compra_id):
                                # Configurar taxa para a mesma quantidade da compra
                                operacao.taxa = operacao_c.taxa
                                operacao.atual = (operacao.quantidade/operacao_c.quantidade) * operacao_c.atual
                                operacao_c.atual -= operacao.atual
                                str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                                operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                                break
                
        # Proximo dia útil
        proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
        if len(proximas_datas) > 0:
            data_iteracao = proximas_datas[0].data
        else:
            break
    
    # Remover operações que não estejam mais rendendo
    operacoes = [operacao for operacao in operacoes if (operacao.atual > 0 and operacao.tipo_operacao == 'C')]
    
    total_ganho_prox_dia = 0
    # Calcular o ganho no dia seguinte, considerando taxa do dia anterior
    for operacao in operacoes:
        operacao.ganho_prox_dia = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa) - operacao.atual
        str_auxiliar = str(operacao.ganho_prox_dia.quantize(Decimal('.0001')))
        operacao.ganho_prox_dia = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        total_ganho_prox_dia += operacao.ganho_prox_dia
    
    # Popular dados
    dados = {}
    dados['total_atual'] = total_atual
    dados['total_ganho_prox_dia'] = total_ganho_prox_dia
    
    return render_to_response('lc/painel.html', {'operacoes': operacoes, 'dados': dados},
                               context_instance=RequestContext(request))