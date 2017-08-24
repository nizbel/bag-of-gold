# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoCriptomoedaFormSet, \
    DivisaoTransferenciaCriptomoedaFormSet
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    Divisao, DivisaoTransferenciaCriptomoeda
from bagogold.criptomoeda.forms import OperacaoCriptomoedaForm, \
    TransferenciaCriptomoedaForm
from bagogold.criptomoeda.models import Criptomoeda, OperacaoCriptomoeda, \
    OperacaoCriptomoedaMoeda, OperacaoCriptomoedaTaxa, TransferenciaCriptomoeda
from bagogold.fundo_investimento.utils import \
    calcular_qtd_cotas_ate_dia_por_fundo
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from urllib2 import urlopen
from itertools import chain
from operator import attrgetter
import datetime
import json
import traceback

@login_required
@adiciona_titulo_descricao('Editar operação em criptomoeda', 'Alterar valores de uma operação de compra/venda em criptomoeda')
def editar_operacao_criptomoeda(request, id_operacao):
    investidor = request.user.investidor
    
    operacao_criptomoeda = OperacaoCriptomoeda.objects.get(pk=id_operacao)
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if operacao_criptomoeda.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoCriptomoeda, DivisaoOperacaoCriptomoeda, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoCriptomoedaFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_criptomoeda = OperacaoCriptomoedaForm(request.POST, instance=operacao_criptomoeda, investidor=investidor)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_criptomoeda, investidor=investidor) if varias_divisoes else None
                
            if form_operacao_criptomoeda.is_valid():
                moeda_utilizada = Criptomoeda.objects.get(id=int(form_operacao_criptomoeda.cleaned_data['moeda_utilizada'])) \
                    if form_operacao_criptomoeda.cleaned_data['moeda_utilizada'] != '' else None
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        try:
                            with transaction.atomic():
                                operacao_criptomoeda.save()
                                # Caso o valor para a taxa da moeda comprada/vendida seja maior que 0, criar ou editar taxa
                                if form_operacao_criptomoeda.cleaned_data['taxa'] > 0:
                                    taxa_moeda = Criptomoeda.objects.get(id=int(form_operacao_criptomoeda.cleaned_data['taxa_moeda'])) \
                                        if form_operacao_criptomoeda.cleaned_data['taxa_moeda'] != '' else None
                                    OperacaoCriptomoedaTaxa.objects.update_or_create(operacao=operacao_criptomoeda, defaults={'moeda': taxa_moeda,
                                                                                                                              'valor': form_operacao_criptomoeda.cleaned_data['taxa']})
                                # Caso contrário, apagar taxa para a moeda, caso exista
                                elif OperacaoCriptomoedaTaxa.objects.filter(operacao=operacao_criptomoeda).exists():
                                    OperacaoCriptomoedaTaxa.objects.get(operacao=operacao_criptomoeda).delete()
                                
                                # Caso a moeda utilizada não seja o real, criar ou editar registro de moeda utilizada
                                if moeda_utilizada:
                                    OperacaoCriptomoedaMoeda.objects.update_or_create(operacao=operacao_criptomoeda, defaults={'criptomoeda': moeda_utilizada})
                                # Caso moeda utilizada seja o real, verificar se existe registro de moeda utilizada para apagar
                                elif OperacaoCriptomoedaMoeda.objects.filter(operacao=operacao_criptomoeda).exists():
                                    OperacaoCriptomoedaMoeda.objects.get(operacao=operacao_criptomoeda).delete()
                                    
                                divisao_operacao = DivisaoOperacaoCriptomoeda(operacao=operacao_criptomoeda, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_criptomoeda.quantidade)
                                formset_divisao.save()
                                messages.success(request, 'Operação editada com sucesso')
                                return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                        except:
                            messages.error(request, 'Houve um erro ao editar a operação')
                            if settings.ENV == 'DEV':
                                raise
                            elif settings.ENV == 'PROD':
                                mail_admins(u'Erro ao editar operação em criptomoeda com várias divisões', traceback.format_exc())
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                        
                else:
                    try:
                        with transaction.atomic():
                            operacao_criptomoeda.save()
                            # Caso o valor para a taxa da moeda comprada/vendida seja maior que 0, criar ou editar taxa
                            if form_operacao_criptomoeda.cleaned_data['taxa'] > 0:
                                taxa_moeda = Criptomoeda.objects.get(id=int(form_operacao_criptomoeda.cleaned_data['taxa_moeda'])) \
                                    if form_operacao_criptomoeda.cleaned_data['taxa_moeda'] != '' else None
                                OperacaoCriptomoedaTaxa.objects.update_or_create(operacao=operacao_criptomoeda, defaults={'moeda': taxa_moeda,
                                                                                                                          'valor': form_operacao_criptomoeda.cleaned_data['taxa']})
                            # Caso contrário, apagar taxa para a moeda, caso exista
                            elif OperacaoCriptomoedaTaxa.objects.filter(operacao=operacao_criptomoeda).exists():
                                OperacaoCriptomoedaTaxa.objects.get(operacao=operacao_criptomoeda).delete()
                                
                            # Caso a moeda utilizada não seja o real, criar ou editar registro de moeda utilizada
                            if moeda_utilizada:
                                OperacaoCriptomoedaMoeda.objects.update_or_create(operacao=operacao_criptomoeda, defaults={'criptomoeda': moeda_utilizada})
                            # Caso moeda utilizada seja o real, verificar se existe registro de moeda utilizada para apagar
                            elif OperacaoCriptomoedaMoeda.objects.filter(operacao=operacao_criptomoeda).exists():
                                OperacaoCriptomoedaMoeda.objects.get(operacao=operacao_criptomoeda).delete()
                                
                            divisao_operacao = DivisaoOperacaoCriptomoeda.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_criptomoeda)
                            divisao_operacao.quantidade = operacao_criptomoeda.quantidade
                            divisao_operacao.save()
                            messages.success(request, 'Operação editada com sucesso')
                            return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                    except:
                        messages.error(request, 'Houve um erro ao editar a operação')
                        if settings.ENV == 'DEV':
                            raise
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro ao editar operação em criptomoeda com uma divisão', traceback.format_exc())
                
            for erro in [erro for erro in form_operacao_criptomoeda.non_field_errors()]:
                messages.error(request, erro)
#                         print '%s %s'  % (divisao_criptomoeda.quantidade, divisao_criptomoeda.divisao)
                
        elif request.POST.get("delete"):
            # Verifica se, em caso de compra, a quantidade de cotas do investidor não fica negativa
            if operacao_criptomoeda.tipo_operacao == 'C' and calcular_qtd_cotas_ate_dia_por_fundo(investidor, operacao_criptomoeda.criptomoeda.id, datetime.date.today()) - operacao_criptomoeda.quantidade < 0:
                messages.error(request, 'Operação de compra não pode ser apagada pois quantidade atual para o fundo %s seria negativa' % (operacao_criptomoeda.criptomoeda))
            else:
                divisao_criptomoeda = DivisaoOperacaoCriptomoeda.objects.filter(operacao=operacao_criptomoeda)
                for divisao in divisao_criptomoeda:
                    divisao.delete()
                operacao_criptomoeda.delete()
                messages.success(request, 'Operação apagada com sucesso')
                return HttpResponseRedirect(reverse('td:historico_td'))
 
    else:
        if OperacaoCriptomoedaTaxa.objects.filter(operacao=operacao_criptomoeda).exists():
            taxa = OperacaoCriptomoedaTaxa.objects.get(operacao=operacao_criptomoeda)
            taxa_valor = taxa.valor
            taxa_moeda = taxa.moeda
        else:
            taxa_valor = 0
            taxa_moeda = None
        form_operacao_criptomoeda = OperacaoCriptomoedaForm(instance=operacao_criptomoeda, investidor=investidor, initial={'taxa': taxa_valor, 'taxa_moeda': taxa_moeda})
        formset_divisao = DivisaoFormSet(instance=operacao_criptomoeda, investidor=investidor)
        
    # Preparar nome de fundo selecionado
#     if request.POST.get('criptomoeda', -1) != -1:
#         fundo_selecionado = Criptomoeda.objects.get(id=request.POST['criptomoeda'])
#     else:
#         fundo_selecionado = operacao_criptomoeda.criptomoeda.nome
    return TemplateResponse(request, 'criptomoedas/editar_operacao_criptomoeda.html', {'form_operacao_criptomoeda': form_operacao_criptomoeda, 'formset_divisao': formset_divisao, \
                                                                                             'varias_divisoes': varias_divisoes})  

@login_required
@adiciona_titulo_descricao('Editar transferência para criptomoedas', 'Alterar valores de uma transferência para criptomoedas')
def editar_transferencia(request, id_transferencia):
    investidor = request.user.investidor
    

@adiciona_titulo_descricao('Histórico de Criptomoedas', 'Histórico de operações de compra/venda em Criptomoedas')
def historico(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
    
    # Transferências do investidor
    transferencias = TransferenciaCriptomoeda.objects.filter(investidor=investidor).order_by('data')
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCriptomoeda.objects.filter(investidor=investidor).order_by('data', '-tipo_operacao') 
    
    # Juntar transferências e operações em uma lista
    lista_movimentacoes = sorted(chain(transferencias, operacoes), key=attrgetter('data'))
    # Se investidor não tiver operações, retornar vazio
    if not operacoes:
        return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
    
    # Gráficos
    graf_patrimonio = list()
    graf_investido_total = list()
    
    moedas = {}
    total_investido = 0
    
    for movimentacao in lista_movimentacoes:
        if isinstance(movimentacao, OperacaoCriptomoeda):
            if movimentacao.criptomoeda.ticker not in moedas.keys():
                moedas[movimentacao.criptomoeda.ticker] = 0
                
            if movimentacao.tipo_operacao == 'C':
                movimentacao.tipo = 'Compra'
                moedas[movimentacao.criptomoeda.ticker] += movimentacao.quantidade
            else:
                movimentacao.tipo = 'Venda'
                moedas[movimentacao.criptomoeda.ticker] -= movimentacao.quantidade
            movimentacao.taxa = movimentacao.operacaocriptomoedataxa if hasattr(movimentacao, 'operacaocriptomoedataxa') else None
            if movimentacao.taxa:
                if movimentacao.taxa.moeda == movimentacao.criptomoeda:
                    movimentacao.valor_total = (movimentacao.quantidade + movimentacao.taxa.valor) * movimentacao.valor
                elif movimentacao.taxa.moeda_utilizada() == movimentacao.moeda_utilizada():
                    movimentacao.valor_total = movimentacao.quantidade * movimentacao.valor + movimentacao.taxa.valor
                else:
                    raise ValueError('Moeda utilizada na taxa é inválida')
            else:
                movimentacao.valor_total = movimentacao.quantidade * movimentacao.valor
        
        elif isinstance(movimentacao, TransferenciaCriptomoeda):
            if movimentacao.moeda and movimentacao.moeda.ticker not in moedas.keys():
                moedas[movimentacao.moeda.ticker] = 0
                
            movimentacao.tipo = u'Transferência'
            if movimentacao.moeda:
                moedas[movimentacao.moeda.ticker] -= movimentacao.taxa
            movimentacao.valor_total = movimentacao.quantidade
            movimentacao.valor = movimentacao.quantidade - movimentacao.taxa
            # Usar quantidade para guardar valor da taxa
            movimentacao.quantidade = movimentacao.taxa
            
            # Preparar taxa
            movimentacao.taxa = Object()
            movimentacao.taxa.moeda = movimentacao.moeda
            movimentacao.taxa.valor = movimentacao.quantidade
            
            movimentacao.criptomoeda = movimentacao.moeda
            
        # Limitar valores totais em reais para 2 casas decimais
        if movimentacao.em_real():
            movimentacao.valor_total = movimentacao.valor_total.quantize(Decimal('0.01'))
    
    dados = {}
    dados['total_investido'] = total_investido
    # Carrega o valor de um dólar em reais, mais atual
    url_dolar = 'http://api.fixer.io/latest?base=USD&symbols=BRL'
    resultado = urlopen(url_dolar)
    data = json.load(resultado) 
    dolar_para_real = Decimal(data['rates']['BRL'])
    
    dados['patrimonio'] = 0
    for ticker, qtd in moedas.items():
        if qtd == 0:
            continue
        url = 'https://api.cryptonator.com/api/ticker/%s-usd' % (ticker)
        resultado = urlopen(url)
        data = json.load(resultado) 
        dados['patrimonio'] += qtd * dolar_para_real * Decimal(data['ticker']['price'])
#     dados['lucro'] = total_patrimonio - total_investido
#     dados['lucro_percentual'] = (total_patrimonio - total_investido) / total_investido * 100
    
    return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': dados, 'movimentacoes': lista_movimentacoes, 
                                                    'graf_investido_total': graf_investido_total, 'graf_patrimonio': graf_patrimonio})

@login_required
@adiciona_titulo_descricao('Inserir operação em criptomoedas', 'Inserir registro de operação de compra/venda em criptomoeda')
def inserir_operacao_criptomoeda(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoCriptomoedaFormSet = inlineformset_factory(OperacaoCriptomoeda, DivisaoOperacaoCriptomoeda, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoCriptomoedaFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_operacao_criptomoeda = OperacaoCriptomoedaForm(request.POST, investidor=investidor)
        formset_divisao = DivisaoCriptomoedaFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar Fundo de Investimento
        if form_operacao_criptomoeda.is_valid():
            operacao_criptomoeda = form_operacao_criptomoeda.save(commit=False)
            operacao_criptomoeda.investidor = investidor
            moeda_utilizada = Criptomoeda.objects.get(id=int(form_operacao_criptomoeda.cleaned_data['moeda_utilizada'])) \
                if form_operacao_criptomoeda.cleaned_data['moeda_utilizada'] != '' else None
                
            # Testar se várias divisões
            if varias_divisoes:
                formset_divisao = DivisaoCriptomoedaFormSet(request.POST, instance=operacao_criptomoeda, investidor=investidor)
                if formset_divisao.is_valid():
                    try:
                        with transaction.atomic():
                            operacao_criptomoeda.save()
                            if form_operacao_criptomoeda.cleaned_data['taxa'] > 0:
                                taxa_moeda = Criptomoeda.objects.get(id=int(form_operacao_criptomoeda.cleaned_data['taxa_moeda'])) \
                                    if form_operacao_criptomoeda.cleaned_data['taxa_moeda'] != '' else None
                                OperacaoCriptomoedaTaxa.objects.create(operacao=operacao_criptomoeda, moeda=taxa_moeda, valor=form_operacao_criptomoeda.cleaned_data['taxa'])
                            if moeda_utilizada:
                                OperacaoCriptomoedaMoeda.objects.create(operacao=operacao_criptomoeda, criptomoeda=moeda_utilizada)
                            formset_divisao.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                    except:
                        messages.error(request, 'Houve um erro ao inserir a operação')
                        if settings.ENV == 'DEV':
                            raise
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro ao gerar operação em criptomoeda com várias divisões', traceback.format_exc())
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
            else:
                try:
                    with transaction.atomic():
                        operacao_criptomoeda.save()
                        if form_operacao_criptomoeda.cleaned_data['taxa'] > 0:
                                taxa_moeda = Criptomoeda.objects.get(id=int(form_operacao_criptomoeda.cleaned_data['taxa_moeda'])) \
                                    if form_operacao_criptomoeda.cleaned_data['taxa_moeda'] != '' else None
                                OperacaoCriptomoedaTaxa.objects.create(operacao=operacao_criptomoeda, moeda=taxa_moeda, valor=form_operacao_criptomoeda.cleaned_data['taxa'])
                        if moeda_utilizada:
                            OperacaoCriptomoedaMoeda.objects.create(operacao=operacao_criptomoeda, criptomoeda=moeda_utilizada)
                        divisao_operacao = DivisaoOperacaoCriptomoeda(operacao=operacao_criptomoeda, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_criptomoeda.quantidade)
                        divisao_operacao.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                except:
                    messages.error(request, 'Houve um erro ao inserir a operação')
                    if settings.ENV == 'DEV':
                        raise
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro ao gerar operação em criptomoeda com uma divisão', traceback.format_exc())
            
        for erro in [erro for erro in form_operacao_criptomoeda.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_operacao_criptomoeda = OperacaoCriptomoedaForm(investidor=investidor)
        formset_divisao = DivisaoCriptomoedaFormSet(investidor=investidor)
    
    return TemplateResponse(request, 'criptomoedas/inserir_operacao_criptomoeda.html', {'form_operacao_criptomoeda': form_operacao_criptomoeda, \
                                                                                              'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@login_required
@adiciona_titulo_descricao('Inserir transferência para criptomoedas', 'Inserir registro de transferência para criptomoedas')
def inserir_transferencia(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoCriptomoedaFormSet = inlineformset_factory(TransferenciaCriptomoeda, DivisaoTransferenciaCriptomoeda, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoTransferenciaCriptomoedaFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_transferencia_criptomoeda = TransferenciaCriptomoedaForm(request.POST, investidor=investidor)
        formset_divisao = DivisaoCriptomoedaFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar Fundo de Investimento
        if form_transferencia_criptomoeda.is_valid():
            transferencia_criptomoeda = form_transferencia_criptomoeda.save(commit=False)
            transferencia_criptomoeda.investidor = investidor
                
            # Testar se várias divisões
            if varias_divisoes:
                formset_divisao = DivisaoCriptomoedaFormSet(request.POST, instance=transferencia_criptomoeda, investidor=investidor)
                if formset_divisao.is_valid():
                    try:
                        with transaction.atomic():
                            transferencia_criptomoeda.save()
                            formset_divisao.save()
                            messages.success(request, 'Transferência inserida com sucesso')
                            return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                    except:
                        messages.error(request, 'Houve um erro ao inserir a transferência')
                        if settings.ENV == 'DEV':
                            raise
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro ao gerar transferência para criptomoedas com várias divisões', traceback.format_exc())
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
            else:
                try:
                    with transaction.atomic():
                        transferencia_criptomoeda.save()
                        divisao_operacao = DivisaoOperacaoCriptomoeda(transferencia=transferencia_criptomoeda, divisao=investidor.divisaoprincipal.divisao, quantidade=transferencia_criptomoeda.quantidade)
                        divisao_operacao.save()
                        messages.success(request, 'Transferência inserida com sucesso')
                        return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                except:
                    messages.error(request, 'Houve um erro ao inserir a transferência')
                    if settings.ENV == 'DEV':
                        raise
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro ao gerar transferência para criptomoedas com uma divisão', traceback.format_exc())
            
        for erro in [erro for erro in form_transferencia_criptomoeda.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_transferencia_criptomoeda = TransferenciaCriptomoedaForm(investidor=investidor)
        formset_divisao = DivisaoCriptomoedaFormSet(investidor=investidor)
    
    return TemplateResponse(request, 'criptomoedas/inserir_transferencia.html', {'form_transferencia_criptomoeda': form_transferencia_criptomoeda, \
                                                                                              'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@adiciona_titulo_descricao('Listar criptomoedas cadastrados', 'Lista as criptomoedas no sistema')
def listar_criptomoedas(request):
    moedas = Criptomoeda.objects.all()
    
    # Carrega o valor de um dólar em reais, mais atual
    url_dolar = 'http://api.fixer.io/latest?base=USD&symbols=BRL'
    resultado = urlopen(url_dolar)
    data = json.load(resultado) 
    dolar_para_real = Decimal(data['rates']['BRL'])
    
    for moeda in moedas:
        url = 'https://api.cryptonator.com/api/ticker/%s-usd' % (moeda.ticker)
        resultado = urlopen(url)
        data = json.load(resultado) 
        if data['success']:
            moeda.valor_atual_dolar = Decimal(data['ticker']['price'])
            moeda.valor_atual = dolar_para_real * moeda.valor_atual_dolar
            if moeda.ticker == 'BTC':
                btc_para_dolar = moeda.valor_atual_dolar
    
    # Buscar valores POLONIEX
    url = 'https://poloniex.com/public?command=returnTicker'
    resultado = urlopen(url)
    data_polo = json.load(resultado) 
    
    for moeda in moedas:
        if moeda.ticker != 'BTC':
            if 'BTC_%s' % (moeda.ticker) in data_polo.keys():
                moeda.valor_atual_polo = Decimal(data_polo['BTC_%s' % (moeda.ticker)]['last'])
                moeda.valor_atual_polo_dolar = moeda.valor_atual_polo * btc_para_dolar
        
    
    return TemplateResponse(request, 'criptomoedas/listar_moedas.html', {'moedas': moedas})


@login_required
@adiciona_titulo_descricao('Listar criptomoedas cadastrados', 'Lista as criptomoedas no sistema')
def listar_transferencias(request):
    investidor = request.user.investidor
    transferencias = TransferenciaCriptomoeda.objects.filter(investidor=investidor)
    
    return TemplateResponse(request, 'criptomoedas/listar_transferencias.html', {'transferencias': transferencias})

def painel(request):
    pass

def sobre(request):
    pass