# -*- coding: utf-8 -*-
import calendar
import datetime
from decimal import Decimal, ROUND_FLOOR
from itertools import chain
import json
import math
from operator import attrgetter
import re
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When, Value
from django.db.models.fields import CharField, DecimalField
from django.db.models.query_utils import Q
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.http.response import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse

from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoFIIFormSet
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII, Divisao
from bagogold.bagogold.models.gerador_proventos import ProventoFIIDocumento, \
    InvestidorValidacaoDocumento
from bagogold.bagogold.utils.investidores import is_superuser, \
    buscar_proventos_a_receber
from bagogold.fii.forms import OperacaoFIIForm, ProventoFIIForm, \
    UsoProventosOperacaoFIIForm, CalculoResultadoCorretagemForm
from bagogold.fii.models import OperacaoFII, ProventoFII, HistoricoFII, FII, \
    UsoProventosOperacaoFII, ValorDiarioFII, EventoAgrupamentoFII, \
    EventoDesdobramentoFII, EventoIncorporacaoFII
from bagogold.fii.utils import calcular_valor_fii_ate_dia, \
    calcular_poupanca_prov_fii_ate_dia, calcular_qtd_fiis_ate_dia_por_ticker, \
    calcular_preco_medio_fiis_ate_dia, calcular_qtd_fiis_ate_dia, \
    calcular_preco_medio_fiis_ate_dia_por_ticker


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

    ultimos_valores_diarios = {fii_id: (data_hora, valor) for fii_id, data_hora, valor in ValorDiarioFII.objects.all().order_by('fii__id', '-data_hora') \
                               .distinct('fii__id').values_list('fii', 'data_hora', 'preco_unitario')}    
    ultimos_historicos = {fii_id: (data, valor) for fii_id, data, valor in HistoricoFII.objects.all().order_by('fii__id', '-data') \
                          .distinct('fii__id').values_list('fii', 'data', 'preco_unitario')}
    
    filtros = {}
    
    if request.method == 'POST':
        filtros['mes_inicial'] = request.POST.get('mes_inicial')
        try:
            filtros['mes_inicial'] = datetime.datetime.strptime('01/%s' % (filtros['mes_inicial']), '%d/%m/%Y').date()
        except:
            messages.error(request, 'Mês inicial enviado é inválido')
            # Calcular a data de inicio, buscando o primeiro dia do próximo mês, no ano passado, a fim de completar um ciclo de 12 meses
            mes_inicial = datetime.date.today()
            ultimo_dia_mes = calendar.monthrange(mes_inicial.year, mes_inicial.month)[1]
            filtros['mes_inicial'] = mes_inicial.replace(day=ultimo_dia_mes).replace(year=mes_inicial.year-1) + datetime.timedelta(days=1)
            
        filtros['ignorar_indisponiveis'] = request.POST.get('ignorar_indisponiveis', False)
    else:
        # Calcular a data de inicio, buscando o primeiro dia do próximo mês, no ano passado, a fim de completar um ciclo de 12 meses
        mes_inicial = datetime.date.today()
        ultimo_dia_mes = calendar.monthrange(mes_inicial.year, mes_inicial.month)[1]
        filtros['mes_inicial'] = mes_inicial.replace(day=ultimo_dia_mes).replace(year=mes_inicial.year-1) + datetime.timedelta(days=1)
        filtros['ignorar_indisponiveis'] = True
        
    # Verificar o período em meses de diferença (se mesmo mês/ano, deve ser 1)
    periodo_meses = 1 + datetime.date.today().month - filtros['mes_inicial'].month \
        + (datetime.date.today().year - filtros['mes_inicial'].year) * 12
    for fii in fiis:
#         total_proventos = 0
        # Calcular media de proventos dos ultimos 6 recebimentos
        proventos = ProventoFII.objects.filter(fii=fii, data_pagamento__range=[filtros['mes_inicial'], datetime.date.today()])
#         if len(proventos) > 6:
#             proventos = proventos[0:6]
#         if len(proventos) > 0:
#             qtd_dias_periodo = (datetime.date.today() - proventos[len(proventos)-1].data_ex).days
#         else:
#             continue
        totais_tipos_provento = proventos.values('tipo_provento').annotate(total=Sum('valor_unitario'))
        fii.total_amortizacoes = 0
        fii.total_rendimentos = 0
        for total_tipo_provento in totais_tipos_provento:
            if total_tipo_provento['tipo_provento'] == ProventoFII.TIPO_PROVENTO_AMORTIZACAO:
                fii.total_amortizacoes = total_tipo_provento['total']
            elif total_tipo_provento['tipo_provento'] == ProventoFII.TIPO_PROVENTO_RENDIMENTO:
                fii.total_rendimentos = total_tipo_provento['total']
        fii.total_proventos = fii.total_amortizacoes + fii.total_rendimentos
            
        # Pegar valor atual dos FIIs
        if fii.id in ultimos_valores_diarios.keys():
            preco_unitario = ultimos_valores_diarios[fii.id][1]
            data_hora = ultimos_valores_diarios[fii.id][0].date()
            if data_hora == datetime.date.today():
                fii.valor_atual = preco_unitario
                fii.data = data_hora
                fii.percentual_retorno = (fii.total_rendimentos/fii.valor_atual) * 100
                
        else:
            # Pegar último dia util com negociação da ação para calculo do patrimonio
            if fii.id in ultimos_historicos.keys():
                fii.valor_atual = ultimos_historicos[fii.id][1]
                fii.data = ultimos_historicos[fii.id][0]
                # Percentual do retorno sobre o valor do fundo
                fii.percentual_retorno = (fii.total_rendimentos/fii.valor_atual) * 100
            else:
#                 fii.valor_atual = 0
                fii.data = None
                continue
                # Percentual do retorno sobre o valor do fundo
#                 fii.percentual_retorno = 0
        
        # Taxa mensal a partir da quantidade de dias
        fii.percentual_retorno_mensal = 100*(math.pow(1 + fii.percentual_retorno/100, 1/Decimal(periodo_meses)) - 1)
        # Taxa anual
        fii.percentual_retorno_anual = 100*(math.pow(1 + fii.percentual_retorno_mensal/100, 12) - 1)
#         comparativos += [[fii, valor_atual, total_proventos, percentual_retorno_semestral]]
    
    # Ignorar os FIIs cujos valores não foram encontrados
    if filtros['ignorar_indisponiveis']:
        fiis = [fii for fii in fiis if fii.data != None]

    return TemplateResponse(request, 'fii/acompanhamento.html', {'fiis': fiis, 'filtros': filtros})
    
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
    
def detalhar_fii_id(request, fii_id):
    fii = get_object_or_404(FII, id=fii_id)
    return HttpResponsePermanentRedirect(reverse('fii:detalhar_fii', kwargs={'fii_ticker': fii.ticker}))
    
    
@adiciona_titulo_descricao('Detalhar FII', 'Detalhamento de um FII')
def detalhar_fii(request, fii_ticker):
    fii = get_object_or_404(FII, ticker=fii_ticker)
    
    if HistoricoFII.objects.filter(fii=fii).exists():
        registro_historico_atual = HistoricoFII.objects.filter(fii=fii).order_by('-data')[0]
        fii.valor_atual = registro_historico_atual.preco_unitario
        fii.data_valor_atual = registro_historico_atual.data
    else:
        fii.valor_atual = None
        fii.data_valor_atual = None
        
    
    proventos = ProventoFII.objects.filter(fii=fii).annotate(tipo=Case(When(tipo_provento=ProventoFII.TIPO_PROVENTO_AMORTIZACAO, then=Value(u'Amortização')),
                                                                       When(tipo_provento=ProventoFII.TIPO_PROVENTO_RENDIMENTO, then=Value(u'Rendimento')), output_field=CharField())) \
                                                   .order_by('data_ex')
    
    if proventos.exists():
        rendimentos = proventos.filter(tipo_provento=ProventoFII.TIPO_PROVENTO_RENDIMENTO)
        if rendimentos.exists():
            ultimo_rendimento = rendimentos.order_by('-data_ex')[0]
            fii.ultimo_provento = ultimo_rendimento.valor_unitario
            fii.data_ultimo_provento = ultimo_rendimento.data_pagamento
        else:
            fii.ultimo_provento = None
            fii.data_ultimo_provento = None
    else:
        fii.ultimo_provento = None
        fii.data_ultimo_provento = None

    # Calcular percentual de rendimento do ultimo provento
    if fii.valor_atual and fii.ultimo_provento:
        fii.percentual_rendimento_ult_prov = 100 * fii.ultimo_provento / fii.valor_atual
    else:
        fii.percentual_rendimento_ult_prov = 0
    
    # Se usuário autenticado, mostrar operações e proventos recebidos
    if request.user.is_authenticated():
        investidor = request.user.investidor
        # Buscar operações
        operacoes = OperacaoFII.objects.filter(investidor=investidor, fii=fii).annotate(tipo=Case(When(tipo_operacao='C', then=Value(u'Compra')),
                                                                                                  When(tipo_operacao='V', then=Value(u'Venda')), output_field=CharField())) \
                                      .annotate(taxas=F('emolumentos') + F('corretagem')) \
                                      .annotate(total=Case(When(tipo_operacao='C', then=-1 * (F('quantidade') * F('preco_unitario') + F('emolumentos') + F('corretagem'))),
                                                           When(tipo_operacao='V', then=F('quantidade') * F('preco_unitario') - F('emolumentos') - F('corretagem')),
                                                           output_field=DecimalField())) \
                                      .order_by('data')
        
        fii.qtd_cotas = calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date.today(), fii.ticker)
        fii.preco_medio = calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date.today(), fii.ticker)
        
        fii.total_provento_recebido = 0
        
        if operacoes.exists():
            # Adicionar utilização de proventos
            for operacao in operacoes:
                operacao.uso_proventos = Decimal(0)
                if operacao.utilizou_proventos():
                    operacao.uso_proventos += operacao.qtd_proventos_utilizada()
                    
            proventos = list(proventos)
#             for provento in proventos.filter(data_ex__gt=operacoes[0].data):
            for provento in [provento for provento in proventos if provento.data_ex > operacoes[0].data]:
                provento.pago = datetime.date.today() >= provento.data_pagamento
                provento.qtd_na_data_base = calcular_qtd_fiis_ate_dia_por_ticker(request.user.investidor, provento.data_ex-datetime.timedelta(days=1), provento.fii.ticker)
                provento.valor_recebido = (provento.qtd_na_data_base * provento.valor_unitario).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
                fii.total_provento_recebido += provento.valor_recebido
    else:
        operacoes = list()
        
    # Preparar gráfico histórico
    historico = [[str(calendar.timegm(data.timetuple()) * 1000), float(preco_unitario)] for (data, preco_unitario) in HistoricoFII.objects.filter(fii=fii).values_list('data', 'preco_unitario').order_by('data')]

    return TemplateResponse(request, 'fii/detalhar_fii.html', {'fii': fii, 'historico': historico, 'operacoes': operacoes, 'proventos': proventos})
    
@adiciona_titulo_descricao('Detalhar provento', 'Detalhamento de proventos em FIIs')
def detalhar_provento(request, provento_id):
    provento = get_object_or_404(ProventoFII, pk=provento_id)
    
    documentos = ProventoFIIDocumento.objects.filter(provento=provento).order_by('-versao')
    
    # Se usuário autenticado, mostrar dados do recebimento do provento
    if request.user.is_authenticated():
        provento.pago = datetime.date.today() > provento.data_pagamento
        provento.qtd_na_data_ex = calcular_qtd_fiis_ate_dia_por_ticker(request.user.investidor, provento.data_ex, provento.fii.ticker)
        provento.valor_recebido = (provento.qtd_na_data_ex * provento.valor_unitario).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
    
    # Preencher última versão
    provento.ultima_versao = documentos[0].versao
    
    return TemplateResponse(request, 'fii/detalhar_provento.html', {'provento': provento, 'documentos': documentos})

@login_required
@adiciona_titulo_descricao('Editar operação em FII', 'Alterar valores de uma operação de compra/venda em Fundos de Investimento Imobiliário')
def editar_operacao_fii(request, id_operacao):
    investidor = request.user.investidor
    
    operacao_fii = get_object_or_404(OperacaoFII, pk=id_operacao)
    
    # Verificar se a operação é do investidor logado
    if operacao_fii.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoFII, DivisaoOperacaoFII, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoFIIFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = Divisao.objects.filter(investidor=investidor).count() > 1
    
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
                        try:
                            with transaction.atomic():
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
                                            # Criar uso de proventos para divisão
                                            if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] != None and form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] > 0:
                                                # TODO remover operação de uso proventos
                                                divisao_operacao.usoproventosoperacaofii = UsoProventosOperacaoFII(qtd_utilizada=form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'], operacao=operacao_fii)
                                                divisao_operacao.usoproventosoperacaofii.save()
                        except:
                            messages.error(request, 'Houve um erro ao editar a operação')
                            if settings.ENV == 'DEV':
                                raise
                            elif settings.ENV == 'PROD':
                                mail_admins(u'Erro ao editar operação em FII com várias divisões', traceback.format_exc().decode('utf-8'))
                        
                        messages.success(request, 'Operação alterada com sucesso')
                        return HttpResponseRedirect(reverse('fii:historico_fii'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                    
                else:    
                    if form_uso_proventos.is_valid():
                        try:
                            with transaction.atomic():
                                operacao_fii.save()
                                divisao_operacao = DivisaoOperacaoFII.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_fii)
                                divisao_operacao.quantidade = operacao_fii.quantidade
                                divisao_operacao.save()
                                uso_proventos = form_uso_proventos.save(commit=False)
                                if uso_proventos.qtd_utilizada > 0:
                                    uso_proventos.operacao = operacao_fii
#                                     uso_proventos.divisao_operacao = DivisaoOperacaoFII.objects.get(operacao=operacao_fii)
                                    uso_proventos.divisao_operacao = divisao_operacao
                                    uso_proventos.save()
                                # Se uso proventos for 0 e existir uso proventos atualmente, apagá-lo
                                elif uso_proventos.qtd_utilizada == 0 and UsoProventosOperacaoFII.objects.filter(divisao_operacao__operacao=operacao_fii).exists():
                                    uso_proventos.delete()
                        except:
                            messages.error(request, 'Houve um erro ao editar a operação')
                            if settings.ENV == 'DEV':
                                raise
                            elif settings.ENV == 'PROD':
                                mail_admins(u'Erro ao editar operação em FII com uma divisão', traceback.format_exc().decode('utf-8'))
                        messages.success(request, 'Operação alterada com sucesso')
                        return HttpResponseRedirect(reverse('fii:historico_fii'))
                        
            for erro in form_operacao_fii.non_field_errors():
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
        
    operacoes = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).annotate(valor_unitario=F('preco_unitario')) \
                                        .annotate(tipo=Case(When(tipo_operacao='C', then=Value(u'Compra')),
                                                            When(tipo_operacao='V', then=Value(u'Venda')), output_field=CharField())) \
                                        .annotate(total=Case(When(tipo_operacao='C', then=-1 * (F('quantidade') * F('preco_unitario') + F('emolumentos') + F('corretagem'))),
                                                            When(tipo_operacao='V', then=F('quantidade') * F('preco_unitario') - F('emolumentos') - F('corretagem')),
                                                            output_field=DecimalField())) \
                                        .annotate(fii_ticker=F('fii__ticker')) \
                                        .order_by('data').prefetch_related('usoproventosoperacaofii_set')
    
    # Se investidor não tiver feito operações
    if not operacoes:
        return TemplateResponse(request, 'fii/historico.html', {'dados': {}, 'lista_conjunta': list(), 'graf_poupanca_proventos': list(), 
                                                     'graf_gasto_total': list(), 'graf_patrimonio': list(), 'lista_eventos': list()})
    
    # Proventos
    proventos = ProventoFII.objects.exclude(data_ex__isnull=True).exclude(data_ex__gt=datetime.date.today()).filter(data_ex__gt=operacoes[0].data, fii__in=operacoes.values_list('fii', flat=True)) \
        .annotate(tipo=Value(u'Provento', output_field=CharField())).annotate(data=F('data_ex')).annotate(fii_ticker=F('fii__ticker')).order_by('data_ex')  
    
    # Eventos
    agrupamentos = EventoAgrupamentoFII.objects.filter(fii__in=operacoes.values_list('fii', flat=True), data__lte=datetime.date.today()) \
        .annotate(tipo=Value(u'Agrupamento', output_field=CharField())).annotate(valor_unitario=F('proporcao')) \
        .annotate(fii_ticker=F('fii__ticker')).order_by('data') 

    desdobramentos = EventoDesdobramentoFII.objects.filter(fii__in=operacoes.values_list('fii', flat=True), data__lte=datetime.date.today()) \
        .annotate(tipo=Value(u'Desdobramento', output_field=CharField())).annotate(valor_unitario=F('proporcao')) \
        .annotate(fii_ticker=F('fii__ticker')).order_by('data')
    
    incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__in=operacoes.values_list('fii', flat=True), data__lte=datetime.date.today()) \
                                                         | Q(novo_fii__in=operacoes.values_list('fii', flat=True), data__lte=datetime.date.today())).annotate(tipo=Value(u'Incorporação', output_field=CharField())) \
                                                         .annotate(valor_unitario=F('novo_fii__ticker')) \
                                                         .annotate(fii_ticker=F('fii__ticker')).select_related('novo_fii').order_by('data')

    
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
        if item.fii_ticker not in qtd_papeis.keys():
            qtd_papeis[item.fii_ticker] = Decimal(0)       
        # Verificar se se trata de compra, venda ou provento
        if item.tipo == 'Compra':
            item.uso_proventos = Decimal(0)
            if item.utilizou_proventos():
                item.uso_proventos += item.qtd_proventos_utilizada()
                total_proventos -= item.uso_proventos
#             item.total = Decimal(-1) * (item.quantidade * item.preco_unitario + \
#             item.emolumentos + item.corretagem)
            total_gasto += item.total + item.uso_proventos
            qtd_papeis[item.fii_ticker] += item.quantidade
            
        elif item.tipo == 'Venda':
#             item.total = (item.quantidade * item.preco_unitario - \
#             item.emolumentos - item.corretagem)
            total_gasto += item.total
            qtd_papeis[item.fii_ticker] -= item.quantidade
                
        elif item.tipo == 'Provento':
            if qtd_papeis[item.fii_ticker] == 0:
                item.quantidade = 0
                continue
            item.total = (qtd_papeis[item.fii_ticker] * item.valor_unitario).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
            item.quantidade = qtd_papeis[item.fii_ticker]
            if item.data_pagamento <= datetime.date.today():
                total_proventos += item.total
            
        elif item.tipo == 'Agrupamento':
            if qtd_papeis[item.fii_ticker] == 0:
                item.quantidade = 0
                continue
            item.quantidade = qtd_papeis[item.fii_ticker]
            qtd_papeis[item.fii_ticker] = item.qtd_apos(item.quantidade)
            item.total = qtd_papeis[item.fii_ticker]
                        
        elif item.tipo == 'Desdobramento':
            if qtd_papeis[item.fii_ticker] == 0:
                item.quantidade = 0
                continue
            item.quantidade = qtd_papeis[item.fii_ticker]
            qtd_papeis[item.fii_ticker] = item.qtd_apos(item.quantidade)
            item.total = qtd_papeis[item.fii_ticker]
            
        elif item.tipo == 'Incorporação':
            if qtd_papeis[item.fii_ticker] == 0:
                item.quantidade = 0
                continue
            item.quantidade = qtd_papeis[item.fii_ticker]
            item.total = qtd_papeis[item.fii_ticker]
            qtd_papeis[item.novo_fii.ticker] += qtd_papeis[item.fii_ticker]
            qtd_papeis[item.fii_ticker] = 0
            # Remover do dict qtd_papeis
            del qtd_papeis[item.fii_ticker]
            
        # Verifica se próximo elemento possui a mesma data
        if indice == len(lista_conjunta) - 1 or item.data != lista_conjunta[indice+1].data:
            # Prepara data
            data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
            
            graf_poupanca_proventos += [[data_formatada, float(total_proventos)]]
            graf_gasto_total += [[data_formatada, float(-total_gasto)]]
            
            patrimonio = 0
            # Verifica se houve operacao hoje
            if item.data != datetime.date.today():
                # Pegar último dia util com negociação do fii para calculo do patrimonio
                ultimos_historicos = {ticker: valor for ticker, valor in HistoricoFII.objects.filter(fii__ticker__in=qtd_papeis, data__lte=item.data).order_by('fii__ticker', '-data') \
                          .distinct('fii__ticker').values_list('fii__ticker', 'preco_unitario')}
                for fii in qtd_papeis:
                    patrimonio += qtd_papeis[fii] * ultimos_historicos[fii]
            else:
                houve_operacao_hoje = True
                for fii in qtd_papeis:
                    # Tenta pegar valor diario, se nao houver, pegar historico do ultimo dia util
                    if ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=datetime.date.today()).exists():
                        patrimonio += (Decimal(qtd_papeis[fii]) * ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=datetime.date.today()).order_by('-data_hora')[0].preco_unitario)
                    else:
                        patrimonio += (Decimal(qtd_papeis[fii]) * HistoricoFII.objects.filter(fii__ticker=fii).order_by('-data')[0].preco_unitario)
            graf_patrimonio += [[data_formatada, float(patrimonio)]]
        
    # Adicionar valor mais atual para todos os gráficos
    if not houve_operacao_hoje:
        data_atual = datetime.date.today()
        graf_poupanca_proventos += [[str(calendar.timegm(data_atual.timetuple()) * 1000), float(total_proventos)]]
        graf_gasto_total += [[str(calendar.timegm(data_atual.timetuple()) * 1000), float(-total_gasto)]]
        
        # Buscar valores diários e históricos
        ultimos_valores_diarios = {ticker: valor for ticker, valor in \
                                   ValorDiarioFII.objects.filter(fii__ticker__in=qtd_papeis, data_hora__date=data_atual).order_by('fii__id', '-data_hora') \
                                   .distinct('fii__id').values_list('fii__ticker', 'preco_unitario')}    
        ultimos_historicos = {ticker: valor for ticker, valor in HistoricoFII.objects.filter(fii__ticker__in=qtd_papeis, data__lte=data_atual).order_by('fii__ticker', '-data') \
                              .distinct('fii__ticker').values_list('fii__ticker', 'preco_unitario')}
        
        patrimonio = 0
        for fii in qtd_papeis:
            if qtd_papeis[fii] > 0:
                if fii in ultimos_valores_diarios:
                    patrimonio += (qtd_papeis[fii] * ultimos_valores_diarios[fii])
                else:
                    patrimonio += (qtd_papeis[fii] * ultimos_historicos[fii])
                
        graf_patrimonio += [[str(calendar.timegm(data_atual.timetuple()) * 1000), float(patrimonio)]]
    
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
    varias_divisoes = Divisao.objects.filter(investidor=investidor).count() > 1
    
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
        for erro in form_operacao_fii.non_field_errors():
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

@adiciona_titulo_descricao('Lista de proventos', 'Lista os proventos de FIIs cadastrados')
def listar_proventos(request):
    # Montar filtros
    if request.is_ajax():
        filtros = {}
        # Preparar filtro por tipo de investimento
        filtros['tipo_provento'] = request.GET.get('tipo', 'T')
        if filtros['tipo_provento'] == 'T':
            query_proventos = ProventoFII.objects.all()
        else:
            query_proventos = ProventoFII.objects.filter(tipo_provento=filtros['tipo_provento'])
            
        filtros['fiis'] = re.sub(r'[^,\d]', '', request.GET.get('fiis', ''))
        if filtros['fiis'] != '':
            query_proventos = query_proventos.filter(fii__id__in=filtros['fiis'].split(','))
            
        # Preparar filtros para datas
        # Início data EX
        filtros['inicio_data_ex'] = request.GET.get('inicio_data_ex', '')
        if filtros['inicio_data_ex'] != '':
            try:
                query_proventos = query_proventos.filter(data_ex__gte=datetime.datetime.strptime(filtros['inicio_data_ex'], '%d/%m/%Y'))
            except:
                filtros['inicio_data_ex'] = ''
        # Fim data EX
        filtros['fim_data_ex'] = request.GET.get('fim_data_ex', '')
        if filtros['fim_data_ex'] != '':
            try:
                query_proventos = query_proventos.filter(data_ex__lte=datetime.datetime.strptime(filtros['fim_data_ex'], '%d/%m/%Y'))
            except:
                filtros['fim_data_ex'] = ''
        # Início data pagamento
        filtros['inicio_data_pagamento'] = request.GET.get('inicio_data_pagamento', '')
        if filtros['inicio_data_pagamento'] != '':
            try:
                query_proventos = query_proventos.filter(data_pagamento__gte=datetime.datetime.strptime(filtros['inicio_data_pagamento'], '%d/%m/%Y'))
            except:
                filtros['inicio_data_pagamento'] = ''
        # Fim data pagamento
        filtros['fim_data_pagamento'] = request.GET.get('fim_data_pagamento', '')
        if filtros['fim_data_pagamento'] != '':
            try:
                query_proventos = query_proventos.filter(data_pagamento__lte=datetime.datetime.strptime(filtros['fim_data_pagamento'], '%d/%m/%Y'))
            except:
                filtros['fim_data_pagamento'] = ''
                
        proventos = list(query_proventos.select_related('fii'))
        return HttpResponse(json.dumps(render_to_string('fii/utils/lista_proventos.html', {'proventos': proventos})), content_type = "application/json")  
    else:
        filtros = {'tipo_provento': 'T', 'inicio_data_ex': '', 'fim_data_ex': '', 'inicio_data_pagamento': '', 'fim_data_pagamento': '', 'fiis': ''}
    
    # Buscar últimas atualizações
    ultimas_validacoes = InvestidorValidacaoDocumento.objects.filter(documento__tipo='F').order_by('-data_validacao')[:10] \
        .annotate(provento=F('documento__proventofiidocumento__provento')).values('provento', 'data_validacao')
    ultimas_atualizacoes = ProventoFII.objects.filter(id__in=[validacao['provento'] for validacao in ultimas_validacoes]).select_related('fii')
    for atualizacao in ultimas_atualizacoes:
        atualizacao.data_insercao = next(validacao['data_validacao'].date() for validacao in ultimas_validacoes if validacao['provento'] == atualizacao.id)
    
    if request.user.is_authenticated():
        proximos_proventos = buscar_proventos_a_receber(request.user.investidor, 'F')
    else:
        proximos_proventos = list()
    
    return TemplateResponse(request, 'fii/listar_proventos.html', {'ultimas_atualizacoes': ultimas_atualizacoes, 'proximos_proventos': proximos_proventos,
                                                                   'filtros': filtros})

def listar_tickers_fiis(request):
    return HttpResponse(json.dumps(render_to_string('fii/utils/listar_tickers.html', {'fiis': FII.objects.all().order_by('ticker')})), content_type = "application/json")  

@adiciona_titulo_descricao('Painel de FII', 'Posição atual do investidor em Fundos de Investimento Imobiliário')
def painel(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'fii/painel.html', {'fiis': {}, 'dados': {}, 'graf_composicao': list(), 'graf_valorizacao': list()})
        
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
    for fii in fiis:
        total_papeis += fiis[fii].quantidade
        if ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=datetime.date.today()).exists():
            fiis[fii].valor = ValorDiarioFII.objects.filter(fii__ticker=fii, data_hora__date=datetime.date.today()).order_by('-data_hora')[0].preco_unitario
        else:
            fiis[fii].valor = HistoricoFII.objects.filter(fii__ticker=fii).order_by('-data')[0].preco_unitario
        fiis[fii].valor_total = fiis[fii].valor * fiis[fii].quantidade
        total_valor += fiis[fii].valor_total
         
    # Calcular porcentagens
    for fii in fiis:
        fiis[fii].quantidade_percentual = Decimal(fiis[fii].quantidade) / total_papeis * 100
        fiis[fii].valor_total_percentual = fiis[fii].valor_total / total_valor * 100
     
    # Gráfico de composição
    graf_composicao = [{'label': str(fii), 'data': float(fiis[fii].valor_total_percentual)} for fii in fiis]
    
    # Gráfico de valorização
    graf_valorizacao = [{'label': str(fii), 'data': float(((fiis[fii].valor - fiis[fii].preco_medio)/fiis[fii].preco_medio * 100).quantize(Decimal('0.01')))} for fii in sorted(fiis.keys())]
    
    # Popular dados
    dados = {}
    dados['total_papeis'] = total_papeis
    dados['total_valor'] = total_valor
    if ValorDiarioFII.objects.filter(data_hora__date=datetime.date.today()).exists():
        dados['valor_diario_mais_recente'] = ValorDiarioFII.objects.order_by('-data_hora').values_list('data_hora', flat=True)[0]
    else:
        dados['valor_diario_mais_recente'] = HistoricoFII.objects.order_by('-data').values_list('data', flat=True)[0]
    
    return TemplateResponse(request, 'fii/painel.html', {'fiis': fiis, 'dados': dados, 'graf_composicao': graf_composicao, 'graf_valorizacao': graf_valorizacao})

@adiciona_titulo_descricao('Sobre FII', 'Detalha o que são Fundos de Investimento Imobiliário')
def sobre(request):
    if request.user.is_authenticated():
        total_atual = sum(calcular_valor_fii_ate_dia(request.user.investidor).values())
        total_atual += calcular_poupanca_prov_fii_ate_dia(request.user.investidor)
    else:
        total_atual = 0
    
    return TemplateResponse(request, 'fii/sobre.html', {'total_atual': total_atual})