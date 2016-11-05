# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.divisoes import \
    DivisaoOperacaoFundoInvestimentoFormSet
from bagogold.bagogold.forms.fundo_investimento import \
    OperacaoFundoInvestimentoForm, FundoInvestimentoForm, \
    HistoricoCarenciaFundoInvestimentoForm, HistoricoValorCotasForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLC, \
    DivisaoOperacaoFundoInvestimento, Divisao
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento, FundoInvestimento, HistoricoCarenciaFundoInvestimento, \
    HistoricoValorCotas
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.utils.fundo_investimento import \
    calcular_qtd_cotas_ate_dia_por_fundo
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa
from bagogold.bagogold.utils.misc import calcular_iof_regressivo
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import calendar
import datetime

@login_required
def adicionar_valor_cota_historico(request):
    investidor = request.user.investidor
    
    if request.method == 'POST':
        form_historico_valor_cota = HistoricoValorCotasForm(request.POST, investidor=investidor)
        if form_historico_valor_cota.is_valid():
            form_historico_valor_cota.save()
            return HttpResponseRedirect(reverse('listar_fundo_investimento'))
        
    else:
        form_historico_valor_cota = HistoricoValorCotasForm(investidor=investidor)
    return TemplateResponse(request, 'fundo_investimento/adicionar_valor_cota_historico.html', {'form_historico_valor_cota': form_historico_valor_cota}) 

@login_required
def editar_operacao_fundo_investimento(request, id):
    investidor = request.user.investidor
    
    operacao_fundo_investimento = OperacaoFundoInvestimento.objects.get(pk=id)
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if operacao_fundo_investimento.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoFundoInvestimento, DivisaoOperacaoFundoInvestimento, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoFundoInvestimentoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(request.POST, instance=operacao_fundo_investimento, investidor=investidor)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_fundo_investimento, investidor=investidor) if varias_divisoes else None
            
            if form_operacao_fundo_investimento.is_valid():
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_fundo_investimento.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação editada com sucesso')
                        return HttpResponseRedirect(reverse('historico_fundo_investimento'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                        
                else:
                    operacao_fundo_investimento.save()
                    divisao_operacao = DivisaoOperacaoFundoInvestimento.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_fundo_investimento)
                    divisao_operacao.quantidade = operacao_fundo_investimento.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('historico_fundo_investimento'))
            for erros in form_operacao_fundo_investimento.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
        elif request.POST.get("delete"):
            # Verifica se, em caso de compra, a quantidade de cotas do investidor não fica negativa
            if operacao_fundo_investimento.tipo_operacao == 'C' and calcular_qtd_cotas_ate_dia_por_fundo(investidor, operacao_fundo_investimento.fundo_investimento.id, datetime.date.today()) - operacao_fundo_investimento.quantidade < 0:
                messages.error(request, 'Operação de compra não pode ser apagada pois quantidade atual para o fundo %s seria negativa' % (operacao_fundo_investimento.fundo_investimento))
            else:
                divisao_fundo_investimento = DivisaoOperacaoFundoInvestimento.objects.filter(operacao=operacao_fundo_investimento)
                for divisao in divisao_fundo_investimento:
                    divisao.delete()
                operacao_fundo_investimento.delete()
                messages.success(request, 'Operação apagada com sucesso')
                return HttpResponseRedirect(reverse('historico_td'))
 
    else:
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(instance=operacao_fundo_investimento, investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=operacao_fundo_investimento, investidor=investidor)
            
    return TemplateResponse(request, 'fundo_investimento/editar_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, 'formset_divisao': formset_divisao, \
                                                                                             'varias_divisoes': varias_divisoes})  

    
@login_required
def historico(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data') 
    # Se investidor não tiver operações, retornar vazio
    if not operacoes:
        return TemplateResponse(request, 'fundo_investimento/historico.html', {'dados': {})
    # Prepara o campo valor atual
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
        else:
            operacao.tipo = 'Venda'
            
    
    total_gasto = 0
    total_patrimonio = 0
    # Guarda quantidade de cotas
    fundos_investimento = {}
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    # Adicionar primeira data com valor 0
    graf_gasto_total = list()
    graf_patrimonio = list()

    for operacao in operacoes:   
        total_patrimonio = 0  
        
        if operacao.fundo_investimento not in fundos_investimento.keys():
            fundos_investimento[operacao.fundo_investimento] = operacao.fundo_investimento
            fundos_investimento[operacao.fundo_investimento].qtd_cotas = 0
            fundos_investimento[operacao.fundo_investimento].valor_cotas = 0
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            operacao.valor_cota = operacao.valor / operacao.quantidade
            total_gasto += operacao.valor
            fundos_investimento[operacao.fundo_investimento].qtd_cotas += operacao.quantidade
            fundos_investimento[operacao.fundo_investimento].valor_cotas = (operacao.valor / operacao.quantidade)
                
        elif operacao.tipo_operacao == 'V':
            total_gasto -= operacao.valor
            fundos_investimento[operacao.fundo_investimento].qtd_cotas -= operacao.quantidade
            fundos_investimento[operacao.fundo_investimento].valor_cotas = (operacao.valor / operacao.quantidade)
        
        for fundo in fundos_investimento:
            total_patrimonio += (fundo.valor_cotas * fundo.qtd_cotas)
            
        # Formatar data para inserir nos gráficos
        data_formatada = str(calendar.timegm(operacao.data.timetuple()) * 1000)    
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_gasto_total) > 0 and graf_gasto_total[-1][0] == data_formatada:
            graf_gasto_total[len(graf_gasto_total)-1][1] = float(total_gasto)
        else:
            graf_gasto_total += [[data_formatada, float(total_gasto)]]
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
            graf_patrimonio[len(graf_patrimonio)-1][1] = float(total_patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(total_patrimonio)]]
        
    # Adicionar data atual
    # Formatar data para inserir nos gráficos
    data_formatada = str(calendar.timegm(datetime.date.today().timetuple()) * 1000)    
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_gasto_total) > 0 and graf_gasto_total[-1][0] == data_formatada:
        graf_gasto_total[len(graf_gasto_total)-1][1] = float(total_gasto)
    else:
        graf_gasto_total += [[data_formatada, float(total_gasto)]]
     
    total_patrimonio = 0  
    # Calcular patrimônio atual
    for fundo in fundos_investimento:
        fundo.data_ultima_operacao = operacoes.filter(fundo_investimento=fundo).order_by('-data')[0].data
        historico_cotas = HistoricoValorCotas.objects.filter(fundo_investimento=fundo, data__gt=fundo.data_ultima_operacao).order_by('-data')
        if historico_cotas:
            total_patrimonio += (fundo.qtd_cotas * historico_cotas[0].valor_cota)
        else:
            total_patrimonio += (fundo.valor_cotas * fundo.qtd_cotas)
    
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
        graf_patrimonio[len(graf_patrimonio)-1][1] = float(total_patrimonio)
    else:
        graf_patrimonio += [[data_formatada, float(total_patrimonio)]]
    
    dados = {}
    dados['total_gasto'] = total_gasto
    dados['patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio - total_gasto
    dados['lucro_percentual'] = (total_patrimonio - total_gasto) / total_gasto * 100
    
    return TemplateResponse(request, 'fundo_investimento/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio})
    

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
                        return TemplateResponse(request, 'fundo_investimento/inserir_fundo_investimento.html', {'form_fundo_investimento': form_fundo_investimento,
                                                          'formset_carencia': formset_carencia})
                            
                    return HttpResponseRedirect(reverse('listar_fundo_investimento'))
            for erros in form_fundo_investimento.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
            for erro in formset_carencia.non_form_errors():
                messages.error(request, erro)
            return TemplateResponse(request, 'fundo_investimento/inserir_fundo_investimento.html', {'form_fundo_investimento': form_fundo_investimento,
                                                              'formset_carencia': formset_carencia})
    else:
        form_fundo_investimento = FundoInvestimentoForm()
        formset_carencia = CarenciaFormSet()
    return TemplateResponse(request, 'fundo_investimento/inserir_fundo_investimento.html', {'form_fundo_investimento': form_fundo_investimento,
                                                              'formset_carencia': formset_carencia})

@login_required
def inserir_operacao_fundo_investimento(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoFundoInvestimentoFormSet = inlineformset_factory(OperacaoFundoInvestimento, DivisaoOperacaoFundoInvestimento, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoFundoInvestimentoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(request.POST, investidor=investidor)
        formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar Fundo de Investimento
        if form_operacao_fundo_investimento.is_valid():
            operacao_fundo_investimento = form_operacao_fundo_investimento.save(commit=False)
            operacao_fundo_investimento.investidor = investidor
            
            # Testar se várias divisões
            if varias_divisoes:
                formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(request.POST, instance=operacao_fundo_investimento, investidor=investidor)
                if formset_divisao_fundo_investimento.is_valid():
                    operacao_fundo_investimento.save()
                    formset_divisao_fundo_investimento.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('historico_fundo_investimento'))
                for erro in formset_divisao_fundo_investimento.non_form_errors():
                    messages.error(request, erro)
            else:
                operacao_fundo_investimento.save()
                divisao_operacao = DivisaoOperacaoFundoInvestimento(operacao=operacao_fundo_investimento, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_fundo_investimento.quantidade)
                divisao_operacao.save()
                messages.success(request, 'Operação inserida com sucesso')
                return HttpResponseRedirect(reverse('historico_fundo_investimento'))
            
        for erros in form_operacao_fundo_investimento.errors.values():
            for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                messages.error(request, erro.message)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(investidor=investidor)
        formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(investidor=investidor)
    return TemplateResponse(request, 'fundo_investimento/inserir_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, \
                                                                                              'formset_divisao_fundo_investimento': formset_divisao_fundo_investimento, 'varias_divisoes': varias_divisoes})

@login_required
def listar_fundo_investimento(request):
    investidor = request.user.investidor
    fundos_investimento = FundoInvestimento.objects.filter(investidor=investidor)
    
    for fundo in fundos_investimento:
        # Preparar o valor mais atual para carência
        fundo.carencia_atual = fundo.carencia_atual()
        # Preparar o valor mais atual de rendimento
        try:
            historico_mais_recente = HistoricoValorCotas.objects.filter(fundo_investimento=fundo).order_by('-data')[0]
            fundo.data_valor_cota = historico_mais_recente.data
            fundo.valor_cota = historico_mais_recente.valor_cota
        except:
            pass
        
        # Limitar descrição
        if len(fundo.descricao) > 30:
            fundo.descricao = fundo.descricao[0:30] + '...'
        
        # Prazo
        if fundo.tipo_prazo == 'C':
            fundo.tipo_prazo = 'Curto'
        elif fundo.tipo_prazo == 'L':
            fundo.tipo_prazo = 'Longo'
        
    return TemplateResponse(request, 'fundo_investimento/listar_fundo_investimento.html', {'fundos_investimento': fundos_investimento})

@login_required
def modificar_carencia_fundo_investimento(request):
    investidor = request.user.investidor
    
    if request.method == 'POST':
        form = HistoricoCarenciaFundoInvestimentoForm(request.POST, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de carência para %s alterado com sucesso' % historico.letra_credito)
            return HttpResponseRedirect(reverse('historico_fundo_investimento'))
    else:
        form = HistoricoCarenciaFundoInvestimentoForm(investidor=investidor)
            
    return TemplateResponse(request, 'fundo_investimento/modificar_carencia_fundo_investimento.html', {'form': form})

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
            
    return TemplateResponse(request, 'fundo_investimento/modificar_porcentagem_fundo_investimento.html', {'form': form})

@login_required
def painel(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    # Se não há operações, retornar
    if not operacoes:
        return TemplateResponse(request, 'fundo_investimento/painel.html', {'operacoes': operacoes, 'dados': {}})
    
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
#         print qtd_dias, calcular_iof_regressivo(qtd_dias)
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
    
    return TemplateResponse(request, 'fundo_investimento/painel.html', {'operacoes': operacoes, 'dados': dados})