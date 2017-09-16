# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoInvestimentoFormSet
from bagogold.bagogold.models.divisoes import DivisaoInvestimento, Divisao
from bagogold.outros_investimentos.forms import InvestimentoForm
from bagogold.outros_investimentos.models import Investimento, InvestimentoTaxa
from bagogold.outros_investimentos.utils import \
    calcular_valor_outros_investimentos_ate_data
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
import traceback

def detalhar_investimento(request, id_investimento):
    
    pass

def editar_investimento(request):
    pass

def historico(request):
    pass

@login_required
@adiciona_titulo_descricao('Inserir investimento', 'Inserir registro de investimento')
def inserir_investimento(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoOutrosInvestimentosFormSet = inlineformset_factory(Investimento, DivisaoInvestimento, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoInvestimentoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_outros_invest = InvestimentoForm(request.POST, investidor=investidor)
        formset_divisao = DivisaoOutrosInvestimentosFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar operação
        if form_outros_invest.is_valid():
            investimento = form_outros_invest.save(commit=False)
            investimento.investidor = investidor
                
            # Testar se várias divisões
            if varias_divisoes:
                formset_divisao = DivisaoInvestimentoFormSet(request.POST, instance=investimento, investidor=investidor)
                if formset_divisao.is_valid():
                    try:
                        with transaction.atomic():
                            investimento.save()
                            if form_outros_invest.cleaned_data['taxa'] > 0:
                                InvestimentoTaxa.objects.create(investimento=investimento, valor=form_outros_invest.cleaned_data['taxa'])
                            formset_divisao.save()
                            messages.success(request, 'Investimento inserido com sucesso')
                            return HttpResponseRedirect(reverse('outros_investimentos:historico_outros_invest'))
                    except:
                        messages.error(request, 'Houve um erro ao inserir o investimento')
                        if settings.ENV == 'DEV':
                            raise
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro ao gerar investimento na seção outros investimentos, com várias divisões', traceback.format_exc())
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
            else:
                try:
                    with transaction.atomic():
                        investimento.save()
                        if form_outros_invest.cleaned_data['taxa'] > 0:
                            InvestimentoTaxa.objects.create(investimento=investimento, valor=form_outros_invest.cleaned_data['taxa'])
                        divisao_operacao = DivisaoInvestimento(investimento=investimento, divisao=investidor.divisaoprincipal.divisao, 
                                                               quantidade=investimento.quantidade)
                        divisao_operacao.save()
                        messages.success(request, 'Investimento inserido com sucesso')
                        return HttpResponseRedirect(reverse('outros_investimentos:historico_outros_invest'))
                except:
                    messages.error(request, 'Houve um erro ao inserir o investimento')
                    if settings.ENV == 'DEV':
                        raise
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro ao gerar investimento na seção outros investimentos, com uma divisão', traceback.format_exc())
            
        for erro in [erro for erro in form_outros_invest.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_outros_invest = InvestimentoForm(investidor=investidor)
        formset_divisao = DivisaoOutrosInvestimentosFormSet(investidor=investidor)
    
    return TemplateResponse(request, 'outros_investimentos/inserir_investimento.html', {'form_outros_invest': form_outros_invest, \
                                                                                              'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@adiciona_titulo_descricao('Listar outros investimentos', 'Lista de investimentos cadastrados pelo investidor')
def listar_investimentos(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'outros_investimentos/listar_investimentos.html', {'investimentos': list()})
    
    investimentos = Investimento.objects.filter(investidor=investidor)
    
    return TemplateResponse(request, 'outros_investimentos/listar_investimentos.html', {'investimentos': investimentos})

@login_required
@adiciona_titulo_descricao('Painel de Outros Investimentos', 'Posição atual do investidor em outros investimentos')
def painel(request):
    investidor = request.user.investidor
    qtd_investimentos = calcular_valor_outros_investimentos_ate_data(investidor)
    
    investimentos = Investimento.objects.filter(id__in=qtd_investimentos.keys())
    
    return TemplateResponse(request, 'outros_investimentos/painel.html', {'investimentos': investimentos})

@adiciona_titulo_descricao('', '')
def sobre(request):
    
    return TemplateResponse(request, 'outros_investimentos/sobre.html', {})