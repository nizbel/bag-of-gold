# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoLCFormSet
from bagogold.bagogold.forms.lc import OperacaoLetraCreditoForm, \
    HistoricoPorcentagemLetraCreditoForm, LetraCreditoForm, \
    HistoricoCarenciaLetraCreditoForm
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLC, Divisao
from bagogold.bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito, LetraCredito, HistoricoCarenciaLetraCredito, \
    OperacaoVendaLetraCredito
from bagogold.bagogold.models.td import HistoricoIPCA
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa_di, \
    calcular_valor_lc_ate_dia, simulador_lci_lca, \
    calcular_valor_atualizado_com_taxas_di
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import F
from django.db.models.functions import Coalesce
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
import calendar
import datetime
import json

@login_required
@adiciona_titulo_descricao('Detalhar Letra de Crédito', 'Detalhar Letra de Crédito, incluindo histórico de carência e '
                                                        'porcentagem de rendimento, além de dados da posição do investidor')
def detalhar_lci_lca(request, lci_lca_id):
    investidor = request.user.investidor
    
    lci_lca = get_object_or_404(LetraCredito, id=lci_lca_id)
    if lci_lca.investidor != investidor:
        raise PermissionDenied
    
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.filter(letra_credito=lci_lca)
    historico_carencia = HistoricoCarenciaLetraCredito.objects.filter(letra_credito=lci_lca)
    
    # Inserir dados do investimento
    lci_lca.carencia_atual = lci_lca.carencia_atual()
    lci_lca.porcentagem_atual = lci_lca.porcentagem_di_atual()
    
    # Preparar estatísticas zeradas
    lci_lca.total_investido = Decimal(0)
    lci_lca.saldo_atual = Decimal(0)
    lci_lca.total_iof = Decimal(0)
    lci_lca.lucro = Decimal(0)
    lci_lca.lucro_percentual = Decimal(0)
    
    operacoes = OperacaoLetraCredito.objects.filter(letra_credito=lci_lca).order_by('data')
    # Contar total de operações já realizadas 
    lci_lca.total_operacoes = len(operacoes)
    # Remover operacoes totalmente vendidas
    operacoes = [operacao for operacao in operacoes if operacao.qtd_disponivel_venda() > 0]
    if operacoes:
        historico_di = HistoricoTaxaDI.objects.filter(data__range=[operacoes[0].data, datetime.date.today()])
        for operacao in operacoes:
            # Total investido
            lci_lca.total_investido += operacao.qtd_disponivel_venda()
            
            # Saldo atual
            taxas = historico_di.filter(data__gte=operacao.data).values('taxa').annotate(qtd_dias=Count('taxa'))
            taxas_dos_dias = {}
            for taxa in taxas:
                taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.qtd_disponivel_venda(), operacao.porcentagem_di())
            lci_lca.saldo_atual += operacao.atual
            
            # Calcular impostos
            qtd_dias = (datetime.date.today() - operacao.data).days
            # IOF
            operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.quantidade)
            lci_lca.total_iof += operacao.iof
    
        # Pegar outras estatísticas
        str_auxiliar = str(lci_lca.saldo_atual.quantize(Decimal('.0001')))
        lci_lca.saldo_atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        
        lci_lca.lucro = lci_lca.saldo_atual - lci_lca.total_investido
        lci_lca.lucro_percentual = lci_lca.lucro / lci_lca.total_investido * 100
    try: 
        lci_lca.dias_proxima_retirada = (min(operacao.data + datetime.timedelta(days=operacao.carencia()) for operacao in operacoes if \
                                             (operacao.data + datetime.timedelta(days=operacao.carencia())) > datetime.date.today()) - datetime.date.today()).days
    except ValueError:
        lci_lca.dias_proxima_retirada = 0
    
    return TemplateResponse(request, 'lc/detalhar_lci_lca.html', {'lci_lca': lci_lca, 'historico_porcentagem': historico_porcentagem,
                                                                       'historico_carencia': historico_carencia})

@login_required
@adiciona_titulo_descricao('Editar registro de carência', 'Alterar registro de porcentagem no histórico de uma Letra de Crédito')
def editar_historico_carencia(request, historico_carencia_id):
    investidor = request.user.investidor
    historico_carencia = get_object_or_404(HistoricoCarenciaLetraCredito, id=historico_carencia_id)
    
    if historico_carencia.letra_credito.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_carencia.data is None:
                inicial = True
                form_historico_carencia = HistoricoCarenciaLetraCreditoForm(request.POST, instance=historico_carencia, letra_credito=historico_carencia.letra_credito, \
                                                                       investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_carencia = HistoricoCarenciaLetraCreditoForm(request.POST, instance=historico_carencia, letra_credito=historico_carencia.letra_credito, \
                                                                       investidor=investidor)
            if form_historico_carencia.is_valid():
                historico_carencia.save()
                messages.success(request, 'Histórico de carência editado com sucesso')
                return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': historico_carencia.letra_credito.id}))
            
            for erro in [erro for erro in form_historico_carencia.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_carencia.data is None:
                messages.error(request, 'Valor inicial de carência não pode ser excluído')
                return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': historico_carencia.letra_credito.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            inicial = False
            lci_lca = historico_carencia.letra_credito
            historico_carencia.delete()
            messages.success(request, 'Histórico de carência excluído com sucesso')
            return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': lci_lca.id}))
 
    else:
        if historico_carencia.data is None:
            inicial = True
            form_historico_carencia = HistoricoCarenciaLetraCreditoForm(instance=historico_carencia, letra_credito=historico_carencia.letra_credito, \
                                                                   investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_carencia = HistoricoCarenciaLetraCreditoForm(instance=historico_carencia, letra_credito=historico_carencia.letra_credito, \
                                                                   investidor=investidor)
            
    return TemplateResponse(request, 'lc/editar_historico_carencia.html', {'form_historico_carencia': form_historico_carencia, 'inicial': inicial}) 
    
@login_required
@adiciona_titulo_descricao('Editar registro de porcentagem', 'Alterar um registro de porcentagem no histórico da Letra de Crédito')
def editar_historico_porcentagem(request, historico_porcentagem_id):
    investidor = request.user.investidor
    historico_porcentagem = get_object_or_404(HistoricoPorcentagemLetraCredito, id=historico_porcentagem_id)
    
    if historico_porcentagem.letra_credito.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_porcentagem.data is None:
                inicial = True
                form_historico_porcentagem = HistoricoPorcentagemLetraCreditoForm(request.POST, instance=historico_porcentagem, letra_credito=historico_porcentagem.letra_credito, \
                                                                             investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_porcentagem = HistoricoPorcentagemLetraCreditoForm(request.POST, instance=historico_porcentagem, letra_credito=historico_porcentagem.letra_credito, \
                                                                             investidor=investidor)
            if form_historico_porcentagem.is_valid():
                historico_porcentagem.save(force_update=True)
                messages.success(request, 'Histórico de porcentagem editado com sucesso')
                return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': historico_porcentagem.letra_credito.id}))
                
            for erro in [erro for erro in form_historico_porcentagem.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_porcentagem.data is None:
                messages.error(request, 'Valor inicial de porcentagem não pode ser excluído')
                return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': historico_porcentagem.letra_credito.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            inicial = False
            lci_lca = historico_porcentagem.letra_credito
            historico_porcentagem.delete()
            messages.success(request, 'Histórico de porcentagem excluído com sucesso')
            return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': lci_lca.id}))
 
    else:
        if historico_porcentagem.data is None:
            inicial = True
            form_historico_porcentagem = HistoricoPorcentagemLetraCreditoForm(instance=historico_porcentagem, letra_credito=historico_porcentagem.letra_credito, \
                                                                         investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_porcentagem = HistoricoPorcentagemLetraCreditoForm(instance=historico_porcentagem, letra_credito=historico_porcentagem.letra_credito, \
                                                                         investidor=investidor)
            
    return TemplateResponse(request, 'lc/editar_historico_porcentagem.html', {'form_historico_porcentagem': form_historico_porcentagem, 'inicial': inicial}) 

@login_required
@adiciona_titulo_descricao('Editar Letra de Crédito', 'Alterar dados de uma Letra de Crédito')
def editar_lci_lca(request, lci_lca_id):
    investidor = request.user.investidor
    lci_lca = get_object_or_404(LetraCredito, id=lci_lca_id)
    
    if lci_lca.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_lci_lca = LetraCreditoForm(request.POST, instance=lci_lca)
            
            if form_lci_lca.is_valid():
                lci_lca.save()
                messages.success(request, 'Letra de Crédito editada com sucesso')
                return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': lci_lca.id}))
                
        # TODO verificar o que pode acontecer na exclusão
        elif request.POST.get("delete"):
            if OperacaoLetraCredito.objects.filter(letra_credito=lci_lca).exists():
                messages.error(request, 'Não é possível excluir a Letra de Crédito pois existem operações cadastradas')
                return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': lci_lca.id}))
            else:
                lci_lca.delete()
                messages.success(request, 'Letra de Crédito excluída com sucesso')
                return HttpResponseRedirect(reverse('lci_lca:listar_lci_lca'))
 
    else:
        form_lci_lca = LetraCreditoForm(instance=lci_lca)
            
    return TemplateResponse(request, 'lc/editar_lci_lca.html', {'form_lci_lca': form_lci_lca, 'lci_lca': lci_lca})  
    
@login_required
@adiciona_titulo_descricao('Editar operação em Letras de Crédito', 'Alterar valores de uma operação de compra/venda em Letras de Crédito')
def editar_operacao_lc(request, id):
    investidor = request.user.investidor
    
    operacao_lc = OperacaoLetraCredito.objects.get(pk=id)
    
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if operacao_lc.investidor != investidor:
        raise PermissionDenied
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoLetraCredito, DivisaoOperacaoLC, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoLCFormSet)
    
    if request.method == 'POST':
        form_operacao_lc = OperacaoLetraCreditoForm(request.POST, instance=operacao_lc, investidor=investidor)
        formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc, investidor=investidor) if varias_divisoes else None
        
        if request.POST.get("save"):
            if form_operacao_lc.is_valid():
                operacao_compra = form_operacao_lc.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_lc.save()
                        if operacao_lc.tipo_operacao == 'V':
                            if not OperacaoVendaLetraCredito.objects.filter(operacao_venda=operacao_lc):
                                operacao_venda_lc = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                                operacao_venda_lc.save()
                            else: 
                                operacao_venda_lc = OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao_lc)
                                if operacao_venda_lc.operacao_compra != operacao_compra:
                                    operacao_venda_lc.operacao_compra = operacao_compra
                                    operacao_venda_lc.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação editada com sucesso')
                        return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                else:
                    operacao_lc.save()
                    if operacao_lc.tipo_operacao == 'V':
                        if not OperacaoVendaLetraCredito.objects.filter(operacao_venda=operacao_lc):
                            operacao_venda_lc = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                            operacao_venda_lc.save()
                        else: 
                            operacao_venda_lc = OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao_lc)
                            if operacao_venda_lc.operacao_compra != operacao_compra:
                                operacao_venda_lc.operacao_compra = operacao_compra
                                operacao_venda_lc.save()
                    divisao_operacao = DivisaoOperacaoLC.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_lc)
                    divisao_operacao.quantidade = operacao_lc.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
            for erros in form_operacao_lc.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
#                         print '%s %s'  % (divisao_lc.quantidade, divisao_lc.divisao)
                
        elif request.POST.get("delete"):
            # Testa se operação a excluir não é uma operação de compra com vendas já registradas
            if not OperacaoVendaLetraCredito.objects.filter(operacao_compra=operacao_lc):
                divisao_lc = DivisaoOperacaoLC.objects.filter(operacao=operacao_lc)
                for divisao in divisao_lc:
                    divisao.delete()
                if operacao_lc.tipo_operacao == 'V':
                    OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao_lc).delete()
                operacao_lc.delete()
                messages.success(request, 'Operação excluída com sucesso')
                return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
            else:
                messages.error(request, 'Não é possível excluir operação de compra que já tenha vendas registradas')
 
    else:
        form_operacao_lc = OperacaoLetraCreditoForm(instance=operacao_lc, investidor=investidor, initial={'operacao_compra': operacao_lc.operacao_compra_relacionada(),})
        formset_divisao = DivisaoFormSet(instance=operacao_lc, investidor=investidor)
            
    return TemplateResponse(request, 'lc/editar_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})  

    
@adiciona_titulo_descricao('Histórico de Letras de Crédito', 'Histórico de operações de compra/venda em Letras de Crédito do investidor')
def historico(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'lc/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_gasto_total': list(), 'graf_patrimonio': list()})
    
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    
    # Se investidor não fez operações, retornar
    if not operacoes:
        return TemplateResponse(request, 'lc/historico.html', {'dados': {}})
    
    historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.all() 
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        operacao.taxa = operacao.porcentagem_di()
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
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
                            # Quantidade restante guarda o quanto da operação de compra ainda não foi vendido
                            operacao.qtd_restante = operacao.quantidade
                            total_gasto += operacao.total
                        if taxa_do_dia > 0:
                            # Calcular o valor atualizado para cada operacao
                            operacao.atual = calcular_valor_atualizado_com_taxa_di(taxa_do_dia, operacao.atual, operacao.taxa)
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
                                operacao.atual = (operacao.quantidade/operacao_c.qtd_restante) * operacao_c.atual
                                operacao_c.qtd_restante -= operacao.quantidade
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
    dados['lucro_percentual'] = ((total_patrimonio - total_gasto) / total_gasto * 100) if total_gasto > 0 else 0
    
    return TemplateResponse(request, 'lc/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio})
    
@login_required
@adiciona_titulo_descricao('Inserir registro de carência para uma Letra de Crédito', 'Inserir registro de alteração na carência ao histórico de '
                                                                                     'uma Letra de Crédito')
def inserir_historico_carencia(request, lci_lca_id):
    investidor = request.user.investidor
    lci_lca = get_object_or_404(LetraCredito, id=lci_lca_id)
    
    if lci_lca.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoCarenciaLetraCreditoForm(request.POST, initial={'letra_credito': lci_lca.id}, letra_credito=lci_lca, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de carência para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoCarenciaLetraCreditoForm(initial={'letra_credito': lci_lca.id}, letra_credito=lci_lca, investidor=investidor)
            
    return TemplateResponse(request, 'lc/inserir_historico_carencia_lci_lca.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir registro de porcentagem de rendimento para uma Letra de Crédito', 'Inserir registro de alteração de porcentagem '
                                                                                                      'de rendimento ao histsórico de uma Letra de Crédito')
def inserir_historico_porcentagem(request, lci_lca_id):
    investidor = request.user.investidor
    lci_lca = get_object_or_404(LetraCredito, id=lci_lca_id)
    
    if lci_lca.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoPorcentagemLetraCreditoForm(request.POST, initial={'letra_credito': lci_lca.id}, letra_credito=lci_lca, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de porcentagem de rendimento para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoPorcentagemLetraCreditoForm(initial={'letra_credito': lci_lca.id}, letra_credito=lci_lca, investidor=investidor)
            
    return TemplateResponse(request, 'lc/inserir_historico_porcentagem_lci_lca.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir Letra de Crédito', 'Inserir Letra de Crédito às letras cadastradas pelo investidor')
def inserir_lc(request):
    investidor = request.user.investidor
    
    # Preparar formsets 
    PorcentagemFormSet = inlineformset_factory(LetraCredito, HistoricoPorcentagemLetraCredito, fields=('porcentagem_di',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True)
    CarenciaFormSet = inlineformset_factory(LetraCredito, HistoricoCarenciaLetraCredito, fields=('carencia',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True, labels = {'carencia': 'Período de carência (em dias)',})
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_lc = LetraCreditoForm(request.POST)
            formset_porcentagem = PorcentagemFormSet(request.POST)
            formset_carencia = CarenciaFormSet(request.POST)
            if form_lc.is_valid():
                lc = form_lc.save(commit=False)
                lc.investidor = investidor
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
                            return TemplateResponse(request, 'lc/inserir_lc.html', {'form_lc': form_lc, 'formset_porcentagem': formset_porcentagem,
                                                                         'formset_carencia': formset_carencia})
                        return HttpResponseRedirect(reverse('lci_lca:listar_lci_lca'))
                    
            for erro in [erro for erro in form_lc.non_field_errors()]:
                messages.error(request, erro.message)
            for erro in formset_porcentagem.non_form_errors():
                messages.error(request, erro)
            for erro in formset_carencia.non_form_errors():
                messages.error(request, erro)

    else:
        form_lc = LetraCreditoForm()
        formset_porcentagem = PorcentagemFormSet()
        formset_carencia = CarenciaFormSet()
    return TemplateResponse(request, 'lc/inserir_lc.html', {'form_lc': form_lc, 'formset_porcentagem': formset_porcentagem,
                                                              'formset_carencia': formset_carencia})

@login_required
@adiciona_titulo_descricao('Inserir operações em Letras de Crédito', 'Inserir registro de operação de compra/venda em Letras de Crédito ao histórico')
def inserir_operacao_lc(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoLetraCredito, DivisaoOperacaoLC, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoLCFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_lc = OperacaoLetraCreditoForm(request.POST, investidor=investidor)
            formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
            
            # Validar Letra de Crédito
            if form_operacao_lc.is_valid():
                operacao_lc = form_operacao_lc.save(commit=False)
                operacao_lc.investidor = investidor
                operacao_compra = form_operacao_lc.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                    
                # Validar em caso de venda
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
                        return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                    # Vendas parciais
                    else:
                        # Verificar se varias divisões
                        if varias_divisoes:
                            if formset_divisao.is_valid():
                                operacao_lc.save()
                                formset_divisao.save()
                                operacao_venda_lc = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                                operacao_venda_lc.save()
                                messages.success(request, 'Operação inserida com sucesso')
                                return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                            for erro in formset_divisao.non_form_errors():
                                messages.error(request, erro)
                                
                        else:
                            operacao_lc.save()
                            divisao_operacao = DivisaoOperacaoLC(operacao=operacao_lc, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_lc.quantidade)
                            divisao_operacao.save()
                            operacao_venda_lc = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                            operacao_venda_lc.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                        
                # Compra
                else:
                    # Verificar se várias divisões
                    if varias_divisoes:
                        if formset_divisao.is_valid():
                            operacao_lc.save()
                            formset_divisao.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                        for erro in formset_divisao.non_form_errors():
                            messages.error(request, erro)
                            
                    else:
                        operacao_lc.save()
                        divisao_operacao = DivisaoOperacaoLC(operacao=operacao_lc, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_lc.quantidade)
                        divisao_operacao.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                        
            for erros in form_operacao_lc.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
#                         print '%s %s'  % (divisao_lc.quantidade, divisao_lc.divisao)
                
    else:
        form_operacao_lc = OperacaoLetraCreditoForm(investidor=investidor)
        formset_divisao = DivisaoFormSet(investidor=investidor)
    return TemplateResponse(request, 'lc/inserir_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@adiciona_titulo_descricao('Lista de Letras de Crédito', 'Traz as Letras de Crédito cadastradas pelo investidor')
def listar_lc(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'lc/listar_lc.html', {'lcs': list()})
        
    lcs = LetraCredito.objects.filter(investidor=investidor)
    
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

    return TemplateResponse(request, 'lc/listar_lc.html', {'lcs': lcs})

# Retorna id's das operações que podem ser vendidas na data especificada
@login_required
def listar_operacoes_passada_carencia(request):
    if request.is_ajax():
        if request.GET.get('data'):
            try:
                data = datetime.datetime.strptime(request.GET.get('data'), '%d/%m/%Y').date()
            except:
                return HttpResponse(json.dumps({'sucesso': False, 'mensagem': u'Formato de data inválido'}), content_type = "application/json") 
        else:
            return HttpResponse(json.dumps({'sucesso': False, 'mensagem': u'Data é obrigatória'}), content_type = "application/json") 
        
        investidor = request.user.investidor
        
        operacoes = OperacaoLetraCredito.objects.filter(investidor=investidor, tipo_operacao='C').annotate( \
            qtd_vendida=Coalesce(Sum(F('operacao_compra__operacao_venda__quantidade')), 0)).exclude(qtd_vendida=F('quantidade'))
        operacoes = [operacao for operacao in operacoes if data >= operacao.data_carencia()]
        
         # Verificar se trata-se de uma edição de operação de venda
        if request.GET.get('id_venda'):
            operacao_compra_relacionada = OperacaoLetraCredito.objects.get(id=request.GET.get('id_venda')).operacao_compra_relacionada()
            if operacao_compra_relacionada.id not in [operacao.id for operacao in operacoes] and data >= operacao_compra_relacionada.data_carencia():
                operacoes.append(operacao_compra_relacionada)
        
        return HttpResponse(json.dumps({'sucesso': True, 'operacoes': [str(operacao.id) for operacao in operacoes]}), content_type = "application/json")   
    else:
        return HttpResponse(json.dumps({'sucesso': False}), content_type = "application/json") 

@adiciona_titulo_descricao('Painel de Letras de Crédito', 'Posição atual do investidor em Letras de Crédito')
def painel(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'lc/painel.html', {'operacoes': list(), 'dados': {}})
    
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    
    # Se não há operações, retornar
    if not operacoes:
        return TemplateResponse(request, 'lc/painel.html', {'operacoes': operacoes, 'dados': {}})
    
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
                        operacao.atual = calcular_valor_atualizado_com_taxa_di(taxa_do_dia, operacao.atual, operacao.taxa)
                        # Arredondar na última iteração
                        if (data_iteracao == data_final):
                            str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                            operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                        
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
        
    # Preencher última taxa do dia caso não tenha sido preenchida no loop das operações
    taxa_do_dia = HistoricoTaxaDI.objects.all().order_by('-data')[0].taxa
    
    # Remover operações que não estejam mais rendendo
    operacoes = [operacao for operacao in operacoes if (operacao.atual > 0 and operacao.tipo_operacao == 'C')]
    
    total_atual = 0
    total_ganho_prox_dia = 0
    for operacao in operacoes:
        # Calcular o ganho no dia seguinte, considerando taxa do dia anterior
        operacao.ganho_prox_dia = calcular_valor_atualizado_com_taxa_di(taxa_do_dia, operacao.atual, operacao.taxa) - operacao.atual
        str_auxiliar = str(operacao.ganho_prox_dia.quantize(Decimal('.0001')))
        operacao.ganho_prox_dia = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        total_ganho_prox_dia += operacao.ganho_prox_dia
        # Cálculo do valor total atual
        total_atual += operacao.atual
    
    # Popular dados
    dados = {}
    dados['total_atual'] = total_atual
    dados['total_ganho_prox_dia'] = total_ganho_prox_dia
    dados['data_di_mais_recente'] = data_final
    
    return TemplateResponse(request, 'lc/painel.html', {'operacoes': operacoes, 'dados': dados})

@adiciona_titulo_descricao('Sobre Letras de Crédito', 'Detalha o que são Letras de Crédito')
def sobre(request):
    if request.is_ajax():
        try:
            aplicacao = Decimal(request.GET.get('qtd').replace('.', '').replace(',', '.'))
            filtros_simulador = {'periodo': Decimal(request.GET.get('periodo')), 'percentual_indice': Decimal(request.GET.get('percentual_indice')), \
                             'tipo': 'POS', 'indice': 'DI', 'aplicacao': aplicacao}
        except:
            return HttpResponse(json.dumps({'sucesso': False, 'mensagem': u'Variáveis de entrada inválidas'}), content_type = "application/json") 
        
        graf_simulador = [[str(calendar.timegm(data.timetuple()) * 1000), float(valor_lci_lca)] for data, valor_lci_lca in simulador_lci_lca(filtros_simulador)]
        return HttpResponse(json.dumps({'sucesso': True, 'graf_simulador': graf_simulador}), content_type = "application/json") 
    else:
        data_atual = datetime.date.today()
        historico_di = HistoricoTaxaDI.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3))
        graf_historico_di = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(valor_historico.taxa)] for valor_historico in historico_di]
        
        historico_ipca = HistoricoIPCA.objects.filter(ano__gte=(data_atual.year-3)).exclude(mes__lt=data_atual.month, ano=data_atual.year-3)
        graf_historico_ipca = [[str(calendar.timegm(valor_historico.data().timetuple()) * 1000), float(valor_historico.valor)] for valor_historico in historico_ipca]
        
        if request.user.is_authenticated():
            total_atual = sum(calcular_valor_lc_ate_dia(request.user.investidor).values())
        else:
            total_atual = 0
        
        filtros_simulador = {'periodo': Decimal(12), 'percentual_indice': Decimal(85), 'tipo': 'POS', 'indice': 'DI', 'aplicacao': Decimal(1000)}
        
        graf_simulador = [[str(calendar.timegm(data.timetuple()) * 1000), float(valor_lci_lca)] for data, valor_lci_lca in simulador_lci_lca(filtros_simulador)]
        
        return TemplateResponse(request, 'lc/sobre.html', {'graf_historico_di': graf_historico_di, 'graf_historico_ipca': graf_historico_ipca,
                                                           'total_atual': total_atual, 'filtros_simulador': filtros_simulador,
                                                           'graf_simulador': graf_simulador})