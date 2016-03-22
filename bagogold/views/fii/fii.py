# -*- coding: utf-8 -*-
from bagogold.forms.fii import OperacaoFIIForm, ProventoFIIForm
from bagogold.models.fii import OperacaoFII, ProventoFII, HistoricoFII, FII
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from itertools import chain
from operator import attrgetter
from yahoo_finance import Share
import calendar
import datetime
import math



@login_required
def acompanhamento_mensal_fii(request):
    operacoes = OperacaoFII.objects.exclude(data__isnull=True).order_by('data')
    
    graf_vendas_mes = list()
    graf_lucro_mes = list()
    
    dados_mes = {'qtd_compra': 0, 'qtd_venda': 0, 'qtd_op_compra': 0, 'qtd_op_venda': 0, 'lucro_bruto': 0}
    
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            dados_mes['qtd_compra'] += operacao.quantidade
            dados_mes['qtd_op_compra'] += 1
        elif operacao.tipo_operacao == 'V':
            dados_mes['qtd_venda'] += operacao.quantidade
            dados_mes['qtd_op_venda'] += 1
        
    
    return render_to_response('fii/acompanhamento_mensal.html', {'dados_mes': dados_mes, 'graf_vendas_mes': graf_vendas_mes,
                                                                         'graf_lucro_mes': graf_lucro_mes}, context_instance=RequestContext(request))
    
    
@login_required
def aconselhamento_fii(request):
    fiis = FII.objects.filter()
    
    comparativos = list()
    for fii in fiis:
        total_proventos = 0
        # Calcular media de proventos dos ultimos 6 recebimentos
        proventos = ProventoFII.objects.filter(fii=fii).order_by('-data_ex')
        if len(proventos) > 6:
            proventos = proventos[0:6]
        if len(proventos) > 0:
            qtd_dias_periodo = (datetime.date.today() - proventos[len(proventos)-1].data_ex).days
        for provento in proventos:
            total_proventos += provento.valor_unitario
        
        valor_atual = Decimal(Share('%s.SA' % (fii)).get_price())
        # Percentual do retorno sobre o valor do fundo
        percentual_retorno_semestral = (total_proventos/valor_atual)
        # Taxa diaria pela quantidade de dias
        percentual_retorno_semestral = math.pow(1 + percentual_retorno_semestral, 1/float(qtd_dias_periodo)) - 1
        # Taxa semestral (base 180 dias)
        percentual_retorno_semestral = 100*(math.pow(1 + percentual_retorno_semestral, 180) - 1)
        comparativos += [[fii, valor_atual, total_proventos, percentual_retorno_semestral]]
        
    
    return render_to_response('fii/aconselhamento.html', {'comparativos': comparativos}, context_instance=RequestContext(request))
    
    
@login_required
def editar_operacao_fii(request, id):
    operacao = OperacaoFII.objects.get(pk=id)
    if request.method == 'POST':
        if request.POST.get("save"):
            form = OperacaoFIIForm(request.POST, instance=operacao)
            if form.is_valid():
                form.save()
            return HttpResponseRedirect(reverse('historico_fii'))
        elif request.POST.get("delete"):
            operacao.delete()
            return HttpResponseRedirect(reverse('historico_fii'))

    else:
        form = OperacaoFIIForm(instance=operacao)
            
    return render_to_response('fii/editar_operacao_fii.html', {'form': form}, context_instance=RequestContext(request))   

@login_required
def editar_provento_fii(request, id):
    operacao = ProventoFII.objects.get(pk=id)
    if request.method == 'POST':
        if request.POST.get("save"):
            form = ProventoFIIForm(request.POST, instance=operacao)
            if form.is_valid():
                form.save()
            return HttpResponseRedirect(reverse('historico_fii'))
        elif request.POST.get("delete"):
            operacao.delete()
            return HttpResponseRedirect(reverse('historico_fii'))

    else:
        form = ProventoFIIForm(instance=operacao)
            
    return render_to_response('fii/editar_provento_fii.html', {'form': form}, context_instance=RequestContext(request))   
    
    
@login_required
def historico_fii(request):
    operacoes = OperacaoFII.objects.exclude(data__isnull=True).order_by('data')  
    for operacao in operacoes:
        operacao.valor_unitario = operacao.preco_unitario
    
    proventos = ProventoFII.objects.exclude(data_ex__isnull=True).exclude(data_ex__gt=datetime.date.today()).order_by('data_ex')  
    for provento in proventos:
        provento.data = provento.data_ex
        provento.tipo = 'Provento'
    
    lista_conjunta = sorted(chain(operacoes, proventos),
                            key=attrgetter('data'))
    
    qtd_papeis = {}
    total_gasto = 0
    total_proventos = 0
    
    # Gráfico de proventos recebidos
    graf_poupanca_proventos = list()
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    graf_gasto_total = list()
    graf_patrimonio = list()
    
    # Verifica se foi adicionada alguma operação na data de hoje
    houve_operacao_hoje = False
    
    for item in lista_conjunta:   
        if item.fii.ticker not in qtd_papeis.keys():
            qtd_papeis[item.fii.ticker] = 0       
        if isinstance(item, OperacaoFII):
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                item.tipo = 'Compra'
                uso_proventos = 0
                if len(item.usoproventosoperacaofii_set.all()) > 0:
                    uso_proventos += item.usoproventosoperacaofii_set.all()[0].qtd_utilizada
                    total_proventos -= float(uso_proventos)
                item.total = -1 * (item.quantidade * item.preco_unitario + \
                item.emolumentos + item.corretagem - uso_proventos)
                total_gasto += item.total
                qtd_papeis[item.fii.ticker] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                item.tipo = 'Venda'
                item.total = (item.quantidade * item.preco_unitario - \
                item.emolumentos - item.corretagem)
                total_gasto += item.total
                qtd_papeis[item.fii.ticker] -= item.quantidade
                
        elif isinstance(item, ProventoFII):
            item.total = math.floor(qtd_papeis[item.fii.ticker] * item.valor_unitario * 100) / 100
            item.quantidade = qtd_papeis[item.fii.ticker]
            total_proventos += item.total
        
        # Prepara data
        data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_poupanca_proventos) > 0 and graf_poupanca_proventos[len(graf_poupanca_proventos)-1][0] == data_formatada:
            graf_poupanca_proventos[len(graf_gasto_total)-1][1] = total_proventos
        else:
            graf_poupanca_proventos += [[data_formatada, total_proventos]]
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_gasto_total) > 0 and graf_gasto_total[len(graf_gasto_total)-1][0] == data_formatada:
            graf_gasto_total[len(graf_gasto_total)-1][1] = float(-total_gasto)
        else:
            graf_gasto_total += [[data_formatada, float(-total_gasto)]]
        
        patrimonio = 0
        # Verifica se houve operacao hoje
        if item.data != datetime.date.today():
            for fii in qtd_papeis.keys():
                patrimonio += (qtd_papeis[fii] * HistoricoFII.objects.get(fii__ticker=fii, data=item.data).preco_unitario)
        else:
            houve_operacao_hoje = True
            for fii in qtd_papeis.keys():
                patrimonio += (qtd_papeis[fii] * float(Share('%s.SA' % (fii)).get_price()))
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[len(graf_patrimonio)-1][0] == data_formatada:
            graf_patrimonio[len(graf_gasto_total)-1][1] = float(patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(patrimonio)]]
        
    # Adicionar valor mais atual para todos os gráficos
    if not houve_operacao_hoje:
        data_mais_atual = datetime.datetime.now()
        graf_poupanca_proventos += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), total_proventos]]
        graf_gasto_total += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(-total_gasto)]]
        
        patrimonio = 0
        for fii in qtd_papeis.keys():
            if qtd_papeis[fii] > 0:
                patrimonio += (qtd_papeis[fii] * float(Share('%s.SA' % (fii)).get_price()))
                
        graf_patrimonio += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(patrimonio)]]
        
    dados = {}
    dados['total_proventos'] = total_proventos
    dados['total_gasto'] = -total_gasto
    dados['patrimonio'] = patrimonio
    dados['lucro'] = patrimonio + total_proventos + float(total_gasto)
    dados['lucro_percentual'] = (patrimonio + total_proventos + float(total_gasto)) / -float(total_gasto) * 100
    return render_to_response('fii/historico.html', {'dados': dados, 'lista_conjunta': lista_conjunta, 'graf_poupanca_proventos': graf_poupanca_proventos, 
                                                     'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio},
                               context_instance=RequestContext(request))
    

    
    
@login_required
def inserir_operacao_fii(request):
    if request.method == 'POST':
        form = OperacaoFIIForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('historico_fii'))
    else:
        form = OperacaoFIIForm()
            
    return render_to_response('fii/inserir_operacao_fii.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def inserir_provento_fii(request):
    if request.method == 'POST':
        form = ProventoFIIForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('historico_fii'))
    else:
        form = ProventoFIIForm()
            
    return render_to_response('fii/inserir_provento_fii.html', {'form': form}, context_instance=RequestContext(request))
