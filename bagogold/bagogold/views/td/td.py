# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.td import OperacaoTituloForm
from bagogold.bagogold.models.td import OperacaoTitulo, HistoricoTitulo, \
    ValorDiarioTitulo, Titulo
from bagogold.bagogold.testTD import buscar_valores_diarios
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia, \
    calcular_imposto_venda_td
from copy import deepcopy
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import calendar
import copy
import datetime
import math



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
#             print '%s %s' % (titulo, qtd_titulos[titulo])
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

@login_required
def painel(request):
    # Objeto vazio para preenchimento
    class Object():
        pass
    
    titulos = {}
    titulos_vendidos = {}
#     for titulo_id in OperacaoTitulo.objects.filter().values('titulo_id').distinct():
#         titulo_id = titulo_id['titulo_id']
#         titulos[titulo_id] = Object()
#         titulos[titulo_id].nome = Titulo.objects.get(id=titulo_id).nome()
#         titulos[titulo_id].quantidade = quantidade_titulos_ate_dia(titulo_id, datetime.date.today())
    
    for operacao in OperacaoTitulo.objects.filter().order_by('data'):
        if operacao.tipo_operacao == 'C':
            if operacao.titulo.id not in titulos.keys():
                titulos[operacao.titulo.id] = list()
                titulos_vendidos[operacao.titulo.id] = list()
            compra_titulo = Object()
            compra_titulo.nome = operacao.titulo.nome()
            compra_titulo.quantidade = operacao.quantidade
            compra_titulo.data = operacao.data
            compra_titulo.preco_unitario = operacao.preco_unitario 
            compra_titulo.total_gasto = operacao.quantidade * operacao.preco_unitario
            titulos[operacao.titulo.id].append(compra_titulo)
#             valor_atual = ValorDiarioTitulo.objects.filter(titulo__id=operacao.titulo.id).order_by('-data_hora')[0].preco_venda
#             print '%s comprado a %s valendo %s (%s (%s%%) de lucro)' % (operacao.titulo.nome(), operacao.preco_unitario, valor_atual, \
#                                                                       valor_atual - operacao.preco_unitario, (valor_atual - operacao.preco_unitario) / operacao.preco_unitario * 100)
        elif operacao.tipo_operacao == 'V':
#             print '%s vendido a %s' % (operacao.titulo.nome(), operacao.preco_unitario)
            lista_compras = titulos[operacao.titulo.id]
            lista_compras.sort(key=lambda x: x.preco_unitario)
            indice_operacao = 0
            while operacao.quantidade > 0:
                if lista_compras[indice_operacao].quantidade >= operacao.quantidade:
                    lista_compras[indice_operacao].quantidade -= operacao.quantidade
                    # Adicionar a titulos vendidos
                    venda_objeto = deepcopy(lista_compras[indice_operacao])
                    venda_objeto.quantidade = operacao.quantidade
                    venda_objeto.data_venda = operacao.data
                    venda_objeto.valor_atual = operacao.preco_unitario
                    venda_objeto.valor_taxas = operacao.taxa_bvmf + operacao.taxa_custodia
                    titulos_vendidos[operacao.titulo.id].append(venda_objeto)
                    break
                else:
                    operacao.quantidade -= lista_compras[indice_operacao].quantidade
                    # Adicionar a titulos vendidos
                    venda_objeto = deepcopy(lista_compras[indice_operacao])
                    venda_objeto.quantidade = lista_compras[indice_operacao].quantidade
                    venda_objeto.data_venda = operacao.data
                    venda_objeto.valor_atual = operacao.preco_unitario
                    # Apenas soma o valor da taxa na última venda
                    venda_objeto.valor_taxas = 0
                    titulos_vendidos[operacao.titulo.id].append(venda_objeto)
                    # Remover quantidade do título nas operações vigentes
                    lista_compras[indice_operacao].quantidade = 0
                    indice_operacao += 1
            # Remover aqueles que foram completamente vendidos
            lista_compras = [x for x in lista_compras if x.quantidade > 0]
            titulos[operacao.titulo.id] = lista_compras
                    
    for titulo in titulos.keys():
        for operacao in titulos[titulo]:
            try:
                operacao.valor_atual = ValorDiarioTitulo.objects.filter(titulo__id=titulo).order_by('-data_hora')[0].preco_venda
            except:
                operacao.valor_atual = HistoricoTitulo.objects.filter(titulo__id=titulo).order_by('-data')[0].preco_venda
            operacao.variacao = operacao.valor_atual - operacao.preco_unitario
            operacao.variacao_percentual = operacao.variacao / operacao.preco_unitario * 100
            # Pegar a taxa diária
            operacao.variacao_percentual_mensal = math.pow(1 + operacao.variacao_percentual/100, float(1)/(datetime.date.today() - operacao.data).days) - 1
            # Pegar a taxa mensal
            operacao.variacao_percentual_mensal = (math.pow(1 + operacao.variacao_percentual_mensal, 30) - 1) * 100
            # Pegar a taxa anual
            operacao.variacao_percentual_anual = (math.pow(1 + operacao.variacao_percentual_mensal/100, 12) - 1) * 100
            operacao.valor_total_atual = operacao.valor_atual * operacao.quantidade
            if operacao.valor_total_atual > operacao.total_gasto:
                operacao.lucro = float(operacao.valor_total_atual - operacao.total_gasto) - calcular_imposto_venda_td((datetime.date.today() - operacao.data).days, float(operacao.valor_total_atual), float(operacao.valor_total_atual - operacao.total_gasto))
                operacao.lucro_percentual = operacao.lucro / float(operacao.total_gasto) * 100
            else:
                operacao.lucro = float(operacao.valor_total_atual - operacao.total_gasto)
                operacao.lucro_percentual = operacao.lucro / float(operacao.total_gasto) * 100
#             print '%s: %s ao preço %s valendo %s (%s (%s%%) de lucro)' % (titulo, operacao.quantidade, operacao.preco_unitario, valor_atual, \
#                                                                     valor_atual - operacao.preco_unitario, (valor_atual - operacao.preco_unitario) / operacao.preco_unitario * 100)
    
    for titulo in titulos_vendidos.keys():
        for operacao in titulos_vendidos[titulo]:
            print titulo
            operacao.variacao = operacao.valor_atual - operacao.preco_unitario
            operacao.variacao_percentual = operacao.variacao / operacao.preco_unitario * 100
            print operacao.variacao_percentual
            print (datetime.date.today() - operacao.data).days
            # Pegar a taxa diária
            operacao.variacao_percentual_mensal = math.pow(1 + operacao.variacao_percentual/100, float(1)/(operacao.data_venda - operacao.data).days) - 1
            print operacao.variacao_percentual_mensal
            # Pegar a taxa mensal percentual
            operacao.variacao_percentual_mensal = (math.pow(1 + operacao.variacao_percentual_mensal, 30) - 1) * 100
            print operacao.variacao_percentual_mensal
            # Pegar a taxa anual percentual
            operacao.variacao_percentual_anual = (math.pow(1 + operacao.variacao_percentual_mensal/100, 12) - 1) * 100
            operacao.valor_total_atual = operacao.valor_atual * operacao.quantidade
            if operacao.valor_total_atual > operacao.total_gasto:
                operacao.lucro = float(operacao.valor_total_atual - operacao.total_gasto) - calcular_imposto_venda_td((operacao.data_venda - operacao.data).days, float(operacao.valor_total_atual), float(operacao.valor_total_atual - operacao.total_gasto))
                operacao.lucro -= float(operacao.valor_taxas)
                operacao.lucro_percentual = operacao.lucro / float(operacao.total_gasto) * 100
            else:
                operacao.lucro = float(operacao.valor_total_atual - operacao.total_gasto - operacao.valor_taxas)
                operacao.lucro_percentual = operacao.lucro / float(operacao.total_gasto) * 100
#     titulos = {}
#     for titulo_id in OperacaoTitulo.objects.filter().values('titulo_id').distinct():
#         titulo_id = titulo_id['titulo_id']
#         titulos[titulo_id] = Object()
#         titulos[titulo_id].nome = Titulo.objects.get(id=titulo_id).nome()
#         titulos[titulo_id].quantidade = quantidade_titulos_ate_dia(titulo_id, datetime.date.today())
    
    return render_to_response('td/painel.html', {'titulos': titulos, 'titulos_vendidos': titulos_vendidos}, context_instance=RequestContext(request))