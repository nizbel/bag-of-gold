# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoTDFormSet
from bagogold.bagogold.forms.td import OperacaoTituloForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.models.lc import LetraCredito, HistoricoTaxaDI,\
    HistoricoPorcentagemLetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo, HistoricoTitulo, \
    ValorDiarioTitulo, Titulo
from bagogold.bagogold.testTD import buscar_valores_diarios
from bagogold.bagogold.utils.fii import \
    calcular_rendimento_proventos_fii_12_meses, \
    calcular_variacao_percentual_fii_por_periodo
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia_por_titulo, \
    calcular_imposto_venda_td
from copy import deepcopy
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import calendar
import copy
import datetime
import math


@login_required
def aconselhamento_td(request):
    # Objeto vazio para preenchimento
    class Object():
        pass
    
    titulos = {}
    titulos_vendidos = {}
    
    for operacao in OperacaoTitulo.objects.filter().order_by('data'):
        # Verificar se se trata de compra
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
            compra_titulo.data_vencimento = operacao.titulo.data_vencimento
            titulos[operacao.titulo.id].append(compra_titulo)
#             valor_atual = ValorDiarioTitulo.objects.filter(titulo__id=operacao.titulo.id).order_by('-data_hora')[0].preco_venda
#             print '%s comprado a %s valendo %s (%s (%s%%) de lucro)' % (operacao.titulo.nome(), operacao.preco_unitario, valor_atual, \
#                                                                       valor_atual - operacao.preco_unitario, (valor_atual - operacao.preco_unitario) / operacao.preco_unitario * 100)
        
        # Verificar se se trata de venda
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
    
    # Dados de títulos ainda em posse do usuario                
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
                operacao.lucro = operacao.valor_total_atual - operacao.total_gasto - calcular_imposto_venda_td((datetime.date.today() - operacao.data).days, operacao.valor_total_atual, operacao.valor_total_atual - operacao.total_gasto)
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
            else:
                operacao.lucro = operacao.valor_total_atual - operacao.total_gasto
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
                
            # Valor esperado é a quantidade que ainda vai render caso investidor espere até o dia do vencimento
            valor_esperado = (Decimal(1000) * operacao.quantidade) - calcular_imposto_venda_td((operacao.data_vencimento - operacao.data).days, Decimal(1000) * operacao.quantidade, \
                                                                                               (Decimal(1000) * operacao.quantidade) - operacao.total_gasto) - (operacao.total_gasto + operacao.lucro)
            qtd_dias_esperado = (Titulo.objects.get(id=titulo).data_vencimento - datetime.date.today()).days
            rendimento_esperado = math.pow(1 + (valor_esperado / (operacao.total_gasto + operacao.lucro) * 100)/100, float(1)/qtd_dias_esperado) - 1
            rendimento_esperado = (math.pow(1 + rendimento_esperado, 30) - 1) * 100
            operacao.rendimento_esperado = (math.pow(1 + rendimento_esperado/100, 12) - 1) * 100
    
    # Data de 12 meses atrás
    data_12_meses = datetime.date.today() - datetime.timedelta(days=365)
    
    letras_credito = list(LetraCredito.objects.all())
    # Comparativo com letras de crédito
    for lc in letras_credito:
        lc.rendimento_atual =  lc.porcentagem_di_atual() * HistoricoTaxaDI.objects.filter(data__isnull=False).order_by('-data')[0].taxa / 100
        # Calcular rendimento real dos últimos 12 meses
        lc.rendimento_12_meses = 1000
        data_iteracao = data_12_meses
        try:
            lc.taxa = HistoricoPorcentagemLetraCredito.objects.filter(data__lte=data_iteracao, letra_credito=lc).order_by('-data')[0].porcentagem_di
        except:
            lc.taxa = HistoricoPorcentagemLetraCredito.objects.get(letra_credito=lc, data__isnull=True).porcentagem_di
        while data_iteracao < datetime.date.today():
            try:
                taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
                lc.rendimento_12_meses = Decimal((pow((float(1) + float(taxa_do_dia)/float(100)), float(1)/float(252)) - float(1)) * float(lc.taxa/100) + float(1)) * lc.rendimento_12_meses
            except HistoricoTaxaDI.DoesNotExist:
                pass
            data_iteracao += datetime.timedelta(days=1)
        lc.rendimento_12_meses = (lc.rendimento_12_meses - 1000) / 10
    letras_credito.sort(key=lambda x: x.rendimento_atual, reverse=True)
        
    fiis = list(FII.objects.all())
    for fii in fiis:
        fii.rendimento_prov = calcular_rendimento_proventos_fii_12_meses(fii)
        if fii.rendimento_prov > 0:
            fii.variacao_12_meses = calcular_variacao_percentual_fii_por_periodo(fii, data_12_meses, datetime.date.today())
            print type(fii.rendimento_prov)
    fiis = [fii for fii in fiis if fii.rendimento_prov > 0]
    fiis.sort(key=lambda x: x.rendimento_prov, reverse=True)
    
    return render_to_response('td/aconselhamento.html', {'titulos': titulos, 'letras_credito': letras_credito, 'fiis': fiis}, context_instance=RequestContext(request))

@login_required
def editar_operacao_td(request, id):
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoTitulo, DivisaoOperacaoTD, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoTDFormSet)
    operacao_td = OperacaoTitulo.objects.get(pk=id)
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_td = OperacaoTituloForm(request.POST, instance=operacao_td)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_td)
            
            if form_operacao_td.is_valid():
                if formset_divisao.is_valid():
                    operacao_td.save()
                    formset_divisao.save()
                    messages.success(request, 'Operação alterada com sucesso')
                    return HttpResponseRedirect(reverse('historico_td'))
            for erros in form_operacao_td.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_divisao.non_form_errors():
                messages.error(request, erro)
            return render_to_response('td/editar_operacao_td.html', {'form_operacao_td': form_operacao_td, 'formset_divisao': formset_divisao }, 
                                      context_instance=RequestContext(request))
        elif request.POST.get("delete"):
            divisao_td = DivisaoOperacaoTD.objects.filter(operacao=operacao_td)
            for divisao in divisao_td:
                divisao.delete()
            operacao_td.delete()
            messages.success(request, 'Operação apagada com sucesso')
            return HttpResponseRedirect(reverse('historico_td'))

    else:
        form_operacao_td = OperacaoTituloForm(instance=operacao_td)
        formset_divisao = DivisaoFormSet(instance=operacao_td)
            
    return render_to_response('td/editar_operacao_td.html', {'form_operacao_td': form_operacao_td, 'formset_divisao': formset_divisao }, 
                              context_instance=RequestContext(request))   

    
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
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoTitulo, DivisaoOperacaoTD, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoTDFormSet)
    
    if request.method == 'POST':
        form_operacao_td = OperacaoTituloForm(request.POST)
        if form_operacao_td.is_valid():
            operacao_td = form_operacao_td.save(commit=False)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_td)
            if formset_divisao.is_valid():
                operacao_td.save()
                formset_divisao.save()
                messages.success(request, 'Operação inserida com sucesso')
            return HttpResponseRedirect(reverse('historico_td'))
            for erro in formset_divisao.non_form_errors():
                messages.error(request, erro)
            return render_to_response('td/inserir_operacao_td.html', {'form_operacao_td': form_operacao_td, 'formset_divisao': formset_divisao }, 
                                      context_instance=RequestContext(request))
        
    else:
        form_operacao_td = OperacaoTituloForm()
        formset_divisao = DivisaoFormSet()
            
    return render_to_response('td/inserir_operacao_td.html', {'form_operacao_td': form_operacao_td, 'formset_divisao': formset_divisao }, 
                                      context_instance=RequestContext(request))

@login_required
def painel(request):
    # Objeto vazio para preenchimento
    class Object():
        pass
    
    titulos = {}
    titulos_vendidos = {}
    
    for operacao in OperacaoTitulo.objects.filter().order_by('data'):
        # Verificar se se trata de compra
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
        
        # Verificar se se trata de venda
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
    
    # Dados de títulos ainda em posse do usuario                
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
                operacao.lucro = (operacao.valor_total_atual - operacao.total_gasto) - calcular_imposto_venda_td((datetime.date.today() - operacao.data).days, operacao.valor_total_atual, operacao.valor_total_atual - operacao.total_gasto)
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
            else:
                operacao.lucro = float(operacao.valor_total_atual - operacao.total_gasto)
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
#             print '%s: %s ao preço %s valendo %s (%s (%s%%) de lucro)' % (titulo, operacao.quantidade, operacao.preco_unitario, valor_atual, \
#                                                                     valor_atual - operacao.preco_unitario, (valor_atual - operacao.preco_unitario) / operacao.preco_unitario * 100)
    
    # Dados de títulos vendidos
    for titulo in titulos_vendidos.keys():
        for operacao in titulos_vendidos[titulo]:
#             print titulo
            operacao.variacao = operacao.valor_atual - operacao.preco_unitario
            operacao.variacao_percentual = operacao.variacao / operacao.preco_unitario * 100
#             print operacao.variacao_percentual
#             print (datetime.date.today() - operacao.data).days
            # Pegar a taxa diária
            operacao.variacao_percentual_mensal = math.pow(1 + operacao.variacao_percentual/100, float(1)/(operacao.data_venda - operacao.data).days) - 1
#             print operacao.variacao_percentual_mensal
            # Pegar a taxa mensal percentual
            operacao.variacao_percentual_mensal = (math.pow(1 + operacao.variacao_percentual_mensal, 30) - 1) * 100
#             print operacao.variacao_percentual_mensal
            # Pegar a taxa anual percentual
            operacao.variacao_percentual_anual = (math.pow(1 + operacao.variacao_percentual_mensal/100, 12) - 1) * 100
            operacao.valor_total_atual = operacao.valor_atual * operacao.quantidade
            if operacao.valor_total_atual > operacao.total_gasto:
                operacao.lucro = (operacao.valor_total_atual - operacao.total_gasto) - calcular_imposto_venda_td((operacao.data_venda - operacao.data).days, operacao.valor_total_atual, operacao.valor_total_atual - operacao.total_gasto)
                operacao.lucro -= operacao.valor_taxas
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
            else:
                operacao.lucro = float(operacao.valor_total_atual - operacao.total_gasto - operacao.valor_taxas)
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
    
    return render_to_response('td/painel.html', {'titulos': titulos, 'titulos_vendidos': titulos_vendidos}, context_instance=RequestContext(request))