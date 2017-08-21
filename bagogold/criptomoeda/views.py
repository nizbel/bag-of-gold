# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoCriptomoedaFormSet
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    Divisao
from bagogold.criptomoeda.forms import OperacaoCriptomoedaForm
from bagogold.criptomoeda.models import Criptomoeda, OperacaoCriptomoeda, \
    OperacaoCriptomoedaMoeda
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from urllib2 import urlopen
import json
import traceback

@login_required
def editar_operacao_criptomoeda(request):
    pass

@adiciona_titulo_descricao('Histórico de Criptomoedas', 'Histórico de operações de compra/venda em Criptomoedas')
def historico(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCriptomoeda.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data') 
    # Se investidor não tiver operações, retornar vazio
    if not operacoes:
        return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
    
    # Gráficos
    graf_patrimonio = list()
    graf_investido_total = list()
    
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
        else:
            operacao.tipo = 'Venda'
        operacao.valor_total = operacao.quantidade * operacao.valor + operacao.taxa
        operacao.moeda = 'R$' if operacao.em_real() else operacao.moeda().ticker
    
    dados = {}
#     dados['total_investido'] = total_investido
#     dados['patrimonio'] = total_patrimonio
#     dados['lucro'] = total_patrimonio - total_investido
#     dados['lucro_percentual'] = (total_patrimonio - total_investido) / total_investido * 100
    
    return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': dados, 'operacoes': operacoes, 
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
        moeda.valor_atual = dolar_para_real * Decimal(data['ticker']['price'])
    
    return TemplateResponse(request, 'criptomoedas/listar_moedas.html', {'moedas': moedas})

def painel(request):
    pass

def sobre(request):
    pass