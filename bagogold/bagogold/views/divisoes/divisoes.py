# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.divisoes import DivisaoForm
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC, \
    DivisaoOperacaoFII
from bagogold.bagogold.models.fii import ValorDiarioFII, HistoricoFII, \
    OperacaoFII
from bagogold.bagogold.models.lc import HistoricoTaxaDI, \
    HistoricoPorcentagemLetraCredito, LetraCredito
from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_divisao
from bagogold.bagogold.utils.lc import calcular_valor_lc_ate_dia, \
    calcular_valor_lc_ate_dia_por_divisao
from decimal import Decimal
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import datetime

def detalhar_divisao(request, id):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    divisao = Divisao.objects.get(id=id)
    divisao.valor_total = 0
    
    composicao = {}
    
    # Adicionar letras de crédito
    composicao['lc'] = Object()
    composicao['lc'].nome = 'Letras de Crédito'
    composicao['lc'].patrimonio = 0
    composicao['lc'].composicao = {}
    valores_letras_credito_dia = calcular_valor_lc_ate_dia_por_divisao(datetime.date.today(), divisao.id)
    for lc_id in valores_letras_credito_dia.keys():
        composicao['lc'].patrimonio += valores_letras_credito_dia[lc_id]
        composicao['lc'].composicao[lc_id] = Object()
        lc_nome = LetraCredito.objects.get(id=lc_id).nome
        composicao['lc'].composicao[lc_id].nome = lc_nome
        composicao['lc'].composicao[lc_id].patrimonio = valores_letras_credito_dia[lc_id]
        composicao['lc'].composicao[lc_id].composicao = {}
        # Pegar operações dos LCs
        for operacao_divisao in DivisaoOperacaoLC.objects.filter(divisao=divisao, operacao__letra_credito__id=lc_id):
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id] = Object()
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].nome = operacao_divisao.operacao.tipo_operacao
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].data = operacao_divisao.operacao.data
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].quantidade = operacao_divisao.quantidade
            try:
                composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].valor_unitario = HistoricoPorcentagemLetraCredito.objects.filter(letra_credito=operacao_divisao.operacao.letra_credito, \
                                                                                                                                        data__lte=operacao_divisao.operacao.data).order_by('-data')[0].porcentagem_di
            except:
                composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].valor_unitario = HistoricoPorcentagemLetraCredito.objects.get(data__isnull=True, letra_credito=operacao_divisao.operacao.letra_credito).porcentagem_di
            
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].patrimonio = operacao_divisao.quantidade
    
    # Adicionar FIIs
    composicao['fii'] = Object()
    composicao['fii'].nome = 'Fundos de Invest. Imob.'
    composicao['fii'].patrimonio = 0
    composicao['fii'].composicao = {}
    # Pegar FIIs contidos na divisão
    qtd_fiis_dia = calcular_qtd_fiis_ate_dia_por_divisao(datetime.date.today(), divisao.id)
    for ticker in qtd_fiis_dia.keys():
        try:
            fii_valor = ValorDiarioFII.objects.filter(fii__ticker=ticker, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).order_by('-data_hora')[0].preco_unitario
        except:
            fii_valor = HistoricoFII.objects.filter(fii__ticker=ticker).order_by('-data')[0].preco_unitario
        composicao['fii'].patrimonio += qtd_fiis_dia[ticker] * fii_valor
        composicao['fii'].composicao[ticker] = Object()
        composicao['fii'].composicao[ticker].nome = ticker
        composicao['fii'].composicao[ticker].patrimonio = qtd_fiis_dia[ticker] * fii_valor
        composicao['fii'].composicao[ticker].composicao = {}
        # Pegar operações dos FIIs
        for operacao_divisao in DivisaoOperacaoFII.objects.filter(divisao=divisao, operacao__fii__ticker=ticker):
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id] = Object()
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].nome = operacao_divisao.operacao.tipo_operacao
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].data = operacao_divisao.operacao.data
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].quantidade = operacao_divisao.quantidade
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].valor_unitario = HistoricoFII.objects.get(data=operacao_divisao.operacao.data, fii=operacao_divisao.operacao.fii).preco_unitario
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].patrimonio = operacao_divisao.quantidade * \
                composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].valor_unitario
    
    # Calcular valor total da divisão
    for item in composicao.values():
        divisao.valor_total += item.patrimonio
        
    # Calcular valor percentual para cada item da composição da divisão
    for item in composicao.values():
        item.percentual = item.patrimonio / divisao.valor_total * 100
        # Calcular valor percentual para cada operação
        for operacao in item.composicao.values():
            operacao.percentual = operacao.patrimonio / item.patrimonio * 100
        
    return render_to_response('divisoes/detalhar_divisao.html', {'divisao': divisao, 'composicao': composicao},
                               context_instance=RequestContext(request))
    
def inserir_divisao(request):
    if request.method == 'POST':
        form = DivisaoForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('listar_divisoes'))
    else:
        form = DivisaoForm()
            
    return render_to_response('divisoes/inserir_divisao.html', {'form': form}, context_instance=RequestContext(request))

def listar_divisoes(request):
    divisoes = Divisao.objects.all()
    
    for divisao in divisoes:
        divisao.valor_atual = 0
        # TODO calcular valor atual
        # Fundos de investimento imobiliário
        fii_divisao = calcular_qtd_fiis_ate_dia_por_divisao(datetime.date.today(), divisao.id)
        for ticker in fii_divisao.keys():
            try:
                fii_valor = ValorDiarioFII.objects.filter(fii__ticker=ticker, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).order_by('-data_hora')[0].preco_unitario
            except:
                fii_valor = HistoricoFII.objects.filter(fii__ticker=ticker).order_by('-data')[0].preco_unitario
            divisao.valor_atual += (fii_divisao[ticker] * fii_valor)
        # Letras de crédito
        lc_divisao = calcular_valor_lc_ate_dia_por_divisao(datetime.date.today(), divisao.id)
        for total_lc in lc_divisao.values():
            print total_lc
            divisao.valor_atual += total_lc
        
        if not divisao.objetivo_indefinido():
            divisao.quantidade_percentual = divisao.valor_atual / divisao.valor_objetivo * 100
        else:
            divisao.quantidade_percentual = 100
    
    return render_to_response('divisoes/listar_divisoes.html', {'divisoes': divisoes}, context_instance=RequestContext(request))