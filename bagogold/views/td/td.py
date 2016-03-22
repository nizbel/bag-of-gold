# -*- coding: utf-8 -*-
from bagogold.forms.td import OperacaoTituloForm
from bagogold.models.td import OperacaoTitulo, HistoricoTitulo, \
    ValorDiarioTitulo
from bagogold.testTD import buscar_valores_diarios
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import calendar
import datetime



@login_required
def editar_operacao_td(request, id):
    operacao = OperacaoTitulo.objects.get(pk=id)
    if request.method == 'POST':
        if request.POST.get("save"):
            form = OperacaoTituloForm(request.POST, instance=operacao)
            if form.is_valid():
                form.save()
            return HttpResponseRedirect(reverse('historico_td'))
        elif request.POST.get("delete"):
            operacao.delete()
            return HttpResponseRedirect(reverse('historico_td'))

    else:
        form = OperacaoTituloForm(instance=operacao)
            
    return render_to_response('td/editar_operacao_td.html', {'form': form}, context_instance=RequestContext(request))   

    
@login_required
def historico_td(request):
    operacoes = OperacaoTitulo.objects.exclude(data__isnull=True).order_by('data')  
    for operacao in operacoes:
        operacao.valor_unitario = operacao.preco_unitario
    
    qtd_titulos = {}
    total_gasto = 0
    total_patrimonio = 0
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    graf_gasto_total = list()
    graf_patrimonio = list()
    graf_total_venc = list()
    
    for item in operacoes:          
        if isinstance(item, OperacaoTitulo):
            if item.titulo not in qtd_titulos.keys():
                qtd_titulos[item.titulo] = 0
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                item.tipo = 'Compra'
                item.total = -1 * (item.quantidade * item.preco_unitario + \
                item.taxa_bvmf + item.taxa_custodia)
                total_gasto += item.total
                qtd_titulos[item.titulo] += item.quantidade
                graf_gasto_total += [[str(calendar.timegm(item.data.timetuple()) * 1000), float(-total_gasto)]]
                total_patrimonio = 0
                qtd_total_titulos = 0
                for titulo in qtd_titulos.keys():
                    qtd_total_titulos += qtd_titulos[titulo]
                    if not item.data == datetime.date.today():
                        total_patrimonio += (qtd_titulos[titulo] * HistoricoTitulo.objects.get(data=item.data, titulo=titulo).preco_venda)
                    else:
                        for valor_diario in buscar_valores_diarios():
                            if valor_diario.titulo == titulo:
                                total_patrimonio += (qtd_titulos[titulo] * valor_diario.preco_venda)
                                break
                graf_patrimonio += [[str(calendar.timegm(item.data.timetuple()) * 1000), float(total_patrimonio)]]
                graf_total_venc += [[str(calendar.timegm(item.data.timetuple()) * 1000), float(qtd_total_titulos * 1000)]]
                
            elif item.tipo_operacao == 'V':
                item.tipo = 'Venda'
                item.total = (item.quantidade * item.preco_unitario - \
                item.taxa_bvmf - item.taxa_custodia)
                total_gasto += item.total
                qtd_titulos[item.titulo] -= item.quantidade
                graf_gasto_total += [[str(calendar.timegm(item.data.timetuple()) * 1000), float(-total_gasto)]]
                total_patrimonio = 0
                qtd_total_titulos = 0
                for titulo in qtd_titulos.keys():
                    qtd_total_titulos += qtd_titulos[titulo]
                    if item.data is not datetime.date.today():
                        total_patrimonio += (qtd_titulos[titulo] * HistoricoTitulo.objects.get(data=item.data, titulo=titulo).preco_venda)
                    else:
                        for valor_diario in buscar_valores_diarios():
                            if valor_diario.titulo == titulo:
                                total_patrimonio += (qtd_titulos[titulo] * valor_diario.preco_venda)
                                break
                graf_patrimonio += [[str(calendar.timegm(item.data.timetuple()) * 1000), float(total_patrimonio)]]
                graf_total_venc += [[str(calendar.timegm(item.data.timetuple()) * 1000), float(qtd_total_titulos * 1000)]]
            
    # Adicionar valor mais atual para todos os gráficos
    data_mais_atual = datetime.datetime.now()
    graf_gasto_total += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(-total_gasto)]]
    patrimonio_atual = 0
    total_vencimento_atual = 0
    for titulo in qtd_titulos.keys():
        if qtd_titulos[titulo] > 0:
            print '%s %s' % (titulo, qtd_titulos[titulo])
            # Calcular o patrimonio com base nas quantidades de títulos
            valores_diarios_titulo = ValorDiarioTitulo.objects.filter(titulo=titulo).order_by('-data_hora')
            if not valores_diarios_titulo or valores_diarios_titulo[0].data_hora.day != datetime.date.today().day:
                patrimonio_atual += (qtd_titulos[titulo] * HistoricoTitulo.objects.filter(titulo=titulo).order_by('-data')[0].preco_venda)
            else:
                patrimonio_atual += (qtd_titulos[titulo] * valores_diarios_titulo[0].preco_venda)
            
            # Calcular o total a receber no vencimento com base nas quantidades
            total_vencimento_atual += qtd_titulos[titulo] * 1000
    graf_patrimonio += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(patrimonio_atual)]]
    graf_total_venc += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(total_vencimento_atual)]]
        
    dados = {}
    dados['total_venc_atual'] = total_vencimento_atual
    dados['total_gasto'] = -total_gasto
    dados['patrimonio'] = patrimonio_atual
    dados['lucro'] = patrimonio_atual + total_gasto
    dados['lucro_percentual'] = (patrimonio_atual + total_gasto) / -total_gasto * 100
    
    # Pegar valores correntes dos títulos no site do Tesouro
    
    
    return render_to_response('td/historico.html', {'dados': dados, 'operacoes': operacoes, 'graf_total_venc': graf_total_venc,
                                                     'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio},
                               context_instance=RequestContext(request))
    

    
@login_required
def inserir_operacao_td(request):
    if request.method == 'POST':
        form = OperacaoTituloForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('historico_td'))
    else:
        form = OperacaoTituloForm()
            
    return render_to_response('td/inserir_operacao_td.html', {'form': form}, context_instance=RequestContext(request))