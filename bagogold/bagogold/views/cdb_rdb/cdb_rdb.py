# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.cdb_rdb import HistoricoPorcentagemForm, \
    HistoricoCarenciaForm, CDB_RDBForm
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoLCFormSet, \
    DivisaoOperacaoCDBFormSet, DivisaoOperacaoRDBFormSet
from bagogold.bagogold.forms.lc import OperacaoLetraCreditoForm, \
    HistoricoPorcentagemLetraCreditoForm, LetraCreditoForm, \
    HistoricoCarenciaLetraCreditoForm
from bagogold.bagogold.models.cdb_rdb import HistoricoPorcentagemCDB_RDB, \
    HistoricoCarenciaCDB_RDB
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLC, \
    DivisaoOperacaoCDB, DivisaoOperacaoRDB
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
from itertools import chain
import calendar
import datetime

TIPO_CDB = '1'
TIPO_RDB = '2'

@login_required
def editar_operacao_cdb_rdb(request, id):
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoLetraCredito, DivisaoOperacaoLC, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoLCFormSet)
    operacao_cdb_rdb = OperacaoLetraCredito.objects.get(pk=id)
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_cdb_rdb = OperacaoLetraCreditoForm(request.POST, instance=operacao_cdb_rdb)
            operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_cdb_rdb, operacao_compra=operacao_compra)
            
            if form_operacao_cdb_rdb.is_valid():
                if formset_divisao.is_valid():
                    operacao_cdb_rdb.save()
                    formset_divisao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('historico_cdb_rdb'))
            for erros in form_operacao_cdb_rdb.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_divisao.non_form_errors():
                messages.error(request, erro)
            return render_to_response('cdb_rdb/editar_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao': formset_divisao },
                      context_instance=RequestContext(request))
#                         print '%s %s'  % (divisao_cdb_rdb.quantidade, divisao_cdb_rdb.divisao)
                
        elif request.POST.get("delete"):
            divisao_cdb_rdb = DivisaoOperacaoLC.objects.filter(operacao=operacao_cdb_rdb)
            for divisao in divisao_cdb_rdb:
                divisao.delete()
            if operacao_cdb_rdb.tipo_operacao == 'V':
                OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao_cdb_rdb).delete()
            operacao_cdb_rdb.delete()
            messages.success(request, 'Operação excluída com sucesso')
            return HttpResponseRedirect(reverse('historico_cdb_rdb'))
 
    else:
        form_operacao_cdb_rdb = OperacaoLetraCreditoForm(instance=operacao_cdb_rdb, initial={'operacao_compra': operacao_cdb_rdb.operacao_compra_relacionada(),})
        formset_divisao = DivisaoFormSet(instance=operacao_cdb_rdb)
            
    return render_to_response('cdb_rdb/editar_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao': formset_divisao},
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
    
    return render_to_response('cdb_rdb/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio},
                               context_instance=RequestContext(request))
    

@login_required
def inserir_cdb_rdb(request):
    if request.method == 'POST':
        form_cdb_rdb = CDB_RDBForm(request.POST)
        form_historico_porcentagem = HistoricoPorcentagemForm(request.POST)
        form_historico_carencia = HistoricoCarenciaForm(request.POST)
        if form_cdb_rdb.is_valid():
            investimento = form_cdb_rdb.save(commit=False)
            if form_historico_porcentagem.is_valid():
                if form_historico_carencia.is_valid():
                    try:
                        historico_porcentagem = HistoricoPorcentagemCDB_RDB(cdb=investimento, porcentagem=form_historico_porcentagem.cleaned_data['porcentagem'])
                        historico_carencia = HistoricoCarenciaCDB_RDB(cdb=investimento, carencia=form_historico_carencia.cleaned_data['carencia'])
                        investimento.save()
                        historico_porcentagem.save()
                        historico_carencia.save()
                        
                    # Capturar erros oriundos da hora de salvar os objetos
                    except Exception as erro:
                        messages.error(request, erro.message)
                        return render_to_response('cdb_rdb/inserir_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'form_historico_porcentagem': form_historico_porcentagem,
                                                           'form_historico_carencia': form_historico_carencia}, context_instance=RequestContext(request))
                    return HttpResponseRedirect(reverse('listar_cdb_rdb'))
        for erros in form_cdb_rdb.errors.values():
            for erro in erros:
                messages.error(request, erro)
        return render_to_response('cdb_rdb/inserir_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'form_historico_porcentagem': form_historico_porcentagem,
                                                               'form_historico_carencia': form_historico_carencia}, context_instance=RequestContext(request))
    else:
        form_cdb_rdb = CDB_RDBForm()
        form_historico_porcentagem = HistoricoPorcentagemForm()
        form_historico_carencia = HistoricoCarenciaForm()
    return render_to_response('cdb_rdb/inserir_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'form_historico_porcentagem': form_historico_porcentagem,
                                                               'form_historico_carencia': form_historico_carencia}, context_instance=RequestContext(request))

@login_required
def inserir_operacao_cdb_rdb(request):
    # Preparar formset para divisoes
    DivisaoCDB_RDBFormSet = inlineformset_factory(OperacaoCDB_RDB, DivisaoOperacaoCDB_RDB, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoCDB_RDBFormSet)
    
    if request.method == 'POST':
        form_operacao_cdb = OperacaoCDBForm(request.POST)
        formset_divisao_cdb = DivisaoCDBFormSet(request.POST)
        form_operacao_rdb = OperacaoCDBForm(request.POST)
        formset_divisao_rdb = DivisaoCDBFormSet(request.POST)
        
        # Validar CDB
        if request.POST.get("save") == 'cdb':
            if form_operacao_cdb.is_valid():
                operacao_cdb = form_operacao_cdb.save(commit=False)
                operacao_compra = form_operacao_cdb.cleaned_data['operacao_compra']
                formset_divisao_cdb = DivisaoCDBFormSet(request.POST, instance=operacao_cdb, operacao_compra=operacao_compra)
                    
                # TODO Validar em caso de venda
                if form_operacao_cdb.cleaned_data['tipo_operacao'] == 'V':
                    operacao_compra = form_operacao_cdb.cleaned_data['operacao_compra']
                    # Caso de venda total da letra de crédito
                    if form_operacao_cdb.cleaned_data['quantidade'] == operacao_compra.quantidade:
                        # Desconsiderar divisões inseridas, copiar da operação de compra
                        operacao_cdb.save()
                        for divisao_cdb_rdb in DivisaoOperacaoCDB.objects.filter(operacao=operacao_compra):
                            divisao_cdb_rdb_venda = DivisaoOperacaoLC(quantidade=divisao_cdb_rdb.quantidade, divisao=divisao_cdb_rdb.divisao, \
                                                                 operacao=operacao_cdb)
                            divisao_cdb_rdb_venda.save()
                        operacao_venda_cdb_rdb = OperacaoVendaCDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb)
                        operacao_venda_cdb_rdb.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('historico_cdb_rdb'))
                    # Vendas parciais
                    else:
                        if formset_divisao_cdb.is_valid():
                            operacao_cdb.save()
                            formset_divisao_cdb.save()
                            operacao_venda_cdb_rdb = OperacaoVendaCDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb)
                            operacao_venda_cdb_rdb.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('historico_cdb_rdb'))
                else:
                    if formset_divisao_cdb.is_valid():
                        operacao_cdb.save()
                        formset_divisao_cdb.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('historico_cdb_rdb'))
                        
            for erros in form_operacao_cdb.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_divisao_cdb.non_form_errors():
                messages.error(request, erro)
        # Validar RDB
        if request.POST.get("save") == 'rdb':
            if form_operacao_rdb.is_valid():
                operacao_rdb = form_operacao_rdb.save(commit=False)
                operacao_compra = form_operacao_rdb.cleaned_data['operacao_compra']
                formset_divisao_rdb = DivisaoRDBFormSet(request.POST, instance=operacao_rdb, operacao_compra=operacao_compra)
                    
                # TODO Validar em caso de venda
                if form_operacao_rdb.cleaned_data['tipo_operacao'] == 'V':
                    operacao_compra = form_operacao_rdb.cleaned_data['operacao_compra']
                    # Caso de venda total da letra de crédito
                    if form_operacao_rdb.cleaned_data['quantidade'] == operacao_compra.quantidade:
                        # Desconsiderar divisões inseridas, copiar da operação de compra
                        operacao_rdb.save()
                        for divisao_rdb_rdb in DivisaoOperacaoRDB.objects.filter(operacao=operacao_compra):
                            divisao_rdb_rdb_venda = DivisaoOperacaoRDB(quantidade=divisao_rdb_rdb.quantidade, divisao=divisao_rdb_rdb.divisao, \
                                                                 operacao=operacao_rdb)
                            divisao_rdb_rdb_venda.save()
                        operacao_venda_rdb_rdb = OperacaoVendaRDB(operacao_compra=operacao_compra, operacao_venda=operacao_rdb)
                        operacao_venda_rdb_rdb.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('historico_rdb_rdb'))
                    # Vendas parciais
                    else:
                        if formset_divisao_rdb.is_valid():
                            operacao_rdb.save()
                            formset_divisao_rdb.save()
                            operacao_venda_rdb_rdb = OperacaoVendaRDB(operacao_compra=operacao_compra, operacao_venda=operacao_rdb)
                            operacao_venda_rdb_rdb.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('historico_rdb_rdb'))
                else:
                    if formset_divisao_rdb.is_valid():
                        operacao_rdb.save()
                        formset_divisao_rdb.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('historico_rdb_rdb'))
                        
            for erros in form_operacao_rdb.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_divisao_rdb.non_form_errors():
                messages.error(request, erro)
                
        return render_to_response('cdb_rdb/inserir_operacao_cdb_rdb.html', {'form_operacao_cdb': form_operacao_cdb, 'form_operacao_rdb': form_operacao_rdb, 
                                                                            'formset_divisao_cdb': formset_divisao_cdb, 'formset_divisao_rdb': formset_divisao_rdb},
                                  context_instance=RequestContext(request))
#                         print '%s %s'  % (divisao_cdb_rdb.quantidade, divisao_cdb_rdb.divisao)
                
    else:
        form_operacao_cdb = OperacaoCDBForm()
        form_operacao_rdb = OperacaoRDBForm()
        formset_divisao_cdb = DivisaoCDBFormSet()
        formset_divisao_rdb = DivisaoRDBFormSet()
    return render_to_response('cdb_rdb/inserir_operacao_cdb_rdb.html', {'form_operacao_cdb': form_operacao_cdb, 'form_operacao_rdb': form_operacao_rdb, 
                                                                        'formset_divisao_cdb': formset_divisao_cdb, 'formset_divisao_rdb': formset_divisao_rdb}, context_instance=RequestContext(request))

@login_required
def listar_cdb_rdb(request):
    cdb = CDB.objects.all()
    for item in cdb:
        item.tipo = 'CDB'
    rdb = RDB.objects.all()
    for item in rdb:
        item.tipo = 'RDB'
    cdb_rdb = list(chain(cdb, rdb))
    
    for investimento in cdb_rdb:
        # Preparar o valor mais atual para carência
        investimento.carencia_atual = investimento.carencia_atual()
        # Preparar o valor mais atual de rendimento
        investimento.rendimento_atual = investimento.porcentagem_atual()
        
        if investimento.tipo_rendimento == 1:
            investimento.str_tipo_rendimento = 'Pré-fixado'
        elif investimento.tipo_rendimento == 2:
            investimento.str_tipo_rendimento = 'Pós-fixado'
        
    return render_to_response('cdb_rdb/listar_cdb_rdb.html', {'cdb_rdb': cdb_rdb},
                              context_instance=RequestContext(request))

@login_required
def modificar_carencia_cdb_rdb(request):
    if request.method == 'POST':
        form = HistoricoCarenciaLetraCreditoForm(request.POST)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de carência para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('historico_cdb_rdb'))
    else:
        form = HistoricoCarenciaLetraCreditoForm()
            
    return render_to_response('cdb_rdb/modificar_carencia_cdb_rdb.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def modificar_porcentagem_di_cdb_rdb(request):
    if request.method == 'POST':
        form = HistoricoPorcentagemLetraCreditoForm(request.POST)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de porcentagem de rendimento para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('historico_cdb_rdb'))
    else:
        form = HistoricoPorcentagemLetraCreditoForm()
            
    return render_to_response('cdb_rdb/modificar_porcentagem_di_cdb_rdb.html', {'form': form}, context_instance=RequestContext(request))

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
    
    return render_to_response('cdb_rdb/painel.html', {'operacoes': operacoes, 'dados': dados},
                               context_instance=RequestContext(request))