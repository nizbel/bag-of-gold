# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoCriptomoedaFormSet
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    Divisao
from bagogold.criptomoeda.forms import OperacaoCriptomoedaForm
from bagogold.criptomoeda.models import Criptomoeda, OperacaoCriptomoeda, \
    OperacaoCriptomoedaMoeda, OperacaoCriptomoedaTaxa
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
import datetime
import json
import traceback

@login_required
@adiciona_titulo_descricao('Editar operação em Criptomoeda', 'Alterar valores de uma operação de compra/venda em Criptomoeda')
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
                                if form_operacao_criptomoeda.cleaned_data['taxa_moeda'] > 0:
                                    OperacaoCriptomoedaTaxa.objects.update_or_create(operacao=operacao_criptomoeda, moeda=operacao_criptomoeda.criptomoeda, 
                                                                                     defaults={'valor': form_operacao_criptomoeda.cleaned_data['taxa_moeda']})
                                # Caso contrário, apagar taxa para a moeda, caso exista
                                elif OperacaoCriptomoedaTaxa.objects.filter(operacao=operacao_criptomoeda, moeda=operacao_criptomoeda.criptomoeda).exists():
                                    OperacaoCriptomoedaTaxa.objects.get(operacao=operacao_criptomoeda, moeda=operacao_criptomoeda.criptomoeda).delete()
                                # Caso o valor para a taxa da moeda utilizada para operação seja maior que 0, criar ou editar taxa
                                if form_operacao_criptomoeda.cleaned_data['taxa_moeda_utilizada'] > 0:
                                    OperacaoCriptomoedaTaxa.objects.update_or_create(operacao=operacao_criptomoeda, moeda=moeda_utilizada, 
                                                                                     defaults={'valor': form_operacao_criptomoeda.cleaned_data['taxa_moeda_utilizada']})
                                # Caso contrário, apagar taxa para a moeda, caso exista
                                elif OperacaoCriptomoedaTaxa.objects.filter(operacao=operacao_criptomoeda, moeda=moeda_utilizada).exists():
                                    OperacaoCriptomoedaTaxa.objects.get(operacao=operacao_criptomoeda, moeda=moeda_utilizada).delete()
                                
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
                            if form_operacao_criptomoeda.cleaned_data['taxa_moeda'] > 0:
                                OperacaoCriptomoedaTaxa.objects.update_or_create(operacao=operacao_criptomoeda, moeda=operacao_criptomoeda.criptomoeda, 
                                                                                 defaults={'valor': form_operacao_criptomoeda.cleaned_data['taxa_moeda']})
                            # Caso contrário, apagar taxa para a moeda, caso exista
                            elif OperacaoCriptomoedaTaxa.objects.filter(operacao=operacao_criptomoeda, moeda=operacao_criptomoeda.criptomoeda).exists():
                                OperacaoCriptomoedaTaxa.objects.get(operacao=operacao_criptomoeda, moeda=operacao_criptomoeda.criptomoeda).delete()
                            # Caso o valor para a taxa da moeda utilizada para operação seja maior que 0, criar ou editar taxa
                            if form_operacao_criptomoeda.cleaned_data['taxa_moeda_utilizada'] > 0:
                                OperacaoCriptomoedaTaxa.objects.update_or_create(operacao=operacao_criptomoeda, moeda=moeda_utilizada, 
                                                                                 defaults={'valor': form_operacao_criptomoeda.cleaned_data['taxa_moeda_utilizada']})
                            # Caso contrário, apagar taxa para a moeda, caso exista
                            elif OperacaoCriptomoedaTaxa.objects.filter(operacao=operacao_criptomoeda, moeda=moeda_utilizada).exists():
                                OperacaoCriptomoedaTaxa.objects.get(operacao=operacao_criptomoeda, moeda=moeda_utilizada).delete()
                            
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
        operacao_criptomoeda.taxas = operacao_criptomoeda.operacaocriptomoedataxa_set.all()
        taxa_moeda = sum([taxa.valor for taxa in operacao_criptomoeda.taxas if taxa.moeda == operacao_criptomoeda.criptomoeda])
        taxa_moeda_utilizada = sum([taxa.valor for taxa in operacao_criptomoeda.taxas if taxa.moeda_utilizada() == operacao_criptomoeda.moeda_utilizada()])
        form_operacao_criptomoeda = OperacaoCriptomoedaForm(instance=operacao_criptomoeda, investidor=investidor, initial={'taxa_moeda': taxa_moeda, 'taxa_moeda_utilizada': taxa_moeda_utilizada})
        formset_divisao = DivisaoFormSet(instance=operacao_criptomoeda, investidor=investidor)
        
    # Preparar nome de fundo selecionado
#     if request.POST.get('criptomoeda', -1) != -1:
#         fundo_selecionado = Criptomoeda.objects.get(id=request.POST['criptomoeda'])
#     else:
#         fundo_selecionado = operacao_criptomoeda.criptomoeda.nome
    return TemplateResponse(request, 'criptomoedas/editar_operacao_criptomoeda.html', {'form_operacao_criptomoeda': form_operacao_criptomoeda, 'formset_divisao': formset_divisao, \
                                                                                             'varias_divisoes': varias_divisoes})  

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
        operacao.taxas = operacao.operacaocriptomoedataxa_set.all()
        operacao.valor_total = (operacao.quantidade + sum([taxa.valor for taxa in operacao.taxas if taxa.moeda == operacao.criptomoeda])) * operacao.valor \
            + sum([taxa.valor for taxa in operacao.taxas if taxa.moeda_utilizada() == operacao.moeda_utilizada()])
        # Limitar valores totais em reais para 2 casas decimais
        if operacao.em_real():
            operacao.valor_total = operacao.valor_total.quantize(Decimal('0.01'))
    
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
                            if form_operacao_criptomoeda.cleaned_data['taxa_moeda'] > 0:
                                OperacaoCriptomoedaTaxa.objects.create(operacao=operacao_criptomoeda, moeda=operacao_criptomoeda.criptomoeda, valor=form_operacao_criptomoeda.cleaned_data['taxa_moeda'])
                            if form_operacao_criptomoeda.cleaned_data['taxa_moeda_utilizada'] > 0:
                                OperacaoCriptomoedaTaxa.objects.create(operacao=operacao_criptomoeda, moeda=moeda_utilizada, valor=form_operacao_criptomoeda.cleaned_data['taxa_moeda_utilizada'])
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
                        if form_operacao_criptomoeda.cleaned_data['taxa_moeda'] > 0:
                            OperacaoCriptomoedaTaxa.objects.create(operacao=operacao_criptomoeda, moeda=operacao_criptomoeda.criptomoeda, valor=form_operacao_criptomoeda.cleaned_data['taxa_moeda'])
                        if form_operacao_criptomoeda.cleaned_data['taxa_moeda_utilizada'] > 0:
                            OperacaoCriptomoedaTaxa.objects.create(operacao=operacao_criptomoeda, moeda=moeda_utilizada, valor=form_operacao_criptomoeda.cleaned_data['taxa_moeda_utilizada'])
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