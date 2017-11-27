# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoFIIFormSet
from bagogold.bagogold.forms.fii import OperacaoFIIForm, ProventoFIIForm, \
    UsoProventosOperacaoFIIForm, CalculoResultadoCorretagemForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII, Divisao
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII, HistoricoFII, \
    FII, UsoProventosOperacaoFII, ValorDiarioFII, EventoAgrupamentoFII, \
    EventoDesdobramentoFII, EventoIncorporacaoFII
from bagogold.bagogold.utils.fii import calcular_valor_fii_ate_dia, \
    calcular_poupanca_prov_fii_ate_dia, calcular_qtd_fiis_ate_dia, \
    calcular_preco_medio_fiis_ate_dia
from bagogold.bagogold.utils.investidores import is_superuser
from decimal import Decimal, ROUND_FLOOR
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models.expressions import F, Case, When, Value
from django.db.models.fields import CharField
from django.db.models.query_utils import Q
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from itertools import chain
from operator import attrgetter, itemgetter
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
        
    
    return TemplateResponse(request, 'fii/acompanhamento_mensal.html', {'dados_mes': dados_mes, 'graf_vendas_mes': graf_vendas_mes,
                                                                         'graf_lucro_mes': graf_lucro_mes})
    
    
@adiciona_titulo_descricao('Acompanhamento de FII', 'Mostra o rendimento dos FIIs do investidor para '
    'comparar com os potenciais ganhos em outros investimentos')
def acompanhamento_fii(request):
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
    
    return TemplateResponse(request, 'fii/acompanhamento.html', {'comparativos': comparativos})
    
@adiciona_titulo_descricao('Cálculo de corretagem', 'Calcular quantidade de dinheiro que o investidor pode juntar para '
    'comprar novas cotasde forma a diluir mais eficientemente a corretagem')
def calcular_resultado_corretagem(request):
    # Preparar ranking
    ranking = list()
    
    if request.method == 'POST':
        form_calcular = CalculoResultadoCorretagemForm(request.POST)
        
        if form_calcular.is_valid():
            NUM_MESES = form_calcular.cleaned_data['num_meses']
            PRECO_COTA = form_calcular.cleaned_data['preco_cota']
            CORRETAGEM = form_calcular.cleaned_data['corretagem']
            RENDIMENTO = form_calcular.cleaned_data['rendimento']
            QTD_COTAS = form_calcular.cleaned_data['quantidade_cotas']
            
            ranking = list()
            for qtd_cotas_juntar in range(1, 11):
                qtd_cotas = QTD_COTAS
                qtd_acumulada = 0
                for _ in range(NUM_MESES):
                    qtd_acumulada += qtd_cotas * RENDIMENTO
                    if qtd_acumulada >= (PRECO_COTA * qtd_cotas_juntar) + CORRETAGEM:
                        qtd_cotas_comprada = int(math.floor((qtd_acumulada - CORRETAGEM) / PRECO_COTA))
                        qtd_cotas += qtd_cotas_comprada
                        qtd_acumulada -= (qtd_cotas_comprada * PRECO_COTA) + CORRETAGEM
                # print 'Ao final, tem %s cotas e %s reais' % (qtd_cotas, qtd_acumulada)
                total_acumulado = qtd_cotas * PRECO_COTA + qtd_acumulada
        #         print 'Esperando %s: %s' % (qtd_cotas_juntar, total_acumulado)
                ranking.append((qtd_cotas_juntar, total_acumulado))
                
            ranking.sort(key=lambda x: x[1], reverse=True)
                
    else:
        form_calcular = CalculoResultadoCorretagemForm()
    
    return TemplateResponse(request, 'fii/calcular_resultado_corretagem.html', {'ranking': ranking, 'form_calcular': form_calcular})
    
    
@login_required
@adiciona_titulo_descricao('Editar operação em FII', 'Alterar valores de uma operação de compra/venda em Fundos de Investimento Imobiliário')
def editar_operacao_fii(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_fii = get_object_or_404(OperacaoFII, pk=operacao_id)
    
    # Verificar se a operação é do investidor logado
    if operacao_fii.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoFII, DivisaoOperacaoFII, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoFIIFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
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
                        return HttpResponseRedirect(reverse('fii:historico_fii'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                    
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
                        return HttpResponseRedirect(reverse('fii:historico_fii'))
                        
            for erro in [erro for erro in form_operacao_fii.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            divisao_fii = DivisaoOperacaoFII.objects.filter(operacao=operacao_fii)
            for divisao in divisao_fii:
                if hasattr(divisao, 'usoproventosoperacaofii'):
                    divisao.usoproventosoperacaofii.delete()
                divisao.delete()
            operacao_fii.delete()
            messages.success(request, 'Operação apagada com sucesso')
            return HttpResponseRedirect(reverse('fii:historico_fii'))

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
            
    return TemplateResponse(request, 'fii/editar_operacao_fii.html', {'form_operacao_fii': form_operacao_fii, 'form_uso_proventos': form_uso_proventos,
                                                               'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})   


@adiciona_titulo_descricao('Histórico de FII', 'Histórico de operações de compra/venda e rendimentos/amortizações do investidor')
def historico_fii(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'fii/historico.html', {'dados': {}, 'lista_conjunta': list(), 'graf_poupanca_proventos': list(), 
                                                     'graf_gasto_total': list(), 'graf_patrimonio': list(), 'lista_eventos': list()})
        
    operacoes = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).annotate(valor_unitario=F('preco_unitario')).annotate(tipo=Case(When(tipo_operacao='C', then=Value(u'Compra')),
                                                                                                                                                            When(tipo_operacao='V', then=Value(u'Venda')),
                                                                                                                                                            output_field=CharField())).order_by('data') 
    
    # Se investidor não tiver feito operações
    if not operacoes:
        return TemplateResponse(request, 'fii/historico.html', {'dados': {}, 'lista_conjunta': list(), 'graf_poupanca_proventos': list(), 
                                                     'graf_gasto_total': list(), 'graf_patrimonio': list(), 'lista_eventos': list()})
    
    # Proventos
    proventos = ProventoFII.objects.exclude(data_ex__isnull=True).exclude(data_ex__gt=datetime.date.today()).filter(data_ex__gt=operacoes[0].data, fii__in=operacoes.values_list('fii', flat=True)) \
        .annotate(tipo=Value(u'Provento', output_field=CharField())).annotate(data=F('data_ex')).order_by('data_ex')  
    
    # Eventos
    agrupamentos = EventoAgrupamentoFII.objects.filter(fii__in=operacoes.values_list('fii', flat=True), data__lte=datetime.date.today()) \
        .annotate(tipo=Value(u'Agrupamento', output_field=CharField())).annotate(valor_unitario=F('proporcao')).order_by('data') 

    desdobramentos = EventoDesdobramentoFII.objects.filter(fii__in=operacoes.values_list('fii', flat=True), data__lte=datetime.date.today()) \
        .annotate(tipo=Value(u'Desdobramento', output_field=CharField())).annotate(valor_unitario=F('proporcao')).order_by('data')
    
    incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__in=operacoes.values_list('fii', flat=True), data__lte=datetime.date.today()) \
                                                         | Q(novo_fii__in=operacoes.values_list('fii', flat=True), data__lte=datetime.date.today())).annotate(tipo=Value(u'Incorporação', output_field=CharField())) \
                                                         .annotate(valor_unitario=F('novo_fii__ticker')).order_by('data')

    
    # Proventos devem ser computados primeiro na data EX
    lista_conjunta = sorted(chain(proventos, agrupamentos, desdobramentos, incorporacoes, operacoes),
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
    
    for indice, item in enumerate(lista_conjunta):   
        if item.fii.ticker not in qtd_papeis.keys():
            qtd_papeis[item.fii.ticker] = Decimal(0)       
        # Verificar se se trata de compra, venda ou provento
        if item.tipo == 'Compra':
            uso_proventos = Decimal(0)
            if item.utilizou_proventos():
                uso_proventos += item.qtd_proventos_utilizada()
                total_proventos -= uso_proventos
            item.total = Decimal(-1) * (item.quantidade * item.preco_unitario + \
            item.emolumentos + item.corretagem - uso_proventos)
            total_gasto += item.total
            qtd_papeis[item.fii.ticker] += item.quantidade
            
        elif item.tipo == 'Venda':
            item.total = (item.quantidade * item.preco_unitario - \
            item.emolumentos - item.corretagem)
            total_gasto += item.total
            qtd_papeis[item.fii.ticker] -= item.quantidade
                
        elif item.tipo == 'Provento':
            if qtd_papeis[item.fii.ticker] == 0:
                item.quantidade = 0
                continue
#             item.total = (qtd_papeis[item.fii.ticker] * item.valor_unitario * Decimal(100)).to_integral_exact(rounding=ROUND_FLOOR) / Decimal(100)
            item.total = (qtd_papeis[item.fii.ticker] * item.valor_unitario).quantize(Decimal('0.01'))
            item.quantidade = qtd_papeis[item.fii.ticker]
            total_proventos += item.total
            
        elif item.tipo == 'Agrupamento':
            if qtd_papeis[item.fii.ticker] == 0:
                item.quantidade = 0
                continue
            item.quantidade = qtd_papeis[item.fii.ticker]
            qtd_papeis[item.fii.ticker] = item.qtd_apos(item.quantidade)
            item.total = qtd_papeis[item.fii.ticker]
                        
        elif item.tipo == 'Desdobramento':
            if qtd_papeis[item.fii.ticker] == 0:
                item.quantidade = 0
                continue
            item.quantidade = qtd_papeis[item.fii.ticker]
            qtd_papeis[item.fii.ticker] = item.qtd_apos(item.quantidade)
            item.total = qtd_papeis[item.fii.ticker]
            
        elif item.tipo == 'Incorporação':
            if qtd_papeis[item.fii.ticker] == 0:
                item.quantidade = 0
                continue
            item.quantidade = qtd_papeis[item.fii.ticker]
            item.total = qtd_papeis[item.fii.ticker]
            qtd_papeis[item.novo_fii.ticker] += qtd_papeis[item.fii.ticker]
            qtd_papeis[item.fii.ticker] = 0
            
        # Verifica se próximo elemento possui a mesma data
        if indice == len(lista_conjunta) - 1 or item.data != lista_conjunta[indice+1].data:
            # Prepara data
            data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
            
            graf_poupanca_proventos += [[data_formatada, float(total_proventos)]]
            graf_gasto_total += [[data_formatada, float(-total_gasto)]]
            
            patrimonio = 0
            # Verifica se houve operacao hoje
            if item.data != datetime.date.today():
                for fii in qtd_papeis.keys():
                    # Pegar último dia util com negociação do fii para calculo do patrimonio
                    patrimonio += (qtd_papeis[fii] * HistoricoFII.objects.filter(data__lte=item.data, fii__ticker=fii).order_by('-data')[0].preco_unitario)
            else:
                houve_operacao_hoje = True
                for fii in qtd_papeis.keys():
                    # Tenta pegar valor diario, se nao houver, pegar historico do ultimo dia util
                    if ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=datetime.date.today()).exists():
                        patrimonio += (Decimal(qtd_papeis[fii]) * ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=datetime.date.today()).order_by('-data_hora')[0].preco_unitario)
                    else:
                        patrimonio += (Decimal(qtd_papeis[fii]) * HistoricoFII.objects.filter(fii__ticker=fii).order_by('-data')[0].preco_unitario)
            graf_patrimonio += [[data_formatada, float(patrimonio)]]
        
    # Adicionar valor mais atual para todos os gráficos
    if not houve_operacao_hoje:
        data_mais_atual = datetime.date.today()
        graf_poupanca_proventos += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(total_proventos)]]
        graf_gasto_total += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(-total_gasto)]]
        
        patrimonio = 0
        for fii in qtd_papeis.keys():
            if qtd_papeis[fii] > 0:
                if ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=data_mais_atual).exists():
                    patrimonio += (qtd_papeis[fii] * ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=data_mais_atual) \
                                   .order_by('-data_hora')[0].preco_unitario)
                else:
                    patrimonio += (qtd_papeis[fii] * HistoricoFII.objects.filter(fii__ticker=fii).order_by('-data')[0].preco_unitario)
                
        graf_patrimonio += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(patrimonio)]]
    
    lista_conjunta = [item for item in lista_conjunta if item.quantidade != 0]
    
    dados = {}
    dados['total_proventos'] = total_proventos
    dados['total_gasto'] = -total_gasto
    dados['patrimonio'] = patrimonio
    dados['lucro'] = patrimonio + total_proventos + total_gasto
    dados['lucro_percentual'] = (patrimonio + total_proventos + total_gasto) / -total_gasto * 100
    return TemplateResponse(request, 'fii/historico.html', {'dados': dados, 'lista_conjunta': lista_conjunta, 'graf_poupanca_proventos': graf_poupanca_proventos, 
                                                     'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio, 'lista_eventos': ['Agrupamento', 'Desdobramento', 'Incorporação']})
    
    
@login_required
@adiciona_titulo_descricao('Inserir operação em FII', 'Inserir registro de operação de compra/venda em Fundos de Investimento Imobiliário')
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
                    return HttpResponseRedirect(reverse('fii:historico_fii'))
                
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
                    return HttpResponseRedirect(reverse('fii:historico_fii'))
        for erro in [erro for erro in form_operacao_fii.non_field_errors()]:
            messages.error(request, erro)    
                    
    else:
        form_operacao_fii = OperacaoFIIForm()
        form_uso_proventos = UsoProventosOperacaoFIIForm(initial={'qtd_utilizada': Decimal('0.00')})
        formset_divisao = DivisaoFormSet(investidor=investidor)
            
    return TemplateResponse(request, 'fii/inserir_operacao_fii.html', {'form_operacao_fii': form_operacao_fii, 'form_uso_proventos': form_uso_proventos,
                                                               'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})


@login_required
@user_passes_test(is_superuser)
def inserir_provento_fii(request):
    if request.method == 'POST':
        form = ProventoFIIForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('fii:historico_fii'))
    else:
        form = ProventoFIIForm()
            
    return TemplateResponse(request, 'fii/inserir_provento_fii.html', {'form': form})

@adiciona_titulo_descricao('Painel de FII', 'Posição atual do investidor em Fundos de Investimento Imobiliário')
def painel(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'fii/painel.html', {'fiis': list(), 'dados': {}})
        
    fiis = {}
     
    qtd_fiis = calcular_qtd_fiis_ate_dia(investidor)
    preco_medio_fiis = calcular_preco_medio_fiis_ate_dia(investidor)
     
    for ticker, qtd in qtd_fiis.items():
        novo_fii = Object()
        novo_fii.quantidade = qtd
        novo_fii.preco_medio = preco_medio_fiis[ticker]
        novo_fii.total_investido = novo_fii.preco_medio * novo_fii.quantidade
        fiis[ticker] = novo_fii
         
    total_papeis = 0      
    total_valor = 0
    # Preencher totais
    for fii in fiis.keys():
        total_papeis += fiis[fii].quantidade
        if ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=datetime.date.today()).exists():
            fiis[fii].valor = ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=datetime.date.today()).order_by('-data_hora')[0].preco_unitario
        else:
            fiis[fii].valor = HistoricoFII.objects.filter(fii__ticker=fii).order_by('-data')[0].preco_unitario
        fiis[fii].valor_total = fiis[fii].valor * fiis[fii].quantidade
        total_valor += fiis[fii].valor_total
         
    # Calcular percentagens
    for fii in fiis.keys():
        fiis[fii].quantidade_percentual = fiis[fii].quantidade / total_papeis * 100
        fiis[fii].valor_total_percentual = fiis[fii].valor_total / total_valor * 100
     
    # Popular dados
    dados = {}
    dados['total_papeis'] = total_papeis
    dados['total_valor'] = total_valor
    dados['valor_diario_mais_recente'] = 'N/A' if not ValorDiarioFII.objects.exists() else ValorDiarioFII.objects.latest('data_hora').data_hora
    
    return TemplateResponse(request, 'fii/painel.html', {'fiis': fiis, 'dados': dados})

@adiciona_titulo_descricao('Sobre FII', 'Detalha o que são Fundos de Investimento Imobiliário')
def sobre(request):
    if request.user.is_authenticated():
        total_atual = sum(calcular_valor_fii_ate_dia(request.user.investidor).values())
        total_atual += calcular_poupanca_prov_fii_ate_dia(request.user.investidor)
    else:
        total_atual = 0
    
    return TemplateResponse(request, 'fii/sobre.html', {'total_atual': total_atual})