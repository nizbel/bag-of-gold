# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.cdb_rdb import OperacaoCDB_RDBForm, \
    HistoricoPorcentagemCDB_RDBForm, CDB_RDBForm, HistoricoCarenciaCDB_RDBForm
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoCDB_RDBFormSet
from bagogold.bagogold.models.cdb_rdb import OperacaoCDB_RDB, \
    HistoricoPorcentagemCDB_RDB, CDB_RDB, HistoricoCarenciaCDB_RDB, \
    OperacaoVendaCDB_RDB
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCDB_RDB
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa, \
    calcular_valor_atualizado_com_taxas
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import calendar
import datetime

TIPO_CDB = '1'
TIPO_RDB = '2'

@login_required
def detalhar_cdb_rdb(request, id):
    investidor = request.user.investidor
    
    cdb_rdb = CDB_RDB.objects.get(id=id)
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    historico_porcentagem = HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=cdb_rdb)
    historico_carencia = HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cdb_rdb)
    
    # Inserir dados do investimento
    if cdb_rdb.tipo == 'R':
        cdb_rdb.tipo = 'RDB'
    elif cdb_rdb.tipo == 'C':
        cdb_rdb.tipo = 'CDB'
    cdb_rdb.carencia_atual = cdb_rdb.carencia_atual()
    cdb_rdb.porcentagem_atual = cdb_rdb.porcentagem_atual()
    
    # Preparar estatísticas zeradas
    cdb_rdb.total_investido = Decimal(0)
    cdb_rdb.saldo_atual = Decimal(0)
    cdb_rdb.total_ir = Decimal(0)
    cdb_rdb.total_iof = Decimal(0)
    cdb_rdb.lucro = Decimal(0)
    cdb_rdb.lucro_percentual = Decimal(0)
    
    operacoes = OperacaoCDB_RDB.objects.filter(investimento=cdb_rdb).order_by('data')
    # Contar total de operações já realizadas 
    cdb_rdb.total_operacoes = len(operacoes)
    # Remover operacoes totalmente vendidas
    operacoes = [operacao for operacao in operacoes if operacao.qtd_disponivel_venda() > 0]
    if operacoes:
        historico_di = HistoricoTaxaDI.objects.filter(data__range=[operacoes[0].data, datetime.date.today()])
        for operacao in operacoes:
            # Total investido
            cdb_rdb.total_investido += operacao.qtd_disponivel_venda()
            
            # Saldo atual
            taxas = historico_di.filter(data__gte=operacao.data).values('taxa').annotate(qtd_dias=Count('taxa'))
            taxas_dos_dias = {}
            for taxa in taxas:
                taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
            operacao.atual = calcular_valor_atualizado_com_taxas(taxas_dos_dias, operacao.qtd_disponivel_venda(), operacao.porcentagem())
            cdb_rdb.saldo_atual += operacao.atual
            
            # Calcular impostos
            qtd_dias = (datetime.date.today() - operacao.data).days
            # IOF
            operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.quantidade)
            # IR
            if qtd_dias <= 180:
                operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.quantidade - operacao.iof)
            elif qtd_dias <= 360:
                operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.quantidade - operacao.iof)
            elif qtd_dias <= 720:
                operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.quantidade - operacao.iof)
            else: 
                operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.quantidade - operacao.iof)
            cdb_rdb.total_ir += operacao.imposto_renda
            cdb_rdb.total_iof += operacao.iof
    
        # Pegar outras estatísticas
        str_auxiliar = str(cdb_rdb.saldo_atual.quantize(Decimal('.0001')))
        cdb_rdb.saldo_atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        
        cdb_rdb.lucro = cdb_rdb.saldo_atual - cdb_rdb.total_investido
        cdb_rdb.lucro_percentual = cdb_rdb.lucro / cdb_rdb.total_investido * 100
    try: 
        cdb_rdb.dias_proxima_retirada = (min(operacao.data + datetime.timedelta(days=operacao.carencia()) for operacao in operacoes if \
                                             (operacao.data + datetime.timedelta(days=operacao.carencia())) > datetime.date.today()) - datetime.date.today()).days
    except ValueError:
        cdb_rdb.dias_proxima_retirada = 0
    
    
    return render_to_response('cdb_rdb/detalhar_cdb_rdb.html', {'cdb_rdb': cdb_rdb, 'historico_porcentagem': historico_porcentagem,
                                                                       'historico_carencia': historico_carencia},
                              context_instance=RequestContext(request))

@login_required
def editar_cdb_rdb(request, id):
    investidor = request.user.investidor
    cdb_rdb = CDB_RDB.objects.get(pk=id)
    
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_cdb_rdb = CDB_RDBForm(request.POST, instance=cdb_rdb)
            
            if form_cdb_rdb.is_valid():
                cdb_rdb.save()
                messages.success(request, 'CDB/RDB editado com sucesso')
                return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': cdb_rdb.id}))
                
        # TODO verificar o que pode acontecer na exclusão
        elif request.POST.get("delete"):
            cdb_rdb.delete()
            messages.success(request, 'CDB/RDB excluído com sucesso')
            return HttpResponseRedirect(reverse('listar_cdb_rdb'))
 
    else:
        form_cdb_rdb = CDB_RDBForm(instance=cdb_rdb)
            
    return render_to_response('cdb_rdb/editar_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb},
                              context_instance=RequestContext(request))  
    
@login_required
def editar_historico_carencia(request, id):
    investidor = request.user.investidor
    historico_carencia = HistoricoCarenciaCDB_RDB.objects.get(pk=id)
    
    if historico_carencia.cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_carencia.data is None:
                form_historico_carencia = HistoricoCarenciaCDB_RDBForm(request.POST, instance=historico_carencia, cdb_rdb=historico_carencia.cdb_rdb, inicial=True)
            else:
                form_historico_carencia = HistoricoCarenciaCDB_RDBForm(request.POST, instance=historico_carencia, cdb_rdb=historico_carencia.cdb_rdb)
            if form_historico_carencia.is_valid():
                historico_carencia.save()
                messages.success(request, 'Histórico de carência editado com sucesso')
                return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': historico_carencia.cdb_rdb.id}))
                
        elif request.POST.get("delete"):
            if historico_carencia.data is None:
                messages.error(request, 'Valor inicial de carência não pode ser excluído')
                return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': historico_carencia.cdb_rdb.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            cdb_rdb = historico_carencia.cdb_rdb
            historico_carencia.delete()
            messages.success(request, 'Histórico de carência excluído com sucesso')
            return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': cdb_rdb.id}))
 
    else:
        if historico_carencia.data is None:
            form_historico_carencia = HistoricoCarenciaCDB_RDBForm(instance=historico_carencia, cdb_rdb=historico_carencia.cdb_rdb, inicial=True)
        else: 
            form_historico_carencia = HistoricoCarenciaCDB_RDBForm(instance=historico_carencia, cdb_rdb=historico_carencia.cdb_rdb)
            
    return render_to_response('cdb_rdb/editar_historico_carencia.html', {'form_historico_carencia': form_historico_carencia},
                              context_instance=RequestContext(request)) 
    
@login_required
def editar_historico_porcentagem(request, id):
    investidor = request.user.investidor
    historico_porcentagem = HistoricoPorcentagemCDB_RDB.objects.get(pk=id)
    
    if historico_porcentagem.cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_porcentagem.data is None:
                form_historico_porcentagem = HistoricoPorcentagemCDB_RDBForm(request.POST, instance=historico_porcentagem, cdb_rdb=historico_porcentagem.cdb_rdb, inicial=True)
            else:
                form_historico_porcentagem = HistoricoPorcentagemCDB_RDBForm(request.POST, instance=historico_porcentagem, cdb_rdb=historico_porcentagem.cdb_rdb)
            if form_historico_porcentagem.is_valid():
                historico_porcentagem.save(force_update=True)
                messages.success(request, 'Histórico de porcentagem editado com sucesso')
                return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': historico_porcentagem.cdb_rdb.id}))
                
        elif request.POST.get("delete"):
            if historico_porcentagem.data is None:
                messages.error(request, 'Valor inicial de porcentagem não pode ser excluído')
                return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': historico_porcentagem.cdb_rdb.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            cdb_rdb = historico_porcentagem.cdb_rdb
            historico_porcentagem.delete()
            messages.success(request, 'Histórico de porcentagem excluído com sucesso')
            return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': cdb_rdb.id}))
 
    else:
        if historico_porcentagem.data is None:
            form_historico_porcentagem = HistoricoPorcentagemCDB_RDBForm(instance=historico_porcentagem, cdb_rdb=historico_porcentagem.cdb_rdb, inicial=True)
        else: 
            form_historico_porcentagem = HistoricoPorcentagemCDB_RDBForm(instance=historico_porcentagem, cdb_rdb=historico_porcentagem.cdb_rdb)
            
    return render_to_response('cdb_rdb/editar_historico_porcentagem.html', {'form_historico_porcentagem': form_historico_porcentagem},
                              context_instance=RequestContext(request)) 
    
@login_required
def editar_operacao_cdb_rdb(request, id):
    investidor = request.user.investidor
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoCDB_RDB, DivisaoOperacaoCDB_RDB, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoCDB_RDBFormSet)
    operacao_cdb_rdb = OperacaoCDB_RDB.objects.get(pk=id)
    
    if operacao_cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_cdb_rdb = OperacaoCDB_RDBForm(request.POST, instance=operacao_cdb_rdb, investidor=investidor)
            
            if form_operacao_cdb_rdb.is_valid():
                operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_cdb_rdb, operacao_compra=operacao_compra, investidor=investidor)
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
            divisao_cdb_rdb = DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao_cdb_rdb)
            for divisao in divisao_cdb_rdb:
                divisao.delete()
            if operacao_cdb_rdb.tipo_operacao == 'V':
                OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb).delete()
            operacao_cdb_rdb.delete()
            messages.success(request, 'Operação excluída com sucesso')
            return HttpResponseRedirect(reverse('historico_cdb_rdb'))
 
    else:
        form_operacao_cdb_rdb = OperacaoCDB_RDBForm(instance=operacao_cdb_rdb, initial={'operacao_compra': operacao_cdb_rdb.operacao_compra_relacionada(),}, \
                                                    investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=operacao_cdb_rdb, investidor=investidor)
            
    return render_to_response('cdb_rdb/editar_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao': formset_divisao},
                              context_instance=RequestContext(request))  

    
@login_required
def historico(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
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
    investidor = request.user.investidor
    # Preparar formsets 
    PorcentagemFormSet = inlineformset_factory(CDB_RDB, HistoricoPorcentagemCDB_RDB, fields=('porcentagem',),
                                            extra=1, can_delete=False, max_num=1, validate_max=True)
    CarenciaFormSet = inlineformset_factory(CDB_RDB, HistoricoCarenciaCDB_RDB, fields=('carencia',),
                                            extra=1, can_delete=False, max_num=1, validate_max=True, labels = {'carencia': 'Período de carência (em dias)',})
    
    if request.method == 'POST':
        form_cdb_rdb = CDB_RDBForm(request.POST)
        formset_porcentagem = PorcentagemFormSet(request.POST)
        formset_carencia = CarenciaFormSet(request.POST)
        if form_cdb_rdb.is_valid():
            cdb_rdb = form_cdb_rdb.save(commit=False)
            cdb_rdb.investidor = request.user.investidor
            formset_porcentagem = PorcentagemFormSet(request.POST, instance=cdb_rdb)
            formset_porcentagem.forms[0].empty_permitted=False
            formset_carencia = CarenciaFormSet(request.POST, instance=cdb_rdb)
            formset_carencia.forms[0].empty_permitted=False
            
            if formset_porcentagem.is_valid():
                if formset_carencia.is_valid():
                    try:
                        cdb_rdb.save()
                        formset_porcentagem.save()
                        formset_carencia.save()
                    # Capturar erros oriundos da hora de salvar os objetos
                    except Exception as erro:
                        messages.error(request, erro.message)
                        return render_to_response('cdb_rdb/inserir_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'formset_porcentagem': formset_porcentagem,
                                                          'formset_carencia': formset_carencia}, context_instance=RequestContext(request))
                        
                    return HttpResponseRedirect(reverse('listar_cdb_rdb'))
        for erros in form_cdb_rdb.errors.values():
            for erro in erros:
                messages.error(request, erro)
        for erro in formset_porcentagem.non_form_errors():
            messages.error(request, erro)
        for erro in formset_carencia.non_form_errors():
            messages.error(request, erro)
        return render_to_response('cdb_rdb/inserir_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'formset_porcentagem': formset_porcentagem,
                                                          'formset_carencia': formset_carencia}, context_instance=RequestContext(request))
    else:
        form_cdb_rdb = CDB_RDBForm()
        formset_porcentagem = PorcentagemFormSet()
        formset_carencia = CarenciaFormSet()
    return render_to_response('cdb_rdb/inserir_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'formset_porcentagem': formset_porcentagem,
                                                              'formset_carencia': formset_carencia}, context_instance=RequestContext(request))

@login_required
def inserir_operacao_cdb_rdb(request):
    investidor = request.user.investidor
    # Preparar formset para divisoes
    DivisaoCDB_RDBFormSet = inlineformset_factory(OperacaoCDB_RDB, DivisaoOperacaoCDB_RDB, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoCDB_RDBFormSet)
    
    if request.method == 'POST':
        form_operacao_cdb_rdb = OperacaoCDB_RDBForm(request.POST, investidor=investidor)
        formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(request.POST, investidor=investidor)
        
        # Validar CDB
        if form_operacao_cdb_rdb.is_valid():
            operacao_cdb_rdb = form_operacao_cdb_rdb.save(commit=False)
            operacao_cdb_rdb.investidor = investidor
            operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
            formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(request.POST, instance=operacao_cdb_rdb, operacao_compra=operacao_compra, investidor=investidor)
                
            # TODO Validar em caso de venda
            if form_operacao_cdb_rdb.cleaned_data['tipo_operacao'] == 'V':
                operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
                # Caso de venda total da letra de crédito
                if form_operacao_cdb_rdb.cleaned_data['quantidade'] == operacao_compra.quantidade:
                    # Desconsiderar divisões inseridas, copiar da operação de compra
                    operacao_cdb_rdb.save()
                    for divisao_cdb_rdb in DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao_compra):
                        divisao_cdb_rdb_venda = DivisaoOperacaoCDB_RDB(quantidade=divisao_cdb_rdb.quantidade, divisao=divisao_cdb_rdb.divisao, \
                                                             operacao=operacao_cdb_rdb)
                        divisao_cdb_rdb_venda.save()
                    operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                    operacao_venda_cdb_rdb.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('historico_cdb_rdb'))
                # Vendas parciais
                else:
                    if formset_divisao_cdb_rdb.is_valid():
                        operacao_cdb_rdb.save()
                        formset_divisao_cdb_rdb.save()
                        operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                        operacao_venda_cdb_rdb.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('historico_cdb_rdb'))
            else:
                if formset_divisao_cdb_rdb.is_valid():
                    operacao_cdb_rdb.save()
                    formset_divisao_cdb_rdb.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('historico_cdb_rdb'))
                    
        for erros in form_operacao_cdb_rdb.errors.values():
            for erro in erros:
                messages.error(request, erro)
        for erro in formset_divisao_cdb_rdb.non_form_errors():
            messages.error(request, erro)
                        
        return render_to_response('cdb_rdb/inserir_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao_cdb_rdb': formset_divisao_cdb_rdb},
                                  context_instance=RequestContext(request))
#                         print '%s %s'  % (divisao_cdb_rdb.quantidade, divisao_cdb_rdb.divisao)
                
    else:
        form_operacao_cdb_rdb = OperacaoCDB_RDBForm(investidor=investidor)
        formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(investidor=investidor)
    return render_to_response('cdb_rdb/inserir_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao_cdb_rdb': formset_divisao_cdb_rdb}, context_instance=RequestContext(request))

@login_required
def listar_cdb_rdb(request):
    investidor = request.user.investidor
    cdb_rdb = CDB_RDB.objects.filter(investidor=investidor)
    
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
def modificar_carencia_cdb_rdb(request, id):
    investidor = request.user.investidor
    cdb_rdb = CDB_RDB.objects.get(id=id)
    
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoCarenciaCDB_RDBForm(request.POST, initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de carência para %s alterado com sucesso' % historico.cdb_rdb)
            return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': cdb_rdb.id}))
    else:
        form = HistoricoCarenciaCDB_RDBForm(initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb)
            
    return render_to_response('cdb_rdb/modificar_carencia_cdb_rdb.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def modificar_porcentagem_cdb_rdb(request, id):
    investidor = request.user.investidor
    cdb_rdb = CDB_RDB.objects.get(id=id)
    
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoPorcentagemCDB_RDBForm(request.POST, initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de porcentagem de rendimento para %s alterado com sucesso' % historico.cdb_rdb)
            return HttpResponseRedirect(reverse('detalhar_cdb_rdb', kwargs={'id': cdb_rdb.id}))
    else:
        form = HistoricoPorcentagemCDB_RDBForm(initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb)
            
    return render_to_response('cdb_rdb/modificar_porcentagem_cdb_rdb.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def painel(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    if not operacoes:
        dados = {}
        dados['total_atual'] = Decimal(0)
        dados['total_ir'] = Decimal(0)
        dados['total_iof'] = Decimal(0)
        dados['total_ganho_prox_dia'] = Decimal(0)
        return render_to_response('cdb_rdb/painel.html', {'operacoes': {}, 'dados': dados},
                               context_instance=RequestContext(request))
    
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
                        # Calcular o valor atualizado para cada operacao
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
    
    return render_to_response('cdb_rdb/painel.html', {'operacoes': operacoes, 'dados': dados},
                               context_instance=RequestContext(request))