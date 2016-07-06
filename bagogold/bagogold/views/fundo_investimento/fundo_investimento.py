# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.divisoes import \
    DivisaoOperacaoFundoInvestimentoFormSet
from bagogold.bagogold.forms.fundo_investimento import \
    OperacaoFundoInvestimentoForm, FundoInvestimentoForm, \
    HistoricoCarenciaFundoInvestimentoForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLC, \
    DivisaoOperacaoFundoInvestimento
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento, FundoInvestimento, HistoricoCarenciaFundoInvestimento
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
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
def adicionar_valor_cota_historico(request):
    pass

@login_required
def editar_operacao_fundo_investimento(request, id):
    investidor = request.user.investidor
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoFundoInvestimento, DivisaoOperacaoFundoInvestimento, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoFundoInvestimentoFormSet)
    operacao_fundo_investimento = OperacaoFundoInvestimento.objects.get(pk=id)
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(request.POST, instance=operacao_fundo_investimento, investidor=investidor)
            
            if form_operacao_fundo_investimento.is_valid():
                operacao_compra = form_operacao_fundo_investimento.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_fundo_investimento, operacao_compra=operacao_compra, investidor=investidor)
                if formset_divisao.is_valid():
                    operacao_fundo_investimento.save()
                    formset_divisao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('historico_fundo_investimento'))
            for erros in form_operacao_fundo_investimento.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_divisao.non_form_errors():
                messages.error(request, erro)
            return render_to_response('fundo_investimento/editar_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, 'formset_divisao': formset_divisao },
                      context_instance=RequestContext(request))
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
        elif request.POST.get("delete"):
            divisao_fundo_investimento = DivisaoOperacaoLC.objects.filter(operacao=operacao_fundo_investimento)
            for divisao in divisao_fundo_investimento:
                divisao.delete()
            if operacao_fundo_investimento.tipo_operacao == 'V':
                OperacaoVendaFundoInvestimento.objects.get(operacao_venda=operacao_fundo_investimento).delete()
            operacao_fundo_investimento.delete()
            messages.success(request, 'Operação excluída com sucesso')
            return HttpResponseRedirect(reverse('historico_fundo_investimento'))
 
    else:
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(instance=operacao_fundo_investimento, initial={'operacao_compra': operacao_fundo_investimento.operacao_compra_relacionada(),}, \
                                                    investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=operacao_fundo_investimento, investidor=investidor)
            
    return render_to_response('fundo_investimento/editar_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, 'formset_divisao': formset_divisao},
                              context_instance=RequestContext(request))  

    
@login_required
def historico(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
            operacao.taxa = operacao.porcentagem()
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
            
        # Cafundo_investimentoular o valor atualizado do patrimonio diariamente
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
                            # Cafundo_investimentoular o valor atualizado para cada operacao
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
    
    return render_to_response('fundo_investimento/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio},
                               context_instance=RequestContext(request))
    

@login_required
def inserir_fundo_investimento(request):
    investidor = request.user.investidor
    # Preparar formsets 
    CarenciaFormSet = inlineformset_factory(FundoInvestimento, HistoricoCarenciaFundoInvestimento, fields=('carencia',),
                                            extra=1, can_delete=False, max_num=1, validate_max=True, labels = {'carencia': 'Período de carência (em dias)',})
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_fundo_investimento = FundoInvestimentoForm(request.POST)
            formset_carencia = CarenciaFormSet(request.POST)
            if form_fundo_investimento.is_valid():
                fundo_investimento = form_fundo_investimento.save(commit=False)
                fundo_investimento.investidor = request.user.investidor
                formset_carencia = CarenciaFormSet(request.POST, instance=fundo_investimento)
                formset_carencia.forms[0].empty_permitted=False
                
                if formset_carencia.is_valid():
                    try:
                        fundo_investimento.save()
                        formset_carencia.save()
                    # Capturar erros oriundos da hora de salvar os objetos
                    except Exception as erro:
                        messages.error(request, erro.message)
                        return render_to_response('fundo_investimento/inserir_fundo_investimento.html', {'form_fundo_investimento': form_fundo_investimento,
                                                          'formset_carencia': formset_carencia}, context_instance=RequestContext(request))
                            
                    return HttpResponseRedirect(reverse('listar_fundo_investimento'))
            for erros in form_fundo_investimento.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_carencia.non_form_errors():
                messages.error(request, erro)
            return render_to_response('fundo_investimento/inserir_fundo_investimento.html', {'form_fundo_investimento': form_fundo_investimento,
                                                              'formset_carencia': formset_carencia}, context_instance=RequestContext(request))
    else:
        form_fundo_investimento = FundoInvestimentoForm()
        formset_carencia = CarenciaFormSet()
    return render_to_response('fundo_investimento/inserir_fundo_investimento.html', {'form_fundo_investimento': form_fundo_investimento,
                                                              'formset_carencia': formset_carencia}, context_instance=RequestContext(request))

@login_required
def inserir_operacao_fundo_investimento(request):
    investidor = request.user.investidor
    # Preparar formset para divisoes
    DivisaoFundoInvestimentoFormSet = inlineformset_factory(OperacaoFundoInvestimento, DivisaoOperacaoFundoInvestimento, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoFundoInvestimentoFormSet)
    
    if request.method == 'POST':
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(request.POST, investidor=investidor)
        formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(request.POST, investidor=investidor)
        
        # Validar CDB
        if form_operacao_fundo_investimento.is_valid():
            operacao_fundo_investimento = form_operacao_fundo_investimento.save(commit=False)
            operacao_fundo_investimento.investidor = investidor
            formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(request.POST, instance=operacao_fundo_investimento, investidor=investidor)
            if formset_divisao_fundo_investimento.is_valid():
                operacao_fundo_investimento.save()
                formset_divisao_fundo_investimento.save()
                messages.success(request, 'Operação inserida com sucesso')
                return HttpResponseRedirect(reverse('historico_fundo_investimento'))
                    
        for erros in form_operacao_fundo_investimento.errors.values():
            for erro in erros:
                messages.error(request, erro)
        for erro in formset_divisao_fundo_investimento.non_form_errors():
            messages.error(request, erro)
                        
        return render_to_response('fundo_investimento/inserir_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, 'formset_divisao_fundo_investimento': formset_divisao_fundo_investimento},
                                  context_instance=RequestContext(request))
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(investidor=investidor)
        formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(investidor=investidor)
    return render_to_response('fundo_investimento/inserir_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, 'formset_divisao_fundo_investimento': formset_divisao_fundo_investimento}, context_instance=RequestContext(request))

@login_required
def listar_fundo_investimento(request):
    investidor = request.user.investidor
    fundo_investimento = FundoInvestimento.objects.filter(investidor=investidor)
    
    for investimento in fundo_investimento:
        # Preparar o valor mais atual para carência
        investimento.carencia_atual = investimento.carencia_atual()
        # Preparar o valor mais atual de rendimento
        investimento.rendimento_atual = investimento.porcentagem_atual()
        
        if investimento.tipo_rendimento == 1:
            investimento.str_tipo_rendimento = 'Pré-fixado'
        elif investimento.tipo_rendimento == 2:
            investimento.str_tipo_rendimento = 'Pós-fixado'
        
    return render_to_response('fundo_investimento/listar_fundo_investimento.html', {'fundo_investimento': fundo_investimento},
                              context_instance=RequestContext(request))

@login_required
def modificar_carencia_fundo_investimento(request):
    if request.method == 'POST':
        form = HistoricoCarenciaFundoInvestimentoForm(request.POST)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de carência para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('historico_fundo_investimento'))
    else:
        form = HistoricoCarenciaFundoInvestimentoForm()
            
    return render_to_response('fundo_investimento/modificar_carencia_fundo_investimento.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def modificar_porcentagem_fundo_investimento(request):
    if request.method == 'POST':
        form = HistoricoPorcentagemFundoInvestimentoForm(request.POST)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de porcentagem de rendimento para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('historico_fundo_investimento'))
    else:
        form = HistoricoPorcentagemFundoInvestimentoForm()
            
    return render_to_response('fundo_investimento/modificar_porcentagem_fundo_investimento.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def painel(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    historico_porcentagem = HistoricoPorcentagemFundoInvestimento.objects.all() 
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
            operacao.taxa = operacao.porcentagem()
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
                            operacao.inicial = operacao.quantidade
                        # Cafundo_investimentoular o valor atualizado para cada operacao
                        operacao.atual = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa)
                        # Arredondar na última iteração
                        if (data_iteracao == data_final):
                            str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                            operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                            total_atual += operacao.atual
                        
                elif operacao.tipo_operacao == 'V':
                    if (operacao.data == data_iteracao):
                        operacao.inicial = operacao.quantidade
                        # Remover quantidade da operação de compra
                        operacao_compra_id = operacao.operacao_compra_relacionada().id
                        for operacao_c in operacoes:
                            if (operacao_c.id == operacao_compra_id):
                                # Configurar taxa para a mesma quantidade da compra
                                operacao.taxa = operacao_c.taxa
                                operacao.atual = (operacao.quantidade/operacao_c.quantidade) * operacao_c.atual
                                operacao_c.atual -= operacao.atual
                                operacao_c.inicial -= operacao.inicial
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
    
    total_ir = 0
    total_iof = 0
    total_ganho_prox_dia = 0
    for operacao in operacoes:
        # Calcular o ganho no dia seguinte, considerando taxa do dia anterior
        operacao.ganho_prox_dia = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa) - operacao.atual
        str_auxiliar = str(operacao.ganho_prox_dia.quantize(Decimal('.0001')))
        operacao.ganho_prox_dia = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        total_ganho_prox_dia += operacao.ganho_prox_dia
        
        # Calcular impostos
        qtd_dias = (datetime.date.today() - operacao.data).days
        print qtd_dias, calcular_iof_regressivo(qtd_dias)
        # IOF
        operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.inicial)
        # IR
        if qtd_dias <= 180:
            operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.inicial - operacao.iof)
        elif qtd_dias <= 360:
            operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.inicial - operacao.iof)
        elif qtd_dias <= 720:
            operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.inicial - operacao.iof)
        else: 
            operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.inicial - operacao.iof)
        total_ir += operacao.imposto_renda
        total_iof += operacao.iof
    
    # Popular dados
    dados = {}
    dados['total_atual'] = total_atual
    dados['total_ir'] = total_ir
    dados['total_iof'] = total_iof
    dados['total_ganho_prox_dia'] = total_ganho_prox_dia
    
    return render_to_response('fundo_investimento/painel.html', {'operacoes': operacoes, 'dados': dados},
                               context_instance=RequestContext(request))