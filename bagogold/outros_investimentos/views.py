# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoInvestimentoFormSet
from bagogold.bagogold.models.divisoes import DivisaoInvestimento, Divisao
from bagogold.outros_investimentos.forms import InvestimentoForm
from bagogold.outros_investimentos.models import Investimento, InvestimentoTaxa, \
    Rendimento, Amortizacao
from bagogold.outros_investimentos.utils import \
    calcular_valor_outros_investimentos_ate_data
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
import datetime
import traceback

def detalhar_investimento(request, id_investimento):
    investidor = request.user.investidor
    
    investimento = get_object_or_404(Investimento, id=id_investimento)
    if investimento.investidor != investidor:
        raise PermissionDenied
    
    historico_rendimentos = Rendimento.objects.filter(investimento=investimento)
    historico_amortizacoes = Amortizacao.objects.filter(investimento=investimento)
    
    # Inserir dados do investimento
#     cdb_rdb.tipo = cdb_rdb.descricao_tipo()
#     cdb_rdb.carencia_atual = cdb_rdb.carencia_atual()
#     cdb_rdb.porcentagem_atual = cdb_rdb.porcentagem_atual()
    
    # Preparar estatísticas zeradas
    investimento.total_investido = investimento.quantidade
    investimento.total_amortizacoes = sum(investimento.amortizacao_set.filter(data__lte=datetime.date.today()).values_list('valor', flat=True))
    investimento.saldo_atual = investimento.quantidade - investimento.total_amortizacoes
    investimento.total_rendimentos = sum(investimento.rendimento_set.filter(data__lte=datetime.date.today()).values_list('valor', flat=True))
#     cdb_rdb.total_ir = Decimal(0)
#     cdb_rdb.total_iof = Decimal(0)
    investimento.lucro = investimento.saldo_atual + investimento.total_amortizacoes + investimento.total_rendimentos - investimento.total_investido
    investimento.lucro_percentual = Decimal(0)
    
#     operacoes = OperacaoCDB_RDB.objects.filter(investimento=cdb_rdb).order_by('data')
#     # Contar total de operações já realizadas 
#     cdb_rdb.total_operacoes = len(operacoes)
#     # Remover operacoes totalmente vendidas
#     operacoes = [operacao for operacao in operacoes if operacao.qtd_disponivel_venda() > 0]
#     if operacoes:
#         historico_di = HistoricoTaxaDI.objects.filter(data__range=[operacoes[0].data, datetime.date.today()])
#         for operacao in operacoes:
#             # Total investido
#             cdb_rdb.total_investido += operacao.qtd_disponivel_venda()
#             
#             # Saldo atual
#             taxas = historico_di.filter(data__gte=operacao.data).values('taxa').annotate(qtd_dias=Count('taxa'))
#             taxas_dos_dias = {}
#             for taxa in taxas:
#                 taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
#             operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.qtd_disponivel_venda(), operacao.porcentagem())
#             cdb_rdb.saldo_atual += operacao.atual
#             
#             # Calcular impostos
#             qtd_dias = (datetime.date.today() - operacao.data).days
#             # IOF
#             operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.quantidade)
#             # IR
#             if qtd_dias <= 180:
#                 operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.quantidade - operacao.iof)
#             elif qtd_dias <= 360:
#                 operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.quantidade - operacao.iof)
#             elif qtd_dias <= 720:
#                 operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.quantidade - operacao.iof)
#             else: 
#                 operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.quantidade - operacao.iof)
#             cdb_rdb.total_ir += operacao.imposto_renda
#             cdb_rdb.total_iof += operacao.iof
#     
#         # Pegar outras estatísticas
#         str_auxiliar = str(cdb_rdb.saldo_atual.quantize(Decimal('.0001')))
#         cdb_rdb.saldo_atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#         
#         cdb_rdb.lucro = cdb_rdb.saldo_atual - cdb_rdb.total_investido
#         cdb_rdb.lucro_percentual = cdb_rdb.lucro / cdb_rdb.total_investido * 100
    try: 
        investimento.dias_prox_rendimento = ((min(rendimento.data for rendimento in investimento.rendimento_set.filter(data__gt=datetime.date.today()))) \
                                              - datetime.date.today()).days
    except ValueError:
        investimento.dias_prox_rendimento = 0
    try: 
        investimento.dias_prox_amortizacao = ((min(amortizacao.data for amortizacao in investimento.amortizacao_set.filter(data__gt=datetime.date.today()))) \
                                               - datetime.date.today()).days
    except ValueError:
        investimento.dias_prox_amortizacao = 0
    
    
    return TemplateResponse(request, 'outros_investimentos/detalhar_investimento.html', {'investimento': investimento, 'historico_rendimentos': historico_rendimentos,
                                                                       'historico_amortizacoes': historico_amortizacoes})

def editar_investimento(request, id_investimento):
    investidor = request.user.investidor
    
    investimento = OperacaoCriptomoeda.objects.get(pk=id_operacao)
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
            taxa_moeda = taxa.moeda.id
        else:
            taxa_valor = 0
            taxa_moeda = None
        if OperacaoCriptomoedaMoeda.objects.filter(operacao=operacao_criptomoeda).exists():
            moeda = OperacaoCriptomoedaMoeda.objects.get(operacao=operacao_criptomoeda)
            moeda_utilizada = moeda.criptomoeda.id
        else:
            moeda_utilizada = None
        form_operacao_criptomoeda = OperacaoCriptomoedaForm(instance=operacao_criptomoeda, investidor=investidor, initial={'taxa': taxa_valor, 'taxa_moeda': taxa_moeda, 'moeda_utilizada': moeda_utilizada})
        formset_divisao = DivisaoFormSet(instance=operacao_criptomoeda, investidor=investidor)
        
    # Preparar nome de fundo selecionado
#     if request.POST.get('criptomoeda', -1) != -1:
#         fundo_selecionado = Criptomoeda.objects.get(id=request.POST['criptomoeda'])
#     else:
#         fundo_selecionado = operacao_criptomoeda.criptomoeda.nome
    return TemplateResponse(request, 'criptomoedas/editar_operacao_criptomoeda.html', {'form_operacao_criptomoeda': form_operacao_criptomoeda, 'formset_divisao': formset_divisao, \
                                                                                             'varias_divisoes': varias_divisoes}) 

def historico(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'outros_investimentos/historico.html', {'dados': {}, 'graf_patrimonio': list(), 'graf_total_investido': list(), 
                                                                                 'investimentos': list()})
    
    investimentos = Investimento.objects.filter(investidor=investidor).order_by('data')
    
    if not investimentos:
        return TemplateResponse(request, 'outros_investimentos/historico.html', {'dados': {}, 'graf_patrimonio': list(), 'graf_total_investido': list(), 
                                                                                 'investimentos': list()})
        
    dados = {}
    
    graf_patrimonio = list()
    graf_total_investido = list()
    
    total_patrimonio = 0
    total_investido = 0
    
    for investimento in investimentos:
        investimento.rendimentos = sum(investimento.rendimento_set.values_list('valor', flat=True))
        investimento.amortizacoes = sum(investimento.amortizacao_set.values_list('valor', flat=True))
        
        total_investido += investimento.quantidade - investimento.amortizacoes
        
    dados['total_investido'] = total_investido
    dados['total_patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio - total_investido
    dados['lucro_percentual'] = dados['lucro'] / 1 if total_investido == 0 else dados['lucro'] / dados['total_investido'] * 100
    
    return TemplateResponse(request, 'outros_investimentos/historico.html', {'dados': dados, 'graf_patrimonio': graf_patrimonio, 'graf_total_investido': graf_total_investido,
                                                                             'investimentos': investimentos})

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
                formset_divisao = DivisaoOutrosInvestimentosFormSet(request.POST, instance=investimento, investidor=investidor)
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