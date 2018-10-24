# -*- coding: utf-8 -*-
import calendar
import datetime
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import mail_admins
from django.db.models.expressions import F, Case, When, Value
from django.shortcuts import get_object_or_404
import json
import traceback

from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.aggregates import Count, Sum
from django.db.models.fields import CharField, DecimalField
from django.db.models.functions import Coalesce
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse

from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoLCI_LCAFormSet
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLCI_LCA, Divisao
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI, \
    HistoricoIPCA
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
from bagogold.bagogold.utils.taxas_indexacao import \
    calcular_valor_atualizado_com_taxas_di, calcular_valor_atualizado_com_taxa_di
from bagogold.lci_lca.forms import OperacaoLetraCreditoForm, \
    HistoricoPorcentagemLetraCreditoForm, LetraCreditoForm, \
    HistoricoCarenciaLetraCreditoForm, HistoricoVencimentoLetraCreditoForm
from bagogold.lci_lca.models import OperacaoLetraCredito, \
    HistoricoPorcentagemLetraCredito, LetraCredito, HistoricoCarenciaLetraCredito, \
    OperacaoVendaLetraCredito, HistoricoVencimentoLetraCredito
from bagogold.lci_lca.utils import simulador_lci_lca, \
    calcular_valor_lci_lca_ate_dia


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
    historico_vencimento = HistoricoVencimentoLetraCredito.objects.filter(letra_credito=lci_lca)
    
    # Inserir dados do investimento
    lci_lca.carencia_atual = lci_lca.carencia_atual()
    lci_lca.porcentagem_atual = lci_lca.porcentagem_atual()
    lci_lca.vencimento_atual = lci_lca.vencimento_atual()
    
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
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.qtd_disponivel_venda(), operacao.porcentagem())
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
    
    return TemplateResponse(request, 'lci_lca/detalhar_lci_lca.html', {'lci_lca': lci_lca, 'historico_porcentagem': historico_porcentagem,
                                                                       'historico_carencia': historico_carencia, 'historico_vencimento': historico_vencimento})

@login_required
@adiciona_titulo_descricao('Editar registro de carência', 'Alterar registro de carência no histórico de uma Letra de Crédito')
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
            
    return TemplateResponse(request, 'lci_lca/editar_historico_carencia.html', {'form_historico_carencia': form_historico_carencia, 'inicial': inicial}) 
    
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
            
    return TemplateResponse(request, 'lci_lca/editar_historico_porcentagem.html', {'form_historico_porcentagem': form_historico_porcentagem, 'inicial': inicial}) 

@login_required
@adiciona_titulo_descricao('Editar registro de vencimento', 'Alterar registro de vencimento no histórico de uma Letra de Crédito')
def editar_historico_vencimento(request, historico_vencimento_id):
    investidor = request.user.investidor
    historico_vencimento = get_object_or_404(HistoricoVencimentoLetraCredito, id=historico_vencimento_id)
    
    if historico_vencimento.letra_credito.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_vencimento.data is None:
                inicial = True
                form_historico_vencimento = HistoricoVencimentoLetraCreditoForm(request.POST, instance=historico_vencimento, letra_credito=historico_vencimento.letra_credito, \
                                                                       investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_vencimento = HistoricoVencimentoLetraCreditoForm(request.POST, instance=historico_vencimento, letra_credito=historico_vencimento.letra_credito, \
                                                                       investidor=investidor)
            if form_historico_vencimento.is_valid():
                historico_vencimento.save()
                messages.success(request, 'Histórico de vencimento editado com sucesso')
                return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': historico_vencimento.letra_credito.id}))
            
            for erro in [erro for erro in form_historico_vencimento.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_vencimento.data is None:
                messages.error(request, 'Valor inicial de vencimento não pode ser excluído')
                return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': historico_vencimento.letra_credito.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            inicial = False
            lci_lca = historico_vencimento.letra_credito
            historico_vencimento.delete()
            messages.success(request, 'Histórico de vencimento excluído com sucesso')
            return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': lci_lca.id}))
 
    else:
        if historico_vencimento.data is None:
            inicial = True
            form_historico_vencimento = HistoricoVencimentoLetraCreditoForm(instance=historico_vencimento, letra_credito=historico_vencimento.letra_credito, \
                                                                   investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_vencimento = HistoricoVencimentoLetraCreditoForm(instance=historico_vencimento, letra_credito=historico_vencimento.letra_credito, \
                                                                   investidor=investidor)
            
    return TemplateResponse(request, 'lci_lca/editar_historico_vencimento.html', {'form_historico_vencimento': form_historico_vencimento, 'inicial': inicial}) 

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
            
    return TemplateResponse(request, 'lci_lca/editar_lci_lca.html', {'form_lci_lca': form_lci_lca, 'lci_lca': lci_lca})  
    
@login_required
@adiciona_titulo_descricao('Editar operação em Letras de Crédito', 'Alterar valores de uma operação de compra/venda em Letras de Crédito')
def editar_operacao_lci_lca(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_lci_lca = OperacaoLetraCredito.objects.get(pk=operacao_id)
    
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if operacao_lci_lca.investidor != investidor:
        raise PermissionDenied
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = Divisao.objects.filter(investidor=investidor).count() > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoLetraCredito, DivisaoOperacaoLCI_LCA, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoLCI_LCAFormSet)
    
    if request.method == 'POST':
        form_operacao_lci_lca = OperacaoLetraCreditoForm(request.POST, instance=operacao_lci_lca, investidor=investidor)
        formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lci_lca, investidor=investidor) if varias_divisoes else None
        
        if request.POST.get("save"):
            if form_operacao_lci_lca.is_valid():
                operacao_compra = form_operacao_lci_lca.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lci_lca, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_lci_lca.save()
                        if operacao_lci_lca.tipo_operacao == 'V':
                            if not OperacaoVendaLetraCredito.objects.filter(operacao_venda=operacao_lci_lca):
                                operacao_venda_lci_lca = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lci_lca)
                                operacao_venda_lci_lca.save()
                            else: 
                                operacao_venda_lci_lca = OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao_lci_lca)
                                if operacao_venda_lci_lca.operacao_compra != operacao_compra:
                                    operacao_venda_lci_lca.operacao_compra = operacao_compra
                                    operacao_venda_lci_lca.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação editada com sucesso')
                        return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                else:
                    operacao_lci_lca.save()
                    if operacao_lci_lca.tipo_operacao == 'V':
                        if not OperacaoVendaLetraCredito.objects.filter(operacao_venda=operacao_lci_lca):
                            operacao_venda_lci_lca = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lci_lca)
                            operacao_venda_lci_lca.save()
                        else: 
                            operacao_venda_lci_lca = OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao_lci_lca)
                            if operacao_venda_lci_lca.operacao_compra != operacao_compra:
                                operacao_venda_lci_lca.operacao_compra = operacao_compra
                                operacao_venda_lci_lca.save()
                    divisao_operacao = DivisaoOperacaoLCI_LCA.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_lci_lca)
                    divisao_operacao.quantidade = operacao_lci_lca.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
            for erros in form_operacao_lci_lca.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
#                         print '%s %s'  % (divisao_lci_lca.quantidade, divisao_lci_lca.divisao)
                
        elif request.POST.get("delete"):
            # Testa se operação a excluir não é uma operação de compra com vendas já registradas
            if not OperacaoVendaLetraCredito.objects.filter(operacao_compra=operacao_lci_lca):
                divisao_lci_lca = DivisaoOperacaoLCI_LCA.objects.filter(operacao=operacao_lci_lca)
                for divisao in divisao_lci_lca:
                    divisao.delete()
                if operacao_lci_lca.tipo_operacao == 'V':
                    OperacaoVendaLetraCredito.objects.get(operacao_venda=operacao_lci_lca).delete()
                operacao_lci_lca.delete()
                messages.success(request, 'Operação excluída com sucesso')
                return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
            else:
                messages.error(request, 'Não é possível excluir operação de compra que já tenha vendas registradas')
 
    else:
        form_operacao_lci_lca = OperacaoLetraCreditoForm(instance=operacao_lci_lca, investidor=investidor, initial={'operacao_compra': operacao_lci_lca.operacao_compra_relacionada(),})
        formset_divisao = DivisaoFormSet(instance=operacao_lci_lca, investidor=investidor)
            
    return TemplateResponse(request, 'lci_lca/editar_operacao_lci_lca.html', {'form_operacao_lci_lca': form_operacao_lci_lca, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})  

    
@adiciona_titulo_descricao('Histórico de Letras de Crédito', 'Histórico de operações de compra/venda em Letras de Crédito do investidor')
def historico(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'lci_lca/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_gasto_total': list(), 'graf_patrimonio': list()})
    
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).annotate(tipo=Case(When(tipo_operacao='C', then=Value(u'Compra')),
                                                            When(tipo_operacao='V', then=Value(u'Venda')), output_field=CharField())) \
                                        .annotate(atual=Case(When(tipo_operacao='C', then=F('quantidade')), output_field=DecimalField())).order_by('-tipo_operacao', 'data') 
    
    # Se investidor não fez operações, retornar
    if not operacoes:
        return TemplateResponse(request, 'lci_lca/historico.html', {'dados': {}})
    
#     historico_porcentagem = HistoricoPorcentagemLetraCredito.objects.all() 
    # Prepara o campo valor atual
#     for operacao in operacoes:
#         operacao.atual = operacao.quantidade
#         operacao.taxa = operacao.porcentagem()
#         if operacao.tipo_operacao == 'C':
#             operacao.tipo = 'Compra'
#         else:
#             operacao.tipo = 'Venda'
    
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
        if HistoricoTaxaDI.objects.filter(data=data_iteracao).exists():
            taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
        else:
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
                        operacao.atual = calcular_valor_atualizado_com_taxa_di(taxa_do_dia, operacao.atual, operacao.porcentagem())
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
    
    return TemplateResponse(request, 'lci_lca/historico.html', {'dados': dados, 'operacoes': operacoes, 
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
            return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': lci_lca_id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoCarenciaLetraCreditoForm(initial={'letra_credito': lci_lca.id}, letra_credito=lci_lca, investidor=investidor)
            
    return TemplateResponse(request, 'lci_lca/inserir_historico_carencia_lci_lca.html', {'form': form})

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
            return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': lci_lca_id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoPorcentagemLetraCreditoForm(initial={'letra_credito': lci_lca.id}, letra_credito=lci_lca, investidor=investidor)
            
    return TemplateResponse(request, 'lci_lca/inserir_historico_porcentagem_lci_lca.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir registro de vencimento para uma Letra de Crédito', 'Inserir registro de alteração na vencimento ao histórico de '
                                                                                     'uma Letra de Crédito')
def inserir_historico_vencimento(request, lci_lca_id):
    investidor = request.user.investidor
    lci_lca = get_object_or_404(LetraCredito, id=lci_lca_id)
    
    if lci_lca.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoVencimentoLetraCreditoForm(request.POST, initial={'letra_credito': lci_lca.id}, letra_credito=lci_lca, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de vencimento para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('lci_lca:detalhar_lci_lca', kwargs={'lci_lca_id': lci_lca_id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoVencimentoLetraCreditoForm(initial={'letra_credito': lci_lca.id}, letra_credito=lci_lca, investidor=investidor)
            
    return TemplateResponse(request, 'lci_lca/inserir_historico_vencimento_lci_lca.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir Letra de Crédito', 'Inserir Letra de Crédito às letras cadastradas pelo investidor')
def inserir_lci_lca(request):
    investidor = request.user.investidor
    
    # Preparar formsets 
    PorcentagemFormSet = inlineformset_factory(LetraCredito, HistoricoPorcentagemLetraCredito, fields=('porcentagem',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True)
    CarenciaFormSet = inlineformset_factory(LetraCredito, HistoricoCarenciaLetraCredito, fields=('carencia',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True, labels = {'carencia': 'Período de carência',})
    VencimentoFormSet = inlineformset_factory(LetraCredito, HistoricoVencimentoLetraCredito, fields=('vencimento',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True, labels = {'vencimento': 'Período de vencimento',})
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_lci_lca = LetraCreditoForm(request.POST)
            formset_porcentagem = PorcentagemFormSet(request.POST)
            formset_carencia = CarenciaFormSet(request.POST)
            formset_vencimento = VencimentoFormSet(request.POST)
            if form_lci_lca.is_valid():
                lci_lca = form_lci_lca.save(commit=False)
                lci_lca.investidor = investidor
                formset_porcentagem = PorcentagemFormSet(request.POST, instance=lci_lca)
                formset_porcentagem.forms[0].empty_permitted=False
                formset_carencia = CarenciaFormSet(request.POST, instance=lci_lca)
                formset_carencia.forms[0].empty_permitted=False
                formset_vencimento = VencimentoFormSet(request.POST, instance=lci_lca)
                formset_vencimento.forms[0].empty_permitted=False
                
                if formset_porcentagem.is_valid():
                    if formset_carencia.is_valid():
                        if formset_vencimento.is_valid():
                            try:
                                if formset_vencimento.forms[0].cleaned_data['vencimento'] < formset_carencia.forms[0].cleaned_data['carencia']:
                                    raise ValidationError('Período de carência não pode ser maior que período de vencimento')
                                with transaction.atomic():
                                    lci_lca.save()
                                    formset_porcentagem.save()
                                    formset_carencia.save()
                                    formset_vencimento.save()
                            # Capturar erros oriundos da hora de salvar os objetos
                            except Exception as erro:
                                messages.error(request, erro.message)
                                return TemplateResponse(request, 'lci_lca/inserir_lci_lca.html', {'form_lci_lca': form_lci_lca, 'formset_porcentagem': formset_porcentagem,
                                                                             'formset_carencia': formset_carencia, 'formset_vencimento': formset_vencimento})
                            return HttpResponseRedirect(reverse('lci_lca:listar_lci_lca'))
                    
            for erro in form_lci_lca.non_field_errors():
                messages.error(request, erro.message)
            for erro in formset_porcentagem.non_form_errors():
                messages.error(request, erro)
            for erro in formset_carencia.non_form_errors():
                messages.error(request, erro)
            for erro in formset_vencimento.non_form_errors():
                messages.error(request, erro)

    else:
        form_lci_lca = LetraCreditoForm()
        formset_porcentagem = PorcentagemFormSet()
        formset_carencia = CarenciaFormSet()
        formset_vencimento = VencimentoFormSet()
    return TemplateResponse(request, 'lci_lca/inserir_lci_lca.html', {'form_lci_lca': form_lci_lca, 'formset_porcentagem': formset_porcentagem,
                                                              'formset_carencia': formset_carencia, 'formset_vencimento': formset_vencimento})

@login_required
@adiciona_titulo_descricao('Inserir operações em Letras de Crédito', 'Inserir registro de operação de compra/venda em Letras de Crédito ao histórico')
def inserir_operacao_lci_lca(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoLetraCredito, DivisaoOperacaoLCI_LCA, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoLCI_LCAFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = Divisao.objects.filter(investidor=investidor).count() > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_lci_lca = OperacaoLetraCreditoForm(request.POST, investidor=investidor)
            formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
            
            try:
                with transaction.atomic():
                    # Validar Letra de Crédito
                    if form_operacao_lci_lca.is_valid():
                        operacao_lci_lca = form_operacao_lci_lca.save(commit=False)
                        operacao_lci_lca.investidor = investidor
                        operacao_compra = form_operacao_lci_lca.cleaned_data['operacao_compra']
                        formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lci_lca, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                            
                        # Validar em caso de venda
                        if form_operacao_lci_lca.cleaned_data['tipo_operacao'] == 'V':
                            operacao_compra = form_operacao_lci_lca.cleaned_data['operacao_compra']
                            # Caso de venda total da letra de crédito
                            if form_operacao_lci_lca.cleaned_data['quantidade'] == operacao_compra.quantidade:
                                # Desconsiderar divisões inseridas, copiar da operação de compra
                                operacao_lci_lca.save()
                                operacao_venda_lci_lca = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lci_lca)
                                operacao_venda_lci_lca.save()
                                for divisao_lci_lca in DivisaoOperacaoLCI_LCA.objects.filter(operacao=operacao_compra):
                                    divisao_lci_lca_venda = DivisaoOperacaoLCI_LCA(quantidade=divisao_lci_lca.quantidade, divisao=divisao_lci_lca.divisao, \
                                                                         operacao=operacao_lci_lca)
                                    divisao_lci_lca_venda.save()
                                messages.success(request, 'Operação inserida com sucesso')
                                return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                            # Vendas parciais
                            else:
                                # Verificar se varias divisões
                                if varias_divisoes:
                                    if formset_divisao.is_valid():
                                        operacao_lci_lca.save()
                                        formset_divisao.save()
                                        operacao_venda_lci_lca = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lci_lca)
                                        operacao_venda_lci_lca.save()
                                        messages.success(request, 'Operação inserida com sucesso')
                                        return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                                    for erro in formset_divisao.non_form_errors():
                                        messages.error(request, erro)
                                        
                                else:
                                    operacao_lci_lca.save()
                                    divisao_operacao = DivisaoOperacaoLCI_LCA(operacao=operacao_lci_lca, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_lci_lca.quantidade)
                                    divisao_operacao.save()
                                    operacao_venda_lci_lca = OperacaoVendaLetraCredito(operacao_compra=operacao_compra, operacao_venda=operacao_lci_lca)
                                    operacao_venda_lci_lca.save()
                                    messages.success(request, 'Operação inserida com sucesso')
                                    return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                                
                        # Compra
                        else:
                            # Verificar se várias divisões
                            if varias_divisoes:
                                if formset_divisao.is_valid():
                                    operacao_lci_lca.save()
                                    formset_divisao.save()
                                    messages.success(request, 'Operação inserida com sucesso')
                                    return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))
                                for erro in formset_divisao.non_form_errors():
                                    messages.error(request, erro)
                                    
                            else:
                                operacao_lci_lca.save()
                                divisao_operacao = DivisaoOperacaoLCI_LCA(operacao=operacao_lci_lca, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_lci_lca.quantidade)
                                divisao_operacao.save()
                                messages.success(request, 'Operação inserida com sucesso')
                                return HttpResponseRedirect(reverse('lci_lca:historico_lci_lca'))

            except:
                messages.error(request, 'Houve um erro ao inserir a operação')
                if settings.ENV == 'DEV':
                    raise
                elif settings.ENV == 'PROD':
                    mail_admins(u'Erro ao inserir operação em LCI/LCA', traceback.format_exc().decode('utf-8')) 
                    
        for erro in [erro for erro in form_operacao_lci_lca.non_field_errors()]:
            messages.error(request, erro)
#             for erros in form_operacao_lci_lca.errors.values():
#                 for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
#                     messages.error(request, erro.message)
# #                         print '%s %s'  % (divisao_lci_lca.quantidade, divisao_lci_lca.divisao)
                
    else:
        form_operacao_lci_lca = OperacaoLetraCreditoForm(investidor=investidor)
        formset_divisao = DivisaoFormSet(investidor=investidor)
    return TemplateResponse(request, 'lci_lca/inserir_operacao_lci_lca.html', {'form_operacao_lci_lca': form_operacao_lci_lca, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@adiciona_titulo_descricao('Lista de Letras de Crédito', 'Traz as Letras de Crédito cadastradas pelo investidor')
def listar_lci_lca(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'lci_lca/listar_lci_lca.html', {'letras_credito': list()})
        
    letras_credito = LetraCredito.objects.filter(investidor=investidor)
    
    return TemplateResponse(request, 'lci_lca/listar_lci_lca.html', {'letras_credito': letras_credito})

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
        return TemplateResponse(request, 'lci_lca/painel.html', {'operacoes': list(), 'dados': {}})
    
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).select_related('letra_credito').order_by('-tipo_operacao', 'data') 
    
    # Se não há operações, retornar
    if not operacoes:
        return TemplateResponse(request, 'lci_lca/painel.html', {'operacoes': operacoes, 'dados': {}})
    
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        if operacao.tipo_operacao == 'C':
            operacao.taxa = operacao.porcentagem()
    
    # Pegar data inicial
    data_inicial = operacoes.order_by('data')[0].data
    
    # Pegar data final
    data_final = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
    
    data_iteracao = data_inicial
    
    for data_iteracao in HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_final]).order_by('data'):
        taxa_do_dia = data_iteracao.taxa
          
        # Processar operações
        for operacao in operacoes:     
            if (operacao.data <= data_iteracao.data):     
                # Verificar se se trata de compra ou venda
                if operacao.tipo_operacao == 'C':
                    if (operacao.data == data_iteracao.data):
                        operacao.total = operacao.quantidade
                    # Calcular o valor atualizado para cada operacao
                    operacao.atual = calcular_valor_atualizado_com_taxa_di(taxa_do_dia, operacao.atual, operacao.taxa)
                    # Arredondar na última iteração
                    if (data_iteracao.data == data_final):
                        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                          
                elif operacao.tipo_operacao == 'V':
                    if (operacao.data == data_iteracao.data):
                        print operacao
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
    
    return TemplateResponse(request, 'lci_lca/painel.html', {'operacoes': operacoes, 'dados': dados})

@adiciona_titulo_descricao('Sobre Letras de Crédito', 'Detalha o que são Letras de Crédito')
def sobre(request):
    if request.is_ajax():
        try:
            aplicacao = Decimal(request.GET.get('qtd').replace('.', '').replace(',', '.'))
            filtros_simulador = {'periodo': Decimal(request.GET.get('periodo')), 'percentual_indice': Decimal(request.GET.get('percentual_indice').replace('.', '').replace(',', '.')), \
                             'tipo': request.GET.get('tipo'), 'aplicacao': aplicacao}
        except:
            return HttpResponse(json.dumps({'sucesso': False, 'mensagem': u'Variáveis de entrada inválidas'}), content_type = "application/json") 
        
        graf_simulador = [[str(calendar.timegm(data.timetuple()) * 1000), float(valor_lci_lca)] for data, valor_lci_lca in simulador_lci_lca(filtros_simulador)]
        return HttpResponse(json.dumps({'sucesso': True, 'graf_simulador': graf_simulador}), content_type = "application/json") 
    else:
        data_atual = datetime.date.today()
        historico_di = HistoricoTaxaDI.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3)).order_by('data')
        graf_historico_di = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(valor_historico.taxa)] for valor_historico in historico_di]
        
        historico_ipca = HistoricoIPCA.objects.filter(data_inicio__year__gte=(data_atual.year-3)).order_by('data_inicio')
        graf_historico_ipca = [[str(calendar.timegm(valor_historico.data_inicio.timetuple()) * 1000), float(valor_historico.valor * 100)] for valor_historico in historico_ipca]
        
        if request.user.is_authenticated():
            total_atual = sum(calcular_valor_lci_lca_ate_dia(request.user.investidor).values())
        else:
            total_atual = 0
        
        filtros_simulador = {'periodo': Decimal(365), 'percentual_indice': Decimal(85), 'tipo': 'POS', 'aplicacao': Decimal(1000)}
        
        graf_simulador = [[str(calendar.timegm(data.timetuple()) * 1000), float(valor_lci_lca)] for data, valor_lci_lca in simulador_lci_lca(filtros_simulador)]
        
        return TemplateResponse(request, 'lci_lca/sobre.html', {'graf_historico_di': graf_historico_di, 'graf_historico_ipca': graf_historico_ipca,
                                                           'total_atual': total_atual, 'filtros_simulador': filtros_simulador,
                                                           'graf_simulador': graf_simulador})