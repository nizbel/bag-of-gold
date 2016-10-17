# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoFIIFormSet
from bagogold.bagogold.forms.fii import OperacaoFIIForm, ProventoFIIForm, \
    UsoProventosOperacaoFIIForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII, Divisao
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII, HistoricoFII, \
    FII, UsoProventosOperacaoFII, ValorDiarioFII
from bagogold.bagogold.utils.investidores import is_superuser
from decimal import Decimal, ROUND_FLOOR
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from itertools import chain
from operator import attrgetter, itemgetter
from yahoo_finance import Share
import calendar
import datetime
import math



@login_required
@user_passes_test(is_superuser)
def acompanhamento_mensal_fii(request):
    investidor = request.user.investidor
    operacoes = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
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
    investidor = request.user.investidor
    fiis = FII.objects.all()
    
    comparativos = list()
    for fii in fiis:
        total_proventos = 0
        # Calcular media de proventos dos ultimos 6 recebimentos
        proventos = ProventoFII.objects.filter(fii=fii).order_by('-data_ex')
        if len(proventos) > 6:
            proventos = proventos[0:6]
        if len(proventos) > 0:
            qtd_dias_periodo = (datetime.date.today() - proventos[len(proventos)-1].data_ex).days
        else:
            continue
        for provento in proventos:
            total_proventos += provento.valor_unitario
            
        # Pegar valor atual dos FIIs
        preenchido = False
        try:
            valor_diario_mais_recente = ValorDiarioFII.objects.filter(fii=fii).order_by('-data_hora')
            if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
                valor_atual = valor_diario_mais_recente[0].preco_unitario
                percentual_retorno_semestral = (total_proventos/valor_atual)
                preenchido = True
        except:
            preenchido = False
        if (not preenchido):
            # Pegar último dia util com negociação da ação para calculo do patrimonio
            try:
                valor_atual = HistoricoFII.objects.filter(fii=fii).order_by('-data')[0].preco_unitario
                # Percentual do retorno sobre o valor do fundo
                percentual_retorno_semestral = (total_proventos/valor_atual)
            except:
                valor_atual = 0
                # Percentual do retorno sobre o valor do fundo
                percentual_retorno_semestral = 0
        
        # Taxa diaria pela quantidade de dias
        percentual_retorno_semestral = math.pow(1 + percentual_retorno_semestral, 1/float(qtd_dias_periodo)) - 1
        # Taxa semestral (base 180 dias)
        percentual_retorno_semestral = 100*(math.pow(1 + percentual_retorno_semestral, 180) - 1)
        comparativos += [[fii, valor_atual, total_proventos, percentual_retorno_semestral]]
        
    # Ordenar lista de comparativos
    comparativos = reversed(sorted(comparativos, key=itemgetter(3)))
    
    return render_to_response('fii/aconselhamento.html', {'comparativos': comparativos}, context_instance=RequestContext(request))
    
    
@login_required
def editar_operacao_fii(request, id):
    investidor = request.user.investidor
    
    operacao_fii = OperacaoFII.objects.get(pk=id)
    
    # Verificar se a operação é do investidor logado
    if operacao_fii.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoFII, DivisaoOperacaoFII, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoFIIFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
#     try:
#         uso_proventos = UsoProventosOperacaoFII.objects.get(operacao=operacao_fii)
#     except UsoProventosOperacaoFII.DoesNotExist:
#         uso_proventos = None
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_fii = OperacaoFIIForm(request.POST, instance=operacao_fii)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_fii, investidor=investidor) if varias_divisoes else None
            
            if not varias_divisoes:
                try:
                    form_uso_proventos = UsoProventosOperacaoFIIForm(request.POST, instance=UsoProventosOperacaoFII.objects.get(divisao_operacao__operacao=operacao_fii))
                except UsoProventosOperacaoFII.DoesNotExist:
                    form_uso_proventos = UsoProventosOperacaoFIIForm(request.POST)
            else:
                form_uso_proventos = UsoProventosOperacaoFIIForm()    
                
#             if uso_proventos is not None:
#                 form_uso_proventos = UsoProventosOperacaoFIIForm(request.POST, instance=uso_proventos)
#             else:
#                 form_uso_proventos = UsoProventosOperacaoFIIForm(request.POST)
            
            if form_operacao_fii.is_valid():
                # Validar de acordo com a quantidade de divisões
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_fii.save()
                        formset_divisao.save()
                        for form_divisao_operacao in [form for form in formset_divisao if form.cleaned_data]:
                            # Ignorar caso seja apagado
                            if 'DELETE' in form_divisao_operacao.cleaned_data and form_divisao_operacao.cleaned_data['DELETE']:
                                pass
                            else:
                                divisao_operacao = form_divisao_operacao.save(commit=False)
                                if hasattr(divisao_operacao, 'usoproventosoperacaofii'):
                                    if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] == None or form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] == 0:
                                        divisao_operacao.usoproventosoperacaofii.delete()
                                    else:
                                        divisao_operacao.usoproventosoperacaofii.qtd_utilizada = form_divisao_operacao.cleaned_data['qtd_proventos_utilizada']
                                        divisao_operacao.usoproventosoperacaofii.save()
                                else:
                                    if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] != None and form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] > 0:
                                        # TODO remover operação de uso proventos
                                        divisao_operacao.usoproventosoperacaofii = UsoProventosOperacaoFII(qtd_utilizada=form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'], operacao=operacao_fii)
                                        divisao_operacao.usoproventosoperacaofii.save()
                        
                        messages.success(request, 'Operação alterada com sucesso')
                        return HttpResponseRedirect(reverse('historico_fii'))
                    
                else:    
                    if form_uso_proventos.is_valid():
                        operacao_fii.save()
                        divisao_operacao = DivisaoOperacaoFII.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_fii)
                        divisao_operacao.quantidade = operacao_fii.quantidade
                        divisao_operacao.save()
                        uso_proventos = form_uso_proventos.save(commit=False)
                        if uso_proventos.qtd_utilizada > 0:
                            uso_proventos.operacao = operacao_fii
                            uso_proventos.divisao_operacao = DivisaoOperacaoFII.objects.get(operacao=operacao_fii)
                            uso_proventos.save()
                        # Se uso proventos for 0 e existir uso proventos atualmente, apagá-lo
                        elif uso_proventos.qtd_utilizada == 0 and UsoProventosOperacaoFII.objects.filter(divisao_operacao__operacao=operacao_fii):
                            uso_proventos.delete()
                        messages.success(request, 'Operação alterada com sucesso')
                        return HttpResponseRedirect(reverse('historico_fii'))
                        
            for erros in form_operacao_fii.errors.values():
                for erro in erros:
                    messages.error(request, erro)
            for erro in formset_divisao.non_form_errors():
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            divisao_fii = DivisaoOperacaoFII.objects.filter(operacao=operacao_fii)
            for divisao in divisao_fii:
                if hasattr(divisao, 'usoproventosoperacaofii'):
                    divisao.usoproventosoperacaofii.delete()
                divisao.delete()
            operacao_fii.delete()
            messages.success(request, 'Operação apagada com sucesso')
            return HttpResponseRedirect(reverse('historico_fii'))

    else:
        form_operacao_fii = OperacaoFIIForm(instance=operacao_fii)
        if not varias_divisoes:
            try:
                form_uso_proventos = UsoProventosOperacaoFIIForm(instance=UsoProventosOperacaoFII.objects.get(divisao_operacao__operacao=operacao_fii))
            except UsoProventosOperacaoFII.DoesNotExist:
                form_uso_proventos = UsoProventosOperacaoFIIForm()
        else:
            form_uso_proventos = UsoProventosOperacaoFIIForm()
        formset_divisao = DivisaoFormSet(instance=operacao_fii, investidor=investidor)
            
    return render_to_response('fii/editar_operacao_fii.html', {'form_operacao_fii': form_operacao_fii, 'form_uso_proventos': form_uso_proventos,
                                                               'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes}, context_instance=RequestContext(request))   


@login_required
@user_passes_test(is_superuser)
def editar_provento_fii(request, id):
    operacao = ProventoFII.objects.get(pk=id)
    if request.method == 'POST':
        if request.POST.get("save"):
            form = ProventoFIIForm(request.POST, instance=operacao)
            if form.is_valid():
                form.save()
            messages.success(request, 'Provento alterado com sucesso')
            return HttpResponseRedirect(reverse('historico_fii'))
        elif request.POST.get("delete"):
            operacao.delete()
            messages.success(request, 'Provento apagado com sucesso')
            return HttpResponseRedirect(reverse('historico_fii'))

    else:
        form = ProventoFIIForm(instance=operacao)
            
    return render_to_response('fii/editar_provento_fii.html', {'form': form}, context_instance=RequestContext(request))   
    
    
@login_required
def historico_fii(request):
    investidor = request.user.investidor
    operacoes = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data') 
    
    # Se investidor não tiver feito operações
    if not operacoes:
        return render_to_response('fii/historico.html', {'dados': {}, 'lista_conjunta': list(), 'graf_poupanca_proventos': list(), 
                                                     'graf_gasto_total': list(), 'graf_patrimonio': list()},
                               context_instance=RequestContext(request))
    
     
    for operacao in operacoes:
        operacao.valor_unitario = operacao.preco_unitario
    
    proventos = ProventoFII.objects.exclude(data_ex__isnull=True).exclude(data_ex__gt=datetime.date.today()).filter(data_ex__gt=operacoes[0].data, fii__in=operacoes.values_list('fii', flat=True)).order_by('data_ex')  
    for provento in proventos:
        provento.data = provento.data_ex
        provento.tipo = 'Provento'
    
    # Proventos devem ser computados primeiro na data EX
    lista_conjunta = sorted(chain(proventos, operacoes),
                            key=attrgetter('data'))
    
    qtd_papeis = {}
    total_gasto = Decimal(0)
    total_proventos = Decimal(0)
    
    # Gráfico de proventos recebidos
    graf_poupanca_proventos = list()
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    graf_gasto_total = list()
    graf_patrimonio = list()
    
    # Verifica se foi adicionada alguma operação na data de hoje
    houve_operacao_hoje = False
    
    for item in lista_conjunta:   
        if item.fii.ticker not in qtd_papeis.keys():
            qtd_papeis[item.fii.ticker] = Decimal(0)       
        if isinstance(item, OperacaoFII):
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                item.tipo = 'Compra'
                uso_proventos = Decimal(0)
                if len(item.usoproventosoperacaofii_set.all()) > 0:
                    uso_proventos += item.usoproventosoperacaofii_set.all()[0].qtd_utilizada
                    total_proventos -= uso_proventos
                item.total = Decimal(-1) * (item.quantidade * item.preco_unitario + \
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
            item.total = (qtd_papeis[item.fii.ticker] * item.valor_unitario * Decimal(100)).to_integral_exact(rounding=ROUND_FLOOR) / Decimal(100)
            item.quantidade = qtd_papeis[item.fii.ticker]
            total_proventos += item.total
        
        # Prepara data
        data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_poupanca_proventos) > 0 and graf_poupanca_proventos[-1][0] == data_formatada:
            graf_poupanca_proventos[len(graf_gasto_total)-1][1] = float(total_proventos)
        else:
            graf_poupanca_proventos += [[data_formatada, float(total_proventos)]]
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_gasto_total) > 0 and graf_gasto_total[-1][0] == data_formatada:
            graf_gasto_total[len(graf_gasto_total)-1][1] = float(-total_gasto)
        else:
            graf_gasto_total += [[data_formatada, float(-total_gasto)]]
        
        patrimonio = 0
        # Verifica se houve operacao hoje
        if item.data != datetime.date.today():
            for fii in qtd_papeis.keys():
                # Pegar último dia util com negociação do fii para calculo do patrimonio
                ultimo_dia_util = item.data
                while not HistoricoFII.objects.filter(data=ultimo_dia_util, fii__ticker=fii):
                    ultimo_dia_util -= datetime.timedelta(days=1)
                patrimonio += (qtd_papeis[fii] * HistoricoFII.objects.get(fii__ticker=fii, data=ultimo_dia_util).preco_unitario)
        else:
            houve_operacao_hoje = True
            for fii in qtd_papeis.keys():
                # Tenta pegar valor diario, se nao houver, pegar historico do ultimo dia util
                try:
                    patrimonio += (Decimal(qtd_papeis[fii]) * ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).order_by('-data_hora')[0].preco_unitario)
                except:
                    patrimonio += (Decimal(qtd_papeis[fii]) * HistoricoFII.objects.filter(fii__ticker=fii).order_by('-data')[0].preco_unitario)
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
            graf_patrimonio[len(graf_gasto_total)-1][1] = float(patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(patrimonio)]]
        
    # Adicionar valor mais atual para todos os gráficos
    if not houve_operacao_hoje:
        data_mais_atual = datetime.date.today()
        graf_poupanca_proventos += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(total_proventos)]]
        graf_gasto_total += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(-total_gasto)]]
        
        patrimonio = 0
        for fii in qtd_papeis.keys():
            if qtd_papeis[fii] > 0:
                patrimonio += (qtd_papeis[fii] * HistoricoFII.objects.filter(fii__ticker=fii)[0].preco_unitario)
                
        graf_patrimonio += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(patrimonio)]]
        
    dados = {}
    dados['total_proventos'] = total_proventos
    dados['total_gasto'] = -total_gasto
    dados['patrimonio'] = patrimonio
    dados['lucro'] = patrimonio + total_proventos + total_gasto
    dados['lucro_percentual'] = (patrimonio + total_proventos + total_gasto) / -total_gasto * 100
    return render_to_response('fii/historico.html', {'dados': dados, 'lista_conjunta': lista_conjunta, 'graf_poupanca_proventos': graf_poupanca_proventos, 
                                                     'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio},
                               context_instance=RequestContext(request))
    
    
@login_required
def inserir_operacao_fii(request):
    investidor = request.user.investidor
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoFII, DivisaoOperacaoFII, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoFIIFormSet)
    
    if request.method == 'POST':
        form_operacao_fii = OperacaoFIIForm(request.POST)
        form_uso_proventos = UsoProventosOperacaoFIIForm(request.POST) if not varias_divisoes else None
        formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        if form_operacao_fii.is_valid():
            operacao_fii = form_operacao_fii.save(commit=False)
            operacao_fii.investidor = investidor
            if varias_divisoes:
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_fii, investidor=investidor)
                if formset_divisao.is_valid():
                    operacao_fii.save()
                    formset_divisao.save()
                    for form_divisao_operacao in [form for form in formset_divisao if form.cleaned_data]:
                        divisao_operacao = form_divisao_operacao.save(commit=False)
                        if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] != None and form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] > 0:
                            # TODO remover operação de uso proventos
                            divisao_operacao.usoproventosoperacaofii = UsoProventosOperacaoFII(qtd_utilizada=form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'], operacao=operacao_fii)
                            divisao_operacao.usoproventosoperacaofii.save()
                        
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('historico_fii'))
                
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
                    
            else:
                if form_uso_proventos.is_valid():
                    operacao_fii.save()
                    divisao_operacao = DivisaoOperacaoFII(operacao=operacao_fii, quantidade=operacao_fii.quantidade, divisao=investidor.divisaoprincipal.divisao)
                    divisao_operacao.save()
                    uso_proventos = form_uso_proventos.save(commit=False)
                    if uso_proventos.qtd_utilizada > 0:
                        uso_proventos.operacao = operacao_fii
                        uso_proventos.divisao_operacao = divisao_operacao
                        uso_proventos.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('historico_fii'))
    else:
        form_operacao_fii = OperacaoFIIForm()
        form_uso_proventos = UsoProventosOperacaoFIIForm(initial={'qtd_utilizada': Decimal('0.00')})
        formset_divisao = DivisaoFormSet(investidor=investidor)
            
    return render_to_response('fii/inserir_operacao_fii.html', {'form_operacao_fii': form_operacao_fii, 'form_uso_proventos': form_uso_proventos,
                                                               'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes}, context_instance=RequestContext(request))


@login_required
@user_passes_test(is_superuser)
def inserir_provento_fii(request):
    if request.method == 'POST':
        form = ProventoFIIForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('historico_fii'))
    else:
        form = ProventoFIIForm()
            
    return render_to_response('fii/inserir_provento_fii.html', {'form': form}, context_instance=RequestContext(request))

@login_required
def painel(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    investidor = request.user.investidor
    
    operacoes = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  
    for operacao in operacoes:
        operacao.valor_unitario = operacao.preco_unitario
        
    operacoes_fiis = list(set(operacoes.values_list('fii', flat=True)))
    
    proventos = ProventoFII.objects.filter(fii__in=operacoes_fiis).exclude(data_ex__isnull=True).exclude(data_ex__gt=datetime.date.today()).order_by('data_ex')  
    for provento in proventos:
        provento.data = provento.data_ex
    
    # Proventos devem ser computados primeiro na data EX
    lista_conjunta = sorted(chain(proventos, operacoes),
                            key=attrgetter('data'))
    
    fiis = {}
    
    
    for item in lista_conjunta:   
        if item.fii.ticker not in fiis.keys():
            fiis[item.fii.ticker] = Object() 
            fiis[item.fii.ticker].quantidade = 0    
            fiis[item.fii.ticker].total_gasto = 0    
        if isinstance(item, OperacaoFII):
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                item.total = -1 * (item.quantidade * item.preco_unitario + \
                item.emolumentos + item.corretagem)
                fiis[item.fii.ticker].total_gasto += float(item.total)
                fiis[item.fii.ticker].quantidade += item.quantidade
                
            elif item.tipo_operacao == 'V':
                item.total = (item.quantidade * item.preco_unitario - \
                item.emolumentos - item.corretagem)
                fiis[item.fii.ticker].total_gasto += float(item.total)
                fiis[item.fii.ticker].quantidade -= item.quantidade
                
        elif isinstance(item, ProventoFII):
            item.total = math.floor(fiis[item.fii.ticker].quantidade * item.valor_unitario * 100) / 100
            fiis[item.fii.ticker].total_gasto += float(item.total)
        
    # Pegar totais de FIIs  
    total_papeis = 0      
    total_valor = 0
    
    for fii in fiis.keys():
        if fiis[fii].quantidade == 0:
            del fiis[fii]
    
    # Preencher totais   
    for fii in fiis.keys():
        total_papeis += fiis[fii].quantidade
        try:
            fiis[fii].valor = ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).order_by('-data_hora')[0].preco_unitario
        except:
            fiis[fii].valor = HistoricoFII.objects.filter(fii__ticker=fii).order_by('-data')[0].preco_unitario
        fiis[fii].valor_total = fiis[fii].valor * fiis[fii].quantidade
        fiis[fii].preco_medio = -fiis[fii].total_gasto / fiis[fii].quantidade
        total_valor += fiis[fii].valor_total
    
    # Calcular percentagens
    for fii in fiis.keys():
        fiis[fii].quantidade_percentual = float(fiis[fii].quantidade) / total_papeis * 100
        fiis[fii].valor_total_percentual = fiis[fii].valor_total / total_valor * 100
    
    # Popular dados
    dados = {}
    dados['total_papeis'] = total_papeis
    dados['total_valor'] = total_valor
    dados['valor_diario_mais_recente'] = ValorDiarioFII.objects.latest('data_hora').data_hora

    return render_to_response('fii/painel.html', 
                              {'fiis': fiis, 'dados': dados},
                              context_instance=RequestContext(request))