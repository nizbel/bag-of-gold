# -*- coding: utf-8 -*-

from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoLetraCambioFormSet
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLetraCambio, Divisao
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.models.td import HistoricoIPCA
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa_di, \
    calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import calcular_iof_regressivo, \
    qtd_dias_uteis_no_periodo, calcular_iof_e_ir_longo_prazo
from bagogold.lc.forms import OperacaoLetraCambioForm, \
    HistoricoPorcentagemLetraCambioForm, LetraCambioForm, HistoricoCarenciaLetraCambioForm, \
    HistoricoVencimentoLetraCambioForm
from bagogold.lc.models import OperacaoLetraCambio, HistoricoPorcentagemLetraCambio, \
    LetraCambio, HistoricoCarenciaLetraCambio, OperacaoVendaLetraCambio, \
    HistoricoVencimentoLetraCambio
from bagogold.lc.utils import calcular_valor_lc_ate_dia, \
    buscar_operacoes_vigentes_ate_data, calcular_valor_atualizado_operacao_ate_dia, \
    calcular_valor_operacao_lc_ate_dia, calcular_valor_venda_lc
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
import calendar
import datetime

@login_required
@adiciona_titulo_descricao('Detalhar Letra de Câmbio', 'Detalhar Letra de Câmbio, incluindo histórico de carência e '
                                                'porcentagem de rendimento, além de dados da posição do investidor')
def detalhar_lc(request, lc_id):
    investidor = request.user.investidor
    
    lc = get_object_or_404(LetraCambio, id=lc_id)
    if lc.investidor != investidor:
        raise PermissionDenied
    
    historico_porcentagem = HistoricoPorcentagemLetraCambio.objects.filter(lc=lc)
    historico_carencia = HistoricoCarenciaLetraCambio.objects.filter(lc=lc)
    historico_vencimento = HistoricoVencimentoLetraCambio.objects.filter(lc=lc)
    
    # Inserir dados do investimento
    lc.carencia_atual = lc.carencia_atual()
    lc.porcentagem_atual = lc.porcentagem_atual()
    
    # Preparar estatísticas zeradas
    lc.total_investido = Decimal(0)
    lc.saldo_atual = Decimal(0)
    lc.total_ir = Decimal(0)
    lc.total_iof = Decimal(0)
    lc.lucro = Decimal(0)
    lc.lucro_percentual = Decimal(0)
    
    operacoes = OperacaoLetraCambio.objects.filter(lc=lc).order_by('data')
    # Contar total de operações já realizadas 
    lc.total_operacoes = len(operacoes)
    # Remover operacoes totalmente vendidas
    operacoes = [operacao for operacao in operacoes if operacao.tipo_operacao == 'C' and operacao.qtd_disponivel_venda() > 0]
    if operacoes:
        historico_di = HistoricoTaxaDI.objects.filter(data__range=[operacoes[0].data, datetime.date.today()])
        for operacao in operacoes:
            # Total investido
            lc.total_investido += operacao.qtd_disponivel_venda()
            
            # Saldo atual
            taxas = historico_di.filter(data__gte=operacao.data).values('taxa').annotate(qtd_dias=Count('taxa'))
            taxas_dos_dias = {}
            for taxa in taxas:
                taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.qtd_disponivel_venda(), operacao.porcentagem())
            lc.saldo_atual += operacao.atual
            
            # Calcular impostos
            qtd_dias = (datetime.date.today() - operacao.data).days
            # IOF
            operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.qtd_disponivel_venda())
            # IR
            if qtd_dias <= 180:
                operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.qtd_disponivel_venda() - operacao.iof)
            elif qtd_dias <= 360:
                operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.qtd_disponivel_venda() - operacao.iof)
            elif qtd_dias <= 720:
                operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.qtd_disponivel_venda() - operacao.iof)
            else: 
                operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.qtd_disponivel_venda() - operacao.iof)
            lc.total_ir += operacao.imposto_renda
            lc.total_iof += operacao.iof
    
        # Pegar outras estatísticas
        str_auxiliar = str(lc.saldo_atual.quantize(Decimal('.0001')))
        lc.saldo_atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        
        lc.lucro = lc.saldo_atual - lc.total_investido
        lc.lucro_percentual = lc.lucro / lc.total_investido * 100
    try: 
        lc.dias_prox_vencimento = (min(operacao.data + datetime.timedelta(days=operacao.vencimento()) for operacao in operacoes if \
                                            operacao.tipo_operacao == 'C' and \
                                            (operacao.data + datetime.timedelta(days=operacao.vencimento())) > datetime.date.today()) - datetime.date.today()).days
    except ValueError:
        lc.dias_prox_vencimento = 0
    
    
    return TemplateResponse(request, 'lc/detalhar_lc.html', {'lc': lc, 'historico_porcentagem': historico_porcentagem,
                                                                       'historico_carencia': historico_carencia, 'historico_vencimento': historico_vencimento})

@login_required
@adiciona_titulo_descricao('Editar Letra de Câmbio', 'Editar os dados de uma Letra de Câmbio')
def editar_lc(request, lc_id):
    investidor = request.user.investidor
    lc = get_object_or_404(LetraCambio, id=lc_id)
    
    if lc.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_lc = LetraCambioForm(request.POST, instance=lc)
            
            if form_lc.is_valid():
                lc.save()
                messages.success(request, 'Letra de Câmbio editada com sucesso')
                return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': lc.id}))
                
        # TODO verificar o que pode acontecer na exclusão
        elif request.POST.get("delete"):
            if OperacaoLetraCambio.objects.filter(investimento=lc).exists():
                messages.error(request, 'Não é possível excluir o %s pois existem operações cadastradas' % (lc.descricao_tipo()))
                return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': lc.id}))
            else:
                lc.delete()
                messages.success(request, 'Letra de Câmbio excluída com sucesso')
                return HttpResponseRedirect(reverse('lc:listar_lc'))
 
    else:
        form_lc = LetraCambioForm(instance=lc)
            
    return TemplateResponse(request, 'lc/editar_lc.html', {'form_lc': form_lc, 'lc': lc})  
    
@login_required
@adiciona_titulo_descricao('Editar registro de carência de uma Letra de Câmbio', 'Alterar um registro de carência no '
                                                                        'histórico da Letra de Câmbio')
def editar_historico_carencia(request, historico_carencia_id):
    investidor = request.user.investidor
    historico_carencia = get_object_or_404(HistoricoCarenciaLetraCambio, id=historico_carencia_id)
    
    if historico_carencia.lc.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_carencia.data is None:
                inicial = True
                form_historico_carencia = HistoricoCarenciaLetraCambioForm(request.POST, instance=historico_carencia, lc=historico_carencia.lc, \
                                                                       investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_carencia = HistoricoCarenciaLetraCambioForm(request.POST, instance=historico_carencia, lc=historico_carencia.lc, \
                                                                       investidor=investidor)
            if form_historico_carencia.is_valid():
                historico_carencia.save()
                messages.success(request, 'Histórico de carência editado com sucesso')
                return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': historico_carencia.lc.id}))
            
            for erro in [erro for erro in form_historico_carencia.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_carencia.data is None:
                messages.error(request, 'Valor inicial de carência não pode ser excluído')
                return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': historico_carencia.lc.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            lc = historico_carencia.lc
            historico_carencia.delete()
            messages.success(request, 'Histórico de carência excluído com sucesso')
            return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': lc.id}))
 
    else:
        if historico_carencia.data is None:
            inicial = True
            form_historico_carencia = HistoricoCarenciaLetraCambioForm(instance=historico_carencia, lc=historico_carencia.lc, \
                                                                   investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_carencia = HistoricoCarenciaLetraCambioForm(instance=historico_carencia, lc=historico_carencia.lc, \
                                                                   investidor=investidor)
            
    return TemplateResponse(request, 'lc/editar_historico_carencia.html', {'form_historico_carencia': form_historico_carencia, 'inicial': inicial}) 
    
@login_required
@adiciona_titulo_descricao('Editar registro de porcentagem de rendimento de uma Letra de Câmbio', 'Alterar um registro de porcentagem de rendimento no '
                                                                                         'histórico da Letra de Câmbio')
def editar_historico_porcentagem(request, historico_porcentagem_id):
    investidor = request.user.investidor
    historico_porcentagem = get_object_or_404(HistoricoPorcentagemLetraCambio, id=historico_porcentagem_id)
    
    if historico_porcentagem.lc.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_porcentagem.data is None:
                inicial = True
                form_historico_porcentagem = HistoricoPorcentagemLetraCambioForm(request.POST, instance=historico_porcentagem, lc=historico_porcentagem.lc, \
                                                                             investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_porcentagem = HistoricoPorcentagemLetraCambioForm(request.POST, instance=historico_porcentagem, lc=historico_porcentagem.lc, \
                                                                             investidor=investidor)
            if form_historico_porcentagem.is_valid():
                historico_porcentagem.save(force_update=True)
                messages.success(request, 'Histórico de porcentagem editado com sucesso')
                return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': historico_porcentagem.lc.id}))
                
            for erro in [erro for erro in form_historico_porcentagem.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_porcentagem.data is None:
                messages.error(request, 'Valor inicial de porcentagem não pode ser excluído')
                return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': historico_porcentagem.lc.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            lc = historico_porcentagem.lc
            historico_porcentagem.delete()
            messages.success(request, 'Histórico de porcentagem excluído com sucesso')
            return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': lc.id}))
 
    else:
        if historico_porcentagem.data is None:
            inicial = True
            form_historico_porcentagem = HistoricoPorcentagemLetraCambioForm(instance=historico_porcentagem, lc=historico_porcentagem.lc, \
                                                                         investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_porcentagem = HistoricoPorcentagemLetraCambioForm(instance=historico_porcentagem, lc=historico_porcentagem.lc, \
                                                                         investidor=investidor)
            
    return TemplateResponse(request, 'lc/editar_historico_porcentagem.html', {'form_historico_porcentagem': form_historico_porcentagem, 'inicial': inicial}) 
    
@login_required
@adiciona_titulo_descricao('Editar registro de vencimento de uma Letra de Câmbio', 'Alterar um registro de vencimento no '
                                                                        'histórico da Letra de Câmbio')
def editar_historico_vencimento(request, historico_vencimento_id):
    investidor = request.user.investidor
    historico_vencimento = get_object_or_404(HistoricoVencimentoLetraCambio, id=historico_vencimento_id)
    
    if historico_vencimento.lc.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_vencimento.data is None:
                inicial = True
                form_historico_vencimento = HistoricoVencimentoLetraCambioForm(request.POST, instance=historico_vencimento, lc=historico_vencimento.lc, \
                                                                       investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_vencimento = HistoricoVencimentoLetraCambioForm(request.POST, instance=historico_vencimento, lc=historico_vencimento.lc, \
                                                                       investidor=investidor)
            if form_historico_vencimento.is_valid():
                historico_vencimento.save()
                messages.success(request, 'Histórico de vencimento editado com sucesso')
                return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': historico_vencimento.lc.id}))
            
            for erro in [erro for erro in form_historico_vencimento.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_vencimento.data is None:
                messages.error(request, 'Valor inicial de vencimento não pode ser excluído')
                return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': historico_vencimento.lc.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            lc = historico_vencimento.lc
            historico_vencimento.delete()
            messages.success(request, 'Histórico de vencimento excluído com sucesso')
            return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': lc.id}))
 
    else:
        if historico_vencimento.data is None:
            inicial = True
            form_historico_vencimento = HistoricoVencimentoLetraCambioForm(instance=historico_vencimento, lc=historico_vencimento.lc, \
                                                                   investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_vencimento = HistoricoVencimentoLetraCambioForm(instance=historico_vencimento, lc=historico_vencimento.lc, \
                                                                   investidor=investidor)
            
    return TemplateResponse(request, 'lc/editar_historico_vencimento.html', {'form_historico_vencimento': form_historico_vencimento, 'inicial': inicial})     

@login_required
@adiciona_titulo_descricao('Editar operação em Letra de Câmbio', 'Alterar valores de uma operação de compra/venda em Letra de Câmbio')
def editar_operacao_lc(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_lc = get_object_or_404(OperacaoLetraCambio, id=operacao_id)
    if operacao_lc.investidor != investidor:
        raise PermissionDenied
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoLetraCambio, DivisaoOperacaoLetraCambio, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoLetraCambioFormSet)
    
    if request.method == 'POST':
        form_operacao_lc = OperacaoLetraCambioForm(request.POST, instance=operacao_lc, investidor=investidor)
        formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc, investidor=investidor) if varias_divisoes else None
        
        if request.POST.get("save"):
            if form_operacao_lc.is_valid():
                operacao_compra = form_operacao_lc.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_lc, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_lc.save()
                        if operacao_lc.tipo_operacao == 'V':
                            if not OperacaoVendaLetraCambio.objects.filter(operacao_venda=operacao_lc):
                                operacao_venda_lc = OperacaoVendaLetraCambio(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                                operacao_venda_lc.save()
                            else: 
                                operacao_venda_lc = OperacaoVendaLetraCambio.objects.get(operacao_venda=operacao_lc)
                                if operacao_venda_lc.operacao_compra != operacao_compra:
                                    operacao_venda_lc.operacao_compra = operacao_compra
                                    operacao_venda_lc.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação editada com sucesso')
                        return HttpResponseRedirect(reverse('lc:historico_lc'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                        
                else:
                    operacao_lc.save()
                    if operacao_lc.tipo_operacao == 'V':
                        if not OperacaoVendaLetraCambio.objects.filter(operacao_venda=operacao_lc):
                            operacao_venda_lc = OperacaoVendaLetraCambio(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                            operacao_venda_lc.save()
                        else: 
                            operacao_venda_lc = OperacaoVendaLetraCambio.objects.get(operacao_venda=operacao_lc)
                            if operacao_venda_lc.operacao_compra != operacao_compra:
                                operacao_venda_lc.operacao_compra = operacao_compra
                                operacao_venda_lc.save()
                    divisao_operacao = DivisaoOperacaoLetraCambio.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_lc)
                    divisao_operacao.quantidade = operacao_lc.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('lc:historico_lc'))
                
            for erro in [erro for erro in form_operacao_lc.non_field_errors()]:
                messages.error(request, erro)
#                         print '%s %s'  % (divisao_lc.quantidade, divisao_lc.divisao)
                
        elif request.POST.get("delete"):
            # Testa se operação a excluir não é uma operação de compra com vendas já registradas
            if not OperacaoVendaLetraCambio.objects.filter(operacao_compra=operacao_lc):
                divisao_lc = DivisaoOperacaoLetraCambio.objects.filter(operacao=operacao_lc)
                for divisao in divisao_lc:
                    divisao.delete()
                if operacao_lc.tipo_operacao == 'V':
                    OperacaoVendaLetraCambio.objects.get(operacao_venda=operacao_lc).delete()
                operacao_lc.delete()
                messages.success(request, 'Operação excluída com sucesso')
                return HttpResponseRedirect(reverse('lc:historico_lc'))
            else:
                messages.error(request, 'Não é possível excluir operação de compra que já tenha vendas registradas')
 
    else:
        form_operacao_lc = OperacaoLetraCambioForm(instance=operacao_lc, initial={'operacao_compra': operacao_lc.operacao_compra_relacionada(),}, \
                                                    investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=operacao_lc, investidor=investidor)
            
    return TemplateResponse(request, 'lc/editar_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})  

    
@adiciona_titulo_descricao('Histórico de Letras de Câmbio', 'Histórico de operações de compra/venda em Letras de Câmbio')
def historico(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'lc/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
     
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoLetraCambio.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data', '-tipo_operacao') 
    # Verifica se não há operações
    if not operacoes:
        return TemplateResponse(request, 'lc/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
     
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.taxa = operacao.porcentagem()
        operacao.atual = operacao.quantidade
        if operacao.tipo_operacao == 'C':
            operacao.qtd_vendida = 0
            operacao.tipo = 'Compra'
        else:
            operacao.tipo = 'Venda'
     
    total_investido = 0
    total_patrimonio = 0
     
    # Gráfico de acompanhamento de investidos vs patrimonio
    graf_investido_total = list()
    graf_patrimonio = list()
     
    # Guarda última data calculada
    ultima_data = operacoes[0].data
 
    for indice, operacao in enumerate(operacoes):
        # Alterar total investido
        if operacao.tipo_operacao == 'C':
            total_investido += operacao.quantidade
        else:
            total_investido -= operacao.quantidade
            # Preparar o valor atual e reiniciar valor da operação de compra
            # Valor atual
            operacao.atual = calcular_valor_venda_lc(operacao, True, True)
             
            # Buscar operação de compra relacionada para reiniciar
            indice_operacao_compra = operacao.operacao_compra_relacionada().id
            for indice_relacionada in xrange(indice):
                if operacoes[indice_relacionada].id == indice_operacao_compra:
                    operacoes[indice_relacionada].qtd_vendida += operacao.quantidade
                    operacoes[indice_relacionada].atual = operacoes[indice_relacionada].quantidade - operacoes[indice_relacionada].qtd_vendida
                    if operacoes[indice_relacionada].atual > 0:
                        # Atualizar o valor
                        operacoes[indice_relacionada].atual = calcular_valor_atualizado_operacao_ate_dia(operacoes[indice_relacionada].atual, operacoes[indice_relacionada].data, 
                                                                       ultima_data, operacoes[indice_relacionada], operacoes[indice_relacionada].atual)
                    break
             
        # Verifica se é última operação ou próxima operação ocorre na mesma data
        if indice + 1 == len(operacoes) or operacoes[indice + 1].data > operacao.data:
         
            # Calcular o valor atualizado do patrimonio
            total_patrimonio = 0
            
            for indice_atualizacao in xrange(indice+1):
                if operacoes[indice_atualizacao].tipo_operacao == 'C' and operacoes[indice_atualizacao].atual > 0:
                    # Pegar primeira data de valorização para a operação feita na data
                    primeira_data_valorizacao = max(operacoes[indice_atualizacao].data, ultima_data)
                    # Pegar última data de valorização
                    ultima_data_valorizacao = min(operacoes[indice_atualizacao].data_vencimento() - datetime.timedelta(days=1), operacao.data)
                    if ultima_data_valorizacao >= ultima_data:
                        # Calcular o valor atualizado para cada operacao
                        operacoes[indice_atualizacao].atual = calcular_valor_atualizado_operacao_ate_dia(operacoes[indice_atualizacao].atual, 
                                                                     primeira_data_valorizacao, ultima_data_valorizacao, operacoes[indice_atualizacao], 
                                                                     operacoes[indice_atualizacao].atual)
                 
                    total_patrimonio += operacoes[indice_atualizacao].atual
                         
            # Preencher gráficos
            graf_investido_total += [[str(calendar.timegm(operacao.data.timetuple()) * 1000), float(total_investido)]]
            graf_patrimonio += [[str(calendar.timegm(operacao.data.timetuple()) * 1000), float(total_patrimonio)]]
             
            # Guardar data como última data usada para calcular valor atualizado
            ultima_data = operacao.data + datetime.timedelta(days=1)
         
    # Pegar data final, nivelar todas as operações para essa data
    data_final = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
     
    if data_final > ultima_data:
        # Adicionar o restante de período (última operação até data atual)
        total_patrimonio = 0
        for operacao in operacoes:
            if operacao.tipo_operacao == 'C' and operacao.atual > 0:
                ultima_data_valorizacao = min(operacao.data_vencimento() - datetime.timedelta(days=1), data_final)
                if ultima_data_valorizacao >= ultima_data:
                    # Calcular o valor atualizado para cada operacao
                    operacao.atual = calcular_valor_atualizado_operacao_ate_dia(operacao.atual, ultima_data, ultima_data_valorizacao, operacao, 
                                                                                operacao.quantidade)
                # Formatar
                str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
             
                total_patrimonio += operacao.atual
             
        # Preencher gráficos
        graf_investido_total += [[str(calendar.timegm(datetime.date.today().timetuple()) * 1000), float(total_investido)]]
        graf_patrimonio += [[str(calendar.timegm(datetime.date.today().timetuple()) * 1000), float(total_patrimonio)]]
        
    dados = {}
    dados['total_investido'] = total_investido
    dados['patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio - total_investido
    dados['lucro_percentual'] = (total_patrimonio - total_investido) / total_investido * 100
    
    return TemplateResponse(request, 'lc/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_investido_total': graf_investido_total, 'graf_patrimonio': graf_patrimonio})
    

@login_required
@adiciona_titulo_descricao('Inserir Letra de Câmbio', 'Inserir uma nova Letra de Câmbio nas opções do investidor')
def inserir_lc(request):
    investidor = request.user.investidor
    
    # Preparar formsets 
    PorcentagemFormSet = inlineformset_factory(LetraCambio, HistoricoPorcentagemLetraCambio, fields=('porcentagem',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True)
    CarenciaFormSet = inlineformset_factory(LetraCambio, HistoricoCarenciaLetraCambio, fields=('carencia',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True, labels = {'carencia': 'Período de carência',})
    VencimentoFormSet = inlineformset_factory(LetraCambio, HistoricoVencimentoLetraCambio, fields=('vencimento',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True, labels = {'vencimento': 'Período de vencimento',})
    
    if request.method == 'POST':
        form_lc = LetraCambioForm(request.POST)
        formset_porcentagem = PorcentagemFormSet(request.POST)
        formset_carencia = CarenciaFormSet(request.POST)
        formset_vencimento = VencimentoFormSet(request.POST)
        if form_lc.is_valid():
            lc = form_lc.save(commit=False)
            lc.investidor = investidor
            formset_porcentagem = PorcentagemFormSet(request.POST, instance=lc)
            formset_porcentagem.forms[0].empty_permitted=False
            formset_carencia = CarenciaFormSet(request.POST, instance=lc)
            formset_carencia.forms[0].empty_permitted=False
            formset_vencimento = VencimentoFormSet(request.POST, instance=lc)
            formset_vencimento.forms[0].empty_permitted=False
            
            if formset_porcentagem.is_valid():
                if formset_vencimento.is_valid():
                    if formset_carencia.is_valid():
                        try:
                            if formset_vencimento.forms[0].cleaned_data['vencimento'] < formset_carencia.forms[0].cleaned_data['carencia']:
                                raise ValidationError('Período de carência não pode ser maior que período de vencimento')
                            with transaction.atomic():
                                lc.save()
                                formset_carencia.save()
                                formset_porcentagem.save()
                                formset_vencimento.save()
                            messages.success(request, 'Letra de Câmbio incluída com sucesso')
                            return HttpResponseRedirect(reverse('lc:listar_lc'))
                        # Capturar erros oriundos da hora de salvar os objetos
                        except Exception as erro:
                            messages.error(request, erro.message)
                            return TemplateResponse(request, 'lc/inserir_lc.html', {'form_lc': form_lc, 'formset_porcentagem': formset_porcentagem,
                                                              'formset_carencia': formset_carencia, 'formset_vencimento': formset_vencimento})
                            
                
        for erro in [erro for erro in form_lc.non_field_errors()]:
            messages.error(request, erro)
        for erro in formset_porcentagem.non_form_errors():
            messages.error(request, erro)
        for erro in formset_carencia.non_form_errors():
            messages.error(request, erro)
        for erro in formset_vencimento.non_form_errors():
            messages.error(request, erro)
            
    else:
        form_lc = LetraCambioForm()
        formset_porcentagem = PorcentagemFormSet()
        formset_carencia = CarenciaFormSet()
        formset_vencimento = VencimentoFormSet()
    return TemplateResponse(request, 'lc/inserir_lc.html', {'form_lc': form_lc, 'formset_porcentagem': formset_porcentagem,
                                                              'formset_carencia': formset_carencia, 'formset_vencimento': formset_vencimento})

@login_required
@adiciona_titulo_descricao('Inserir registro de carência para uma Letra de Câmbio', 'Inserir registro de alteração de carência ao histórico de '
                                                                           'uma Letra de Câmbio')
def inserir_historico_carencia_lc(request, lc_id):
    investidor = request.user.investidor
    lc = get_object_or_404(LetraCambio, id=lc_id)
    
    if lc.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoCarenciaLetraCambioForm(request.POST, initial={'lc': lc.id}, lc=lc, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de carência para %s alterado com sucesso' % historico.lc)
            return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': lc.id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoCarenciaLetraCambioForm(initial={'lc': lc.id}, lc=lc, investidor=investidor)
            
    return TemplateResponse(request, 'lc/inserir_historico_carencia_lc.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir registro de porcentagem para uma Letra de Câmbio', 'Inserir registro de alteração de porcentagem de rendimento '
                                                                              'ao histórico de uma Letra de Câmbio')
def inserir_historico_porcentagem_lc(request, lc_id):
    investidor = request.user.investidor
    lc = get_object_or_404(LetraCambio, id=lc_id)
    
    if lc.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoPorcentagemLetraCambioForm(request.POST, initial={'lc': lc.id}, lc=lc, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de porcentagem de rendimento para %s alterado com sucesso' % historico.lc)
            return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': lc.id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoPorcentagemLetraCambioForm(initial={'lc': lc.id}, lc=lc, investidor=investidor)
            
    return TemplateResponse(request, 'lc/inserir_historico_porcentagem_lc.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir registro de vencimento para uma Letra de Câmbio', 'Inserir registro de alteração de vencimento ao histórico de '
                                                                           'uma Letra de Câmbio')
def inserir_historico_vencimento_lc(request, lc_id):
    investidor = request.user.investidor
    lc = get_object_or_404(LetraCambio, id=lc_id)
    
    if lc.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoVencimentoLetraCambioForm(request.POST, initial={'lc': lc.id}, lc=lc, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de período de vencimento para %s alterado com sucesso' % historico.lc)
            return HttpResponseRedirect(reverse('lc:detalhar_lc', kwargs={'lc_id': lc.id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoVencimentoLetraCambioForm(initial={'lc': lc.id}, lc=lc, investidor=investidor)
            
    return TemplateResponse(request, 'lc/inserir_historico_vencimento_lc.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir operação em Letra de Câmbio', 'Inserir registro de operação de compra/venda em Letra de Câmbio')
def inserir_operacao_lc(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoLetraCambioFormSet = inlineformset_factory(OperacaoLetraCambio, DivisaoOperacaoLetraCambio, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoLetraCambioFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_operacao_lc = OperacaoLetraCambioForm(request.POST, investidor=investidor)
        formset_divisao_lc = DivisaoLetraCambioFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar Letra de Câmbio
        if form_operacao_lc.is_valid():
            operacao_lc = form_operacao_lc.save(commit=False)
            operacao_lc.investidor = investidor
            operacao_compra = form_operacao_lc.cleaned_data['operacao_compra']
            formset_divisao_lc = DivisaoLetraCambioFormSet(request.POST, instance=operacao_lc, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                
            # Validar em caso de venda
            if form_operacao_lc.cleaned_data['tipo_operacao'] == 'V':
                operacao_compra = form_operacao_lc.cleaned_data['operacao_compra']
                # Caso de venda total da letra de cambio
                if form_operacao_lc.cleaned_data['quantidade'] == operacao_compra.quantidade:
                    # Desconsiderar divisões inseridas, copiar da operação de compra
                    operacao_lc.save()
                    for divisao_lc in DivisaoOperacaoLetraCambio.objects.filter(operacao=operacao_compra):
                        divisao_lc_venda = DivisaoOperacaoLetraCambio(quantidade=divisao_lc.quantidade, divisao=divisao_lc.divisao, \
                                                             operacao=operacao_lc)
                        divisao_lc_venda.save()
                    operacao_venda_lc = OperacaoVendaLetraCambio(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                    operacao_venda_lc.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('lc:historico_lc'))
                # Vendas parciais
                else:
                    # Verificar se varias divisões
                    if varias_divisoes:
                        if formset_divisao_lc.is_valid():
                            operacao_lc.save()
                            formset_divisao_lc.save()
                            operacao_venda_lc = OperacaoVendaLetraCambio(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                            operacao_venda_lc.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('lc:historico_lc'))
                        for erro in formset_divisao_lc.non_form_errors():
                            messages.error(request, erro)
                                
                    else:
                        operacao_lc.save()
                        divisao_operacao = DivisaoOperacaoLetraCambio(operacao=operacao_lc, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_lc.quantidade)
                        divisao_operacao.save()
                        operacao_venda_lc = OperacaoVendaLetraCambio(operacao_compra=operacao_compra, operacao_venda=operacao_lc)
                        operacao_venda_lc.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('lc:historico_lc'))
            
            # Compra
            else:
                # Verificar se várias divisões
                if varias_divisoes:
                    if formset_divisao_lc.is_valid():
                        operacao_lc.save()
                        formset_divisao_lc.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('lc:historico_lc'))
                    for erro in formset_divisao_lc.non_form_errors():
                        messages.error(request, erro)
                                
                else:
                    operacao_lc.save()
                    divisao_operacao = DivisaoOperacaoLetraCambio(operacao=operacao_lc, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_lc.quantidade)
                    divisao_operacao.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('lc:historico_lc'))
                    
        for erro in [erro for erro in form_operacao_lc.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_lc.quantidade, divisao_lc.divisao)
                
    else:
        form_operacao_lc = OperacaoLetraCambioForm(investidor=investidor)
        formset_divisao_lc = DivisaoLetraCambioFormSet(investidor=investidor)
    return TemplateResponse(request, 'lc/inserir_operacao_lc.html', {'form_operacao_lc': form_operacao_lc, 'formset_divisao': formset_divisao_lc,
                                                                        'varias_divisoes': varias_divisoes})

@adiciona_titulo_descricao('Listar Letras de Câmbio', 'Lista de Letras de Câmbio cadastrados pelo investidor')
def listar_lc(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'lc/listar_lc.html', {'lc': list()})
    
    lc = LetraCambio.objects.filter(investidor=investidor)
    
    for investimento in lc:
        # Preparar o valor mais atual para carência
        investimento.carencia_atual = investimento.carencia_atual()
        # Preparar o valor mais atual de rendimento
        investimento.rendimento_atual = investimento.porcentagem_atual()
        
        if investimento.tipo_rendimento == LetraCambio.LC_PREFIXADO:
            investimento.str_tipo_rendimento = 'Prefixado'
        elif investimento.tipo_rendimento in [LetraCambio.LC_DI, LetraCambio.LC_IPCA]:
            investimento.str_tipo_rendimento = 'Pós-fixado'
        
    return TemplateResponse(request, 'lc/listar_lc.html', {'lc': lc})

@adiciona_titulo_descricao('Painel de Letras de Câmbio', 'Posição atual do investidor em Letras de Câmbio')
def painel(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'lc/painel.html', {'operacoes': list(), 'dados': {}})
         
    # Processa primeiro operações de venda (V), depois compra (C)
#     operacoes = OperacaoLetraCambio.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
#     print operacoes, len(operacoes)
     
    operacoes = buscar_operacoes_vigentes_ate_data(investidor).order_by('data') 
    if not operacoes:
        dados = {}
        dados['total_atual'] = Decimal(0)
        dados['total_ir'] = Decimal(0)
        dados['total_iof'] = Decimal(0)
        dados['total_ganho_prox_dia'] = Decimal(0)
        return TemplateResponse(request, 'lc/painel.html', {'operacoes': {}, 'dados': dados})
     
    # Pegar data final, nivelar todas as operações para essa data
    data_final = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
     
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.quantidade = operacao.qtd_disponivel_venda
        operacao.taxa = operacao.porcentagem()
        data_final_valorizacao = min(data_final, operacao.data_vencimento() - datetime.timedelta(days=1))

        # Calcular o valor atualizado
        operacao.atual = calcular_valor_operacao_lc_ate_dia(operacao, data_final_valorizacao)
        
    # Remover operações que não estejam mais rendendo
    operacoes = [operacao for operacao in operacoes if (operacao.atual > 0 and operacao.tipo_operacao == 'C')]
     
    total_atual = 0
    total_ir = 0
    total_iof = 0
    total_ganho_prox_dia = 0
    total_vencimento = 0
     
    ultima_taxa_di = HistoricoTaxaDI.objects.filter().order_by('-data')[0].taxa
     
    for operacao in operacoes:
        # Calcular o ganho no dia seguinte
        if data_final < operacao.data_vencimento():
            # Se prefixado apenas pegar rendimento de 1 dia
            if operacao.lc.eh_prefixado():
                operacao.ganho_prox_dia = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa) - operacao.atual
            elif operacao.lc.tipo_rendimento == LetraCambio.LC_DI:
                # Considerar rendimento do dia anterior
                operacao.ganho_prox_dia = calcular_valor_atualizado_com_taxa_di(ultima_taxa_di, operacao.atual, operacao.taxa) - operacao.atual
            # Formatar
            str_auxiliar = str(operacao.ganho_prox_dia.quantize(Decimal('.0001')))
            operacao.ganho_prox_dia = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            total_ganho_prox_dia += operacao.ganho_prox_dia
        else:
            operacao.ganho_prox_dia = Decimal('0.00')
         
        # Calcular impostos
        operacao.iof, operacao.imposto_renda = calcular_iof_e_ir_longo_prazo(operacao.atual - operacao.quantidade, 
                                                 (datetime.date.today() - operacao.data).days)
         
        # Valor líquido
        operacao.valor_liquido = operacao.atual - operacao.imposto_renda - operacao.iof
         
        # Estimativa para o valor do investimento na data de vencimento
        if data_final < operacao.data_vencimento():
            qtd_dias_uteis_ate_vencimento = qtd_dias_uteis_no_periodo(data_final + datetime.timedelta(days=1), operacao.data_vencimento())
            # Se prefixado apenas pegar rendimento de 1 dia
            if operacao.lc.eh_prefixado():
                operacao.valor_vencimento = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa, qtd_dias_uteis_ate_vencimento)
            elif operacao.lc.tipo_rendimento == LetraCambio.LC_DI:
                # Considerar rendimento do dia anterior
                operacao.valor_vencimento = calcular_valor_atualizado_com_taxas_di({HistoricoTaxaDI.objects.get(data=data_final).taxa: qtd_dias_uteis_ate_vencimento},
                                                     operacao.atual, operacao.taxa)
            str_auxiliar = str(operacao.valor_vencimento.quantize(Decimal('.0001')))
            operacao.valor_vencimento = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        else:
            operacao.valor_vencimento = operacao.atual
         
        total_atual += operacao.atual
        total_ir += operacao.imposto_renda
        total_iof += operacao.iof
        total_vencimento += operacao.valor_vencimento
     
    # Popular dados
    dados = {}
    dados['data_di_mais_recente'] = data_final
    dados['total_atual'] = total_atual
    dados['total_ir'] = total_ir
    dados['total_iof'] = total_iof
    dados['total_liquido'] = total_atual - total_ir - total_iof
    dados['total_ganho_prox_dia'] = total_ganho_prox_dia
    dados['total_vencimento'] = total_vencimento
     
    return TemplateResponse(request, 'lc/painel.html', {'operacoes': operacoes, 'dados': dados})

@adiciona_titulo_descricao('Sobre Letras de Câmbio', 'Detalha o que são Letras de Câmbio')
def sobre(request):
    data_atual = datetime.date.today()
    historico_di = HistoricoTaxaDI.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3))
    graf_historico_di = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(valor_historico.taxa)] for valor_historico in historico_di]
    
    historico_ipca = HistoricoIPCA.objects.filter(ano__gte=(data_atual.year-3)).exclude(mes__lt=data_atual.month, ano=data_atual.year-3)
    graf_historico_ipca = [[str(calendar.timegm(valor_historico.data().timetuple()) * 1000), float(valor_historico.valor)] for valor_historico in historico_ipca]
    
    if request.user.is_authenticated():
        total_atual = sum(calcular_valor_lc_ate_dia(request.user.investidor).values())
    else:
        total_atual = 0
    
    return TemplateResponse(request, 'lc/sobre.html', {'graf_historico_di': graf_historico_di, 'graf_historico_ipca': graf_historico_ipca,
                                                            'total_atual': total_atual})