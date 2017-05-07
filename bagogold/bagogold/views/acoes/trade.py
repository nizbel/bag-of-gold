# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoAcaoFormSet
from bagogold.bagogold.forms.operacao_acao import OperacaoAcaoForm, \
    UsoProventosOperacaoAcaoForm
from bagogold.bagogold.forms.operacao_compra_venda import \
    OperacaoCompraVendaForm
from bagogold.bagogold.models.acoes import OperacaoAcao, OperacaoCompraVenda, \
    UsoProventosOperacaoAcao
from bagogold.bagogold.models.divisoes import Divisao, \
    TransferenciaEntreDivisoes, DivisaoOperacaoAcao
from bagogold.bagogold.utils.acoes import calcular_lucro_trade_ate_data, \
    calcular_poupanca_prov_acao_ate_dia
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Sum
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template.response import TemplateResponse
from itertools import chain
import calendar
import datetime
import json
import operator

LISTA_MESES = [['Janeiro', 1],   ['Fevereiro', 2],
               ['Março', 3],     ['Abril', 4],
               ['Maio', 5],      ['Junho', 6],
               ['Julho', 7],     ['Agosto', 8],
               ['Setembro', 9],  ['Outubro', 10],
               ['Novembro', 11], ['Dezembro', 12],
               ]

@login_required
@adiciona_titulo_descricao('Acompanhamento mensal de Trading', 'Mostra acumulados mensais para operações em Ações para Trading')
def acompanhamento_mensal(request):
    investidor = request.user.investidor
    
    # TODO validar entradas
    ano = int(request.GET.get('ano', datetime.date.today().year))
    mes = int(request.GET.get('mes', datetime.date.today().month))
    
    # Pegar primeiro ano que uma operação foi feita
    if OperacaoAcao.objects.filter(destinacao='T', investidor=investidor).exclude(data__isnull=True).order_by('data').exists():
        primeira_operacao = OperacaoAcao.objects.filter(destinacao='T', investidor=investidor).exclude(data__isnull=True).order_by('data')[0]
        primeira_operacao_ano = primeira_operacao.data.year
    else:
        primeira_operacao_ano = datetime.date.today().year
    
    # Preparar lista de anos
    lista_anos = list()
    for ano_operacoes in reversed(range(primeira_operacao_ano, datetime.date.today().year+1)):
#         print type(ano_operacoes)
        lista_anos += [str(ano_operacoes)]
    print lista_anos

    if ano == datetime.date.today().year:
        ultimo_mes = datetime.date.today().month
    else:
        ultimo_mes = 12
    lista_meses = LISTA_MESES
    
#     # Alterar lista de meses
#     if request.is_ajax():
#         return HttpResponse(json.dumps(lista_meses), content_type = "application/json")
        
    operacoes = OperacaoAcao.objects.exclude(data__isnull=True).filter(destinacao='T', investidor=investidor, data__year=ano, data__month=mes).order_by('data')
    
#     if not operacoes:
#         if request.is_ajax():
#             return HttpResponse(json.dumps({'lista_anos': lista_anos, 'lista_meses': lista_meses,
#                                              'dados_mes': {'ultimo_mes': ultimo_mes, 'ano': str(ano).replace('.', ''), 'mes': mes}}), content_type = "application/json")
#         else:
#             return TemplateResponse(request, 'acoes/trade/acompanhamento_mensal.html', {'lista_anos': lista_anos, 'lista_meses': lista_meses, 
#                                                                                         'dados_mes': {'ultimo_mes': ultimo_mes, 'ano': str(ano).replace('.', ''), 'mes': mes},
#                                                                                         'graf_compras_mes': {}, 'graf_vendas_mes': {}, 'graf_lucro_mes': {}})
        
    graf_compras_mes = list()
    graf_vendas_mes = list()
    graf_lucro_mes = list()
    operacoes_compra = {}
    operacoes_venda = {}
    
    # Calcula o saldo para Trades inicial do mês
    saldo_inicial_mes = 0
    for divisao in Divisao.objects.filter():
        saldo_inicial_mes += divisao.saldo_acoes_trade(data=datetime.date(ano, mes, 1) - datetime.timedelta(days=1))
    
    dados_mes = {'ultimo_mes': ultimo_mes, 'ano': str(ano).replace('.', ''), 'mes': mes, 'qtd_compra': 0, 'qtd_venda': 0, 'qtd_op_compra': 0, 'saldo_trades': saldo_inicial_mes,
                 'qtd_op_venda': 0, 'lucro_bruto': 0, 'total_corretagem' : 0, 'total_emolumentos': 0}
    acoes_lucro = {}
    
    # TODO considerar compras/vendas
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            dados_mes['qtd_compra'] += operacao.quantidade * operacao.preco_unitario 
            dados_mes['qtd_op_compra'] += 1
            compra_com_taxas = operacao.quantidade * operacao.preco_unitario + operacao.emolumentos + operacao.corretagem
            dados_mes['saldo_trades'] -= compra_com_taxas
            
            if str(calendar.timegm(operacao.data.timetuple()) * 1000) in operacoes_compra:
                operacoes_compra[str(calendar.timegm(operacao.data.timetuple()) * 1000)] += float(-compra_com_taxas)
            else:
                operacoes_compra[str(calendar.timegm(operacao.data.timetuple()) * 1000)] = float(-compra_com_taxas)
                        
        elif operacao.tipo_operacao == 'V':
            dados_mes['qtd_venda'] += operacao.quantidade * operacao.preco_unitario
            dados_mes['qtd_op_venda'] += 1
            venda_com_taxas = operacao.quantidade * operacao.preco_unitario - operacao.emolumentos - operacao.corretagem
            dados_mes['saldo_trades'] += venda_com_taxas
            
            if str(calendar.timegm(operacao.data.timetuple()) * 1000) in operacoes_venda:
                operacoes_venda[str(calendar.timegm(operacao.data.timetuple()) * 1000)] += float(venda_com_taxas)
            else:
                operacoes_venda[str(calendar.timegm(operacao.data.timetuple()) * 1000)] = float(venda_com_taxas)
            
            # Calcular lucro bruto da operação de venda
            # Pegar operações de compra
            # TODO PREPARAR CASO DE MUITAS COMPRAS PARA MUITAS VENDAS
            qtd_compra = 0
            gasto_total_compras = 0
            for operacao_compra in operacao.venda.get_queryset().order_by('compra__preco_unitario'):
                qtd_compra += min(operacao_compra.compra.quantidade, operacao.quantidade)
                # TODO NAO PREVÊ MUITAS COMPRAS PARA MUITAS VENDAS
                gasto_total_compras += (qtd_compra * operacao_compra.compra.preco_unitario + operacao_compra.compra.emolumentos + \
                                        operacao_compra.compra.corretagem)
            
            lucro_bruto_venda = (operacao.quantidade * operacao.preco_unitario - operacao.corretagem - operacao.emolumentos) - \
                gasto_total_compras
            dados_mes['lucro_bruto'] += lucro_bruto_venda.quantize(Decimal('0.01'))
            
            # Adicionar ao dicionario de lucro por ação
            if operacao.acao.ticker in acoes_lucro:
                acoes_lucro[operacao.acao.ticker] += float(lucro_bruto_venda)
            else:
                acoes_lucro[operacao.acao.ticker] = float(lucro_bruto_venda)
            
            # Adicionar lucro mensal ao gráfico, removendo o ultimo item caso alguma informação sobre o lucro do dia já exista (evitar 2 itens no mesmo dia)
            if len(graf_lucro_mes) > 0:
                ultimo_item = graf_lucro_mes[len(graf_lucro_mes)-1]
                if (ultimo_item[0] == str(calendar.timegm(operacao.data.timetuple()) * 1000)):
                    graf_lucro_mes.remove(ultimo_item)
            graf_lucro_mes += [[str(calendar.timegm(operacao.data.timetuple()) * 1000), float(dados_mes['lucro_bruto'])]]
            
        dados_mes['total_corretagem'] += operacao.corretagem
        dados_mes['total_emolumentos'] += operacao.emolumentos
        
    # Adicionar transferencias ao saldo de trades
    for transferencia in TransferenciaEntreDivisoes.objects.filter(investimento_origem='T', 
                                                                   data__range=[datetime.date(ano, mes, 1), datetime.date(ano, mes, calendar.monthrange(ano,mes)[1])]):
        dados_mes['saldo_trades'] -= transferencia.quantidade
    for transferencia in TransferenciaEntreDivisoes.objects.filter(investimento_destino='T',
                                                                   data__range=[datetime.date(ano, mes, 1), datetime.date(ano, mes, calendar.monthrange(ano,mes)[1])]):
        dados_mes['saldo_trades'] += transferencia.quantidade
    
    # Adicionar pagamentos de proventos
    # TODO Rever a essa forma de calculo
    dados_mes['saldo_trades'] += calcular_poupanca_prov_acao_ate_dia(investidor, datetime.date(ano, mes, calendar.monthrange(ano,mes)[1]), destinacao='T')
    
    # Preparar IR
    if (dados_mes['qtd_venda'] > 20000 and dados_mes['lucro_bruto'] > 0):
        dados_mes['ir_devido'] = float(dados_mes['lucro_bruto']) * 0.15
    else:
        dados_mes['ir_devido'] = 0
        
    # Verificar ações mais e menos lucrativas
    acoes_lucro_ordenado = {}
    if len(acoes_lucro) > 0:
        acoes_lucro_ordenado = sorted(acoes_lucro.items(), key=operator.itemgetter(1), reverse=True)
        dados_mes['mais_lucrativa'] = acoes_lucro_ordenado[0]
        dados_mes['menos_lucrativa'] = acoes_lucro_ordenado[len(acoes_lucro)-1]
    
    # Calcular lucro acumulado até o mes escolhido
    dados_mes['lucro_acumulado'] = calcular_lucro_trade_ate_data(investidor, datetime.date(ano, mes, 1))
    
    # Preencher gráficos de compras e vendas
    for key, value in sorted(operacoes_compra.iteritems(), key=operator.itemgetter(0)):
        graf_compras_mes += [[key, value]]
    for key, value in sorted(operacoes_venda.iteritems(), key=operator.itemgetter(0)):
        graf_vendas_mes += [[key, value]]
    # Se não existirem os dias primeiro e último do mes nos dados inseridos, adicionar
    primeiro_dia = str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000)
    ultimo_dia = datetime.date(ano, mes, 1) + datetime.timedelta(days=calendar.monthrange(ano,mes)[1])
    ultimo_dia = ultimo_dia - datetime.timedelta(days=1)
    ultimo_dia = str(calendar.timegm(datetime.date(ano, mes, ultimo_dia.day).timetuple()) * 1000)
    if not primeiro_dia in operacoes_compra.iteritems():
        graf_compras_mes.insert(0, [primeiro_dia, 0])
    if not primeiro_dia in operacoes_venda.iteritems():
        graf_vendas_mes.insert(0, [primeiro_dia, 0])
    if not [item for item in graf_lucro_mes if primeiro_dia in item]:
        graf_lucro_mes.insert(0, [primeiro_dia, 0])
    if not ultimo_dia in operacoes_compra.iteritems():
        graf_compras_mes += [[ultimo_dia, 0]]
    if not ultimo_dia in operacoes_venda.iteritems():
        graf_vendas_mes += [[ultimo_dia, 0]]
    if not [item for item in graf_lucro_mes if ultimo_dia in item]:
        graf_lucro_mes += [[ultimo_dia, float(dados_mes['lucro_bruto'])]]
    
    # TODO adicionar primeiro e ultimo dia ao lucro do mes
    if request.is_ajax():
        lista_temp = [(ticker, '{0:,}'.format(Decimal(valor).quantize(Decimal('0.01'))).replace(',', '.')[::-1].replace('.', ',', 1)[::-1]) for ticker, valor in acoes_lucro_ordenado]
        acoes_lucro_ordenado = lista_temp
        for chave in dados_mes.keys():
            if isinstance(dados_mes[chave], Decimal):
                # Formata números com separador de mil, trocando , por . e depois inverte a string para trocar o último . por ,
                dados_mes[chave] = '{0:,}'.format(dados_mes[chave].quantize(Decimal('0.01'))).replace(',', '.')[::-1].replace('.', ',', 1)[::-1]
            if isinstance(dados_mes[chave], float):
                # Formata números com separador de mil, trocando , por . e depois inverte a string para trocar o último . por ,
                dados_mes[chave] = '{0:,}'.format(Decimal(dados_mes[chave]).quantize(Decimal('0.01'))).replace(',', '.')[::-1].replace('.', ',', 1)[::-1]
        return HttpResponse(json.dumps({'lista_anos': lista_anos, 'lista_meses': lista_meses, 'dados_mes': dados_mes, 'graf_compras_mes': graf_compras_mes,
                                        'graf_vendas_mes': graf_vendas_mes, 'graf_lucro_mes': graf_lucro_mes, 'acoes_ranking': acoes_lucro_ordenado}), content_type = "application/json")
    else:
        return TemplateResponse(request, 'acoes/trade/acompanhamento_mensal.html', {'lista_anos': lista_anos, 'lista_meses': lista_meses, 'dados_mes': dados_mes, 'graf_compras_mes': graf_compras_mes,
                                                                                    'graf_vendas_mes': graf_vendas_mes, 'graf_lucro_mes': graf_lucro_mes, 'acoes_ranking': acoes_lucro_ordenado})
    
    
@login_required
@adiciona_titulo_descricao('Editar operação de Trading em Ações', 'Altera dados de uma compra e venda de Ações')
def editar_operacao(request, operacao_id):
    investidor = request.user.investidor
    
    operacao = get_object_or_404(OperacaoCompraVenda, pk=operacao_id)
    # Checar se é o investidor da operação
    if investidor != operacao.compra.investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form = OperacaoCompraVendaForm(request.POST, instance=operacao, investidor=investidor)
            if form.is_valid():
                form.save()
                messages.success(request, 'Operação de Compra/Venda editada com sucesso')
                return HttpResponseRedirect(reverse('acoes:trading:historico_operacoes_cv'))
            
            for erro in [erro for erro in form.non_field_errors()]:
                messages.error(request, erro)
        elif request.POST.get("delete"):
            operacao.delete()
            messages.error(request, 'Operação de Compra/Venda excluída com sucesso')
            return HttpResponseRedirect(reverse('acoes:trading:historico_operacoes_cv'))

    else:
        form = OperacaoCompraVendaForm(instance=operacao, investidor=investidor)
        
    return TemplateResponse(request, 'acoes/trade/editar_operacao.html', {'form': form}) 
    
@login_required
@adiciona_titulo_descricao('Editar operação em Ações para Trading', 'Altera valores de uma operação de compra/venda de Ações para Trading')
def editar_operacao_acao(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_acao = get_object_or_404(OperacaoAcao, pk=operacao_id, destinacao='T')
    
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if operacao_acao.investidor != investidor:
        raise PermissionDenied
    
    # Valor da poupança de proventos na data apontada
    poupanca_proventos = calcular_poupanca_prov_acao_ate_dia(investidor, operacao_acao.data)
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoAcao, DivisaoOperacaoAcao, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoAcaoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Busca as operações de compra/venda relativas a essa operação, se alguma envolver daytrade, marcar como daytrade
    # TODO preparar para muitas execuções em uma mesma operação
    operacao_day_trade = False
    if operacao_acao.compra or operacao_acao.venda:
        for operacao_compra_venda in list(chain(operacao_acao.compra.get_queryset(), operacao_acao.venda.get_queryset())):
            if operacao_compra_venda.day_trade:
                operacao_day_trade = True

    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_acao = OperacaoAcaoForm(request.POST, instance=operacao_acao)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_acao, investidor=investidor) if varias_divisoes else None
            
            if not varias_divisoes:
                try:
                    form_uso_proventos = UsoProventosOperacaoAcaoForm(request.POST, instance=UsoProventosOperacaoAcao.objects.get(divisao_operacao__operacao=operacao_acao))
                except UsoProventosOperacaoAcao.DoesNotExist:
                    form_uso_proventos = UsoProventosOperacaoAcaoForm(request.POST)
            else:
                form_uso_proventos = UsoProventosOperacaoAcaoForm()    
                
            if form_operacao_acao.is_valid():
                try:
                    with transaction.atomic():
                        # Validar de acordo com a quantidade de divisões
                        if varias_divisoes:
                            if formset_divisao.is_valid():
                                operacao_acao.save()
                                formset_divisao.save()
                                for form_divisao_operacao in [form for form in formset_divisao if form.cleaned_data]:
                                    # Ignorar caso seja apagado
                                    if 'DELETE' in form_divisao_operacao.cleaned_data and form_divisao_operacao.cleaned_data['DELETE']:
                                        pass
                                    else:
                                        divisao_operacao = form_divisao_operacao.save(commit=False)
                                        if hasattr(divisao_operacao, 'usoproventosoperacaoacao'):
                                            if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] == None or form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] == 0:
                                                divisao_operacao.usoproventosoperacaoacao.delete()
                                            else:
                                                divisao_operacao.usoproventosoperacaoacao.qtd_utilizada = form_divisao_operacao.cleaned_data['qtd_proventos_utilizada']
                                                divisao_operacao.usoproventosoperacaoacao.save()
                                        else:
                                            if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] != None and form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] > 0:
                                                # TODO remover operação de uso proventos
                                                divisao_operacao.usoproventosoperacaoacao = UsoProventosOperacaoAcao(qtd_utilizada=form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'], operacao=operacao_acao)
                                                divisao_operacao.usoproventosoperacaoacao.save()
                                
                                messages.success(request, 'Operação alterada com sucesso')
                                return HttpResponseRedirect(reverse('acoes:trading:historico_operacoes'))
                            for erro in formset_divisao.non_form_errors():
                                messages.error(request, erro)
                                
                        else:
                            if form_uso_proventos.is_valid():
                                operacao_acao.save()
                                divisao_operacao = DivisaoOperacaoAcao.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_acao, quantidade=operacao_acao.quantidade)
                                divisao_operacao.save()
                                uso_proventos = form_uso_proventos.save(commit=False)
        #                         print uso_proventos.qtd_utilizada 
                                if uso_proventos.qtd_utilizada > 0:
                                    uso_proventos.operacao = operacao_acao
                                    uso_proventos.divisao_operacao = DivisaoOperacaoAcao.objects.get(operacao=operacao_acao)
                                    uso_proventos.save()
                                # Se uso proventos for 0 e existir uso proventos atualmente, apagá-lo
                                elif uso_proventos.qtd_utilizada == 0 and UsoProventosOperacaoAcao.objects.filter(divisao_operacao__operacao=operacao_acao):
                                    uso_proventos.delete()
                                messages.success(request, 'Operação alterada com sucesso')
                                return HttpResponseRedirect(reverse('acoes:trading:historico_operacoes'))
                except:
                    pass
            
            for erro in [erro for erro in form_operacao_acao.non_field_errors()]:
                messages.error(request, erro)

        elif request.POST.get("delete"):
            try:
                with transaction.atomic():
                    divisao_acao = DivisaoOperacaoAcao.objects.filter(operacao=operacao_acao)
                    for divisao in divisao_acao:
                        if hasattr(divisao, 'usoproventosoperacaoacao'):
                            divisao.usoproventosoperacaoacao.delete()
                        divisao.delete()
                    operacao_acao.delete()
                    messages.success(request, 'Operação apagada com sucesso')
                    return HttpResponseRedirect(reverse('acoes:bh:historico_bh'))
            except:
                messages.error('Houve um erro na exclusão da operação')

    else:
        form_operacao_acao = OperacaoAcaoForm(instance=operacao_acao)
        if not varias_divisoes:
            if UsoProventosOperacaoAcao.objects.filter(divisao_operacao__operacao=operacao_acao).exists():
                form_uso_proventos = UsoProventosOperacaoAcaoForm(instance=UsoProventosOperacaoAcao.objects.get(divisao_operacao__operacao=operacao_acao))
            else:
                form_uso_proventos = UsoProventosOperacaoAcaoForm()
        else:
            form_uso_proventos = UsoProventosOperacaoAcaoForm()
        formset_divisao = DivisaoFormSet(instance=operacao_acao, investidor=investidor)
            
    return TemplateResponse(request, 'acoes/trade/editar_operacao_acao.html', {'form_operacao_acao': form_operacao_acao, 'form_uso_proventos': form_uso_proventos, 'operacao_day_trade': operacao_day_trade,
                                                                       'formset_divisao': formset_divisao, 'poupanca_proventos': poupanca_proventos, 'varias_divisoes': varias_divisoes})
            
@login_required
@adiciona_titulo_descricao('Histórico de Ações (Trading)', 'Histórico de operações de compra/venda para Trading')
def historico_operacoes(request):
    investidor = request.user.investidor
    
    operacoes = OperacaoAcao.objects.filter(destinacao='T', investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    if not operacoes:
        return TemplateResponse(request, 'acoes/trade/historico_operacoes.html', {'operacoes': operacoes, 'meses_operacao': list(), 'graf_lucro_acumulado': list(),
                               'graf_lucro_mensal': list()})
    
    # Dados para acompanhamento de vendas mensal e tributavel
    ano = operacoes[0].data.year
    mes = operacoes[0].data.month
    qtd_vendas_mensal = Decimal(0)
    lucro_mensal = Decimal(0)
    lucro_geral = Decimal(0)
    
    # Dados para o gráfico
    graf_lucro_acumulado = list()
    graf_lucro_mensal = list()
    
    # Tabela de meses
    meses_operacao = list()
    mes_operacao = {'mes': mes, 'ano': ano}
    
    for operacao in operacoes:
        # Verificar se mes ou ano foram alterados
        if (ano != operacao.data.year or mes != operacao.data.month): 
            
            # Colocar valores
            mes_operacao['lucro_mensal'] = lucro_mensal.quantize(Decimal('0.01'))
            mes_operacao['lucro_geral'] = lucro_geral.quantize(Decimal('0.01'))
            mes_operacao['qtd_vendas_mensal'] = qtd_vendas_mensal
            
            # Adicionar mes a lista de meses
            meses_operacao += [ mes_operacao ]
            
            # Terminar mes adicionando o lucro mensal ao lucro geral
            lucro_geral += lucro_mensal
            
            # Adicionar dados ao gráfico
            graf_lucro_acumulado += [[str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000), float(lucro_geral)]]
            graf_lucro_mensal += [[str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000), float(lucro_mensal)]]
            
            ano = operacao.data.year
            mes = operacao.data.month
            mes_operacao = {'mes': mes, 'ano': ano}
            
            # Reiniciar contadores mensais
            qtd_vendas_mensal = Decimal(0)
            lucro_mensal = Decimal(0)
        
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            operacao.total_gasto = Decimal(-1) * (operacao.quantidade * operacao.preco_unitario + \
            operacao.emolumentos + operacao.corretagem)
        elif operacao.tipo_operacao == 'V':
            operacao.total_gasto = (operacao.quantidade * operacao.preco_unitario - \
            operacao.emolumentos - operacao.corretagem)
        
            qtd_vendas_mensal += operacao.quantidade * operacao.preco_unitario
            
            # Calcular lucro bruto da operação de venda
            # Pegar operações de compra
            # TODO PREPARAR CASO DE MUITAS COMPRAS PARA MUITAS VENDAS
            qtd_compra = Decimal(0)
            gasto_total_compras = Decimal(0)
            for operacao_compra in operacao.venda.get_queryset().order_by('compra__preco_unitario'):
                qtd_compra += operacao_compra.compra.quantidade
                # TODO NAO PREVÊ MUITAS COMPRAS PARA MUITAS VENDAS
                gasto_total_compras += (operacao_compra.compra.quantidade * operacao_compra.compra.preco_unitario + operacao_compra.compra.emolumentos + \
                                        operacao_compra.compra.corretagem) * (Decimal(operacao.quantidade) / operacao_compra.compra.quantidade)
                
            lucro_bruto_venda = (operacao.quantidade * operacao.preco_unitario - operacao.corretagem - operacao.emolumentos) - \
                gasto_total_compras
            
            lucro_mensal += lucro_bruto_venda
        
        # Verificar se é a ultima iteração
        if (operacao == operacoes[len(operacoes)-1]):
            # Colocar valores
            mes_operacao['lucro_mensal'] = lucro_mensal.quantize(Decimal('0.01'))
            mes_operacao['lucro_geral'] = lucro_geral.quantize(Decimal('0.01'))
            mes_operacao['qtd_vendas_mensal'] = qtd_vendas_mensal
            
            # Adicionar mes a lista de meses
            meses_operacao += [ mes_operacao ]
            
            lucro_geral += lucro_mensal 
            
            # Adicionar dados ao gráfico
            graf_lucro_acumulado += [[str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000), float(lucro_geral)]]
            graf_lucro_mensal += [[str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000), float(lucro_mensal)]]
            
                
    return TemplateResponse(request, 'acoes/trade/historico_operacoes.html', {'operacoes': operacoes, 'meses_operacao': meses_operacao, 'graf_lucro_acumulado': graf_lucro_acumulado,
                               'graf_lucro_mensal': graf_lucro_mensal})
    
@login_required
@adiciona_titulo_descricao('Histórico de operações de Trading', 'Histórico de operações de compra e venda')
def historico_operacoes_cv(request):
    investidor = request.user.investidor
    operacoes = OperacaoCompraVenda.objects.filter(compra__investidor=investidor).order_by('id')
    
    # TODO adicionar calculos de lucro com DayTrade
    for operacao in operacoes:
        operacao.total_compra = (Decimal(operacao.quantidade) / operacao.compra.quantidade) * (operacao.compra.preco_unitario * operacao.compra.quantidade + \
                                                                                      operacao.compra.corretagem + operacao.compra.emolumentos)
        operacao.lucro = (Decimal(operacao.quantidade) / operacao.venda.quantidade) * (operacao.venda.preco_unitario * operacao.venda.quantidade - \
                                                                               operacao.venda.corretagem - operacao.venda.emolumentos )
        operacao.lucro -= operacao.total_compra
        # Arredondar
        operacao.lucro = operacao.lucro.quantize(Decimal('0.01'))
        
        operacao.lucro_percentual = operacao.lucro / operacao.total_compra * 100
            
    return TemplateResponse(request, 'acoes/trade/historico_operacoes_cv.html', {'operacoes': operacoes})
    
@login_required
@adiciona_titulo_descricao('Inserir operação de Trading em Ações', 'Insere um registro de operação de Trading em Ações (compra e venda)')
def inserir_operacao(request):
    investidor = request.user.investidor
    if request.method == 'POST':
        form = OperacaoCompraVendaForm(request.POST, investidor=investidor)
        if form.is_valid():
            operacao_trade = form.save(commit=False)
            operacao_trade.investidor = investidor
            operacao_trade.save()
            messages.success(request, 'Operação inserida com sucesso')
            return HttpResponseRedirect(reverse('acoes:trading:historico_operacoes_cv'))
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = OperacaoCompraVendaForm(investidor=investidor)
            
    return TemplateResponse(request, 'acoes/trade/inserir_operacao.html', {'form': form})
    
@login_required
@adiciona_titulo_descricao('Inserir operação em Ações para Trading', 'Insere um registro de operação de compra/venda em Ações para Trading')
def inserir_operacao_acao(request):
    investidor = request.user.investidor
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoAcao, DivisaoOperacaoAcao, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoAcaoFormSet)
    
    if request.method == 'POST':
        form_operacao_acao = OperacaoAcaoForm(request.POST)
        form_uso_proventos = UsoProventosOperacaoAcaoForm(request.POST) if not varias_divisoes else None
        formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        if form_operacao_acao.is_valid():
            operacao_acao = form_operacao_acao.save(commit=False)
            operacao_acao.investidor = investidor
            operacao_acao.destinacao = 'T'
            try:
                with transaction.atomic():
                    # Validar de acordo com a quantidade de divisões
                    if varias_divisoes:
                        formset_divisao = DivisaoFormSet(request.POST, instance=operacao_acao, investidor=investidor)
                        if formset_divisao.is_valid():
                            operacao_acao.save()
                            formset_divisao.save()
                            for form_divisao_operacao in [form for form in formset_divisao if form.cleaned_data]:
                                divisao_operacao = form_divisao_operacao.save(commit=False)
                                if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] != None and form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] > 0:
                                    # TODO remover operação de uso proventos
                                    divisao_operacao.usoproventosoperacaoacao = UsoProventosOperacaoAcao(qtd_utilizada=form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'], operacao=operacao_acao)
                                    divisao_operacao.usoproventosoperacaoacao.save()
                                
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('acoes:trading:historico_operacoes'))
                        for erro in formset_divisao.non_form_errors():
                            messages.error(request, erro)
                        
                    else:
                        if form_uso_proventos.is_valid():
                            operacao_acao.save()
                            divisao_operacao = DivisaoOperacaoAcao(operacao=operacao_acao, quantidade=operacao_acao.quantidade, divisao=investidor.divisaoprincipal.divisao)
                            divisao_operacao.save()
                            uso_proventos = form_uso_proventos.save(commit=False)
                            if uso_proventos.qtd_utilizada > 0:
                                uso_proventos.operacao = operacao_acao
                                uso_proventos.divisao_operacao = divisao_operacao
                                uso_proventos.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('acoes:trading:historico_operacoes'))
            except:
                pass
            
        for erro in [erro for erro in form_operacao_acao.non_field_errors()]:
            messages.error(request, erro)
    else:
        valores_iniciais = {}
        if investidor.tipo_corretagem == 'F':
            valores_iniciais['corretagem'] = investidor.corretagem_padrao
        form_operacao_acao = OperacaoAcaoForm(initial=valores_iniciais)
        form_uso_proventos = UsoProventosOperacaoAcaoForm(initial={'qtd_utilizada': Decimal('0.00')})
        formset_divisao = DivisaoFormSet(investidor=investidor)
            
    return TemplateResponse(request, 'acoes/trade/inserir_operacao_acao.html', {'form_operacao_acao': form_operacao_acao, 'form_uso_proventos': form_uso_proventos,
                                                                       'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})
