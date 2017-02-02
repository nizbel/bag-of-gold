# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.debenture import OperacaoDebentureForm
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoDebentureFormSet
from bagogold.bagogold.models.debentures import OperacaoDebenture, Debenture, \
    HistoricoValorDebenture
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoDebenture
from bagogold.bagogold.utils.misc import \
    formatar_zeros_a_direita_apos_2_casas_decimais
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.db.models.query_utils import Q
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django.template.response import TemplateResponse
from itertools import chain
from operator import attrgetter
import calendar
import datetime
import json



@login_required
def detalhar_debenture(request, debenture_id):
    try:
        debenture = Debenture.objects.get(id=debenture_id)
    except Debenture.DoesNotExist:
        messages.error(request, 'Debênture selecionado é inválido')
        return HttpResponseRedirect(reverse('listar_debentures'))
    
    debenture.valor_emissao = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.valor_emissao))
    if debenture.data_fim:
        debenture.valor_atual = Decimal('0.00') 
    else:
        historico = HistoricoValorDebenture.objects.filter(debenture=debenture).order_by('-data')[0]
        debenture.valor_atual = historico.valor_nominal + historico.juros
        debenture.valor_atual = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.valor_atual))
    
    return TemplateResponse(request, 'debentures/detalhar_debenture.html', {'debenture': debenture})

@login_required
def editar_operacao_debenture(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_debenture = OperacaoDebenture.objects.get(pk=operacao_id)
    
    # Verificar se a operação é do investidor logado
    if operacao_debenture.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoDebenture, DivisaoOperacaoDebenture, fields=('divisao', 'quantidade'),
                                            extra=0, formset=DivisaoOperacaoDebentureFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_debenture = OperacaoDebentureForm(request.POST, instance=operacao_debenture)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_debenture, investidor=investidor) if varias_divisoes else None
            
            if form_operacao_debenture.is_valid():
                # Validar de acordo com a quantidade de divisões
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_debenture.save()
                        formset_divisao.save()
#                         for form_divisao_operacao in [form for form in formset_divisao if form.cleaned_data]:
#                             # Ignorar caso seja apagado
#                             if 'DELETE' in form_divisao_operacao.cleaned_data and form_divisao_operacao.cleaned_data['DELETE']:
#                                 pass
#                             else:
#                                 divisao_operacao = form_divisao_operacao.save(commit=False)
#                                 if hasattr(divisao_operacao, 'usoproventosoperacaofii'):
#                                     if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] == None or form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] == 0:
#                                         divisao_operacao.usoproventosoperacaofii.delete()
#                                     else:
#                                         divisao_operacao.usoproventosoperacaofii.qtd_utilizada = form_divisao_operacao.cleaned_data['qtd_proventos_utilizada']
#                                         divisao_operacao.usoproventosoperacaofii.save()
#                                 else:
#                                     if form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] != None and form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'] > 0:
#                                         # TODO remover operação de uso proventos
#                                         divisao_operacao.usoproventosoperacaofii = UsoProventosOperacaoDebenture(qtd_utilizada=form_divisao_operacao.cleaned_data['qtd_proventos_utilizada'], operacao=operacao_debenture)
#                                         divisao_operacao.usoproventosoperacaofii.save()
                        
                        messages.success(request, 'Operação alterada com sucesso')
                        return HttpResponseRedirect(reverse('historico_debenture'))
                    
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                    
                else:    
                    operacao_debenture.save()
                    divisao_operacao = DivisaoOperacaoDebenture.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_debenture)
                    divisao_operacao.quantidade = operacao_debenture.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação alterada com sucesso')
                    return HttpResponseRedirect(reverse('historico_debenture'))
                        
            for erro in [erro for erro in form_operacao_debenture.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            divisao_debenture = DivisaoOperacaoDebenture.objects.filter(operacao=operacao_debenture)
            for divisao in divisao_debenture:
                if hasattr(divisao, 'usoproventosoperacaofii'):
                    divisao.usoproventosoperacaofii.delete()
                divisao.delete()
            operacao_debenture.delete()
            messages.success(request, 'Operação apagada com sucesso')
            return HttpResponseRedirect(reverse('historico_debenture'))

    else:
        form_operacao_debenture = OperacaoDebentureForm(instance=operacao_debenture)
        formset_divisao = DivisaoFormSet(instance=operacao_debenture, investidor=investidor)
            
    return TemplateResponse(request, 'debentures/editar_operacao_debenture.html', {'form_operacao_debenture': form_operacao_debenture,
                                                               'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})   

    
@login_required
def historico(request):
    investidor = request.user.investidor
    
    operacoes = OperacaoDebenture.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data') 
    
    # Se investidor não tiver feito operações
    if not operacoes:
        return TemplateResponse(request, 'debentures/historico.html', {'usuario_tem_operacoes': False})
    
    for operacao in operacoes:
        operacao.valor_unitario = operacao.preco_unitario
    
    # TODO adicionar proventos
    
    # Proventos devem ser computados primeiro na data EX
    lista_conjunta = sorted(chain(operacoes),
                            key=attrgetter('data'))
    
    qtd_titulos = {}
    total_investido = Decimal(0)
#     total_proventos = Decimal(0)
    
    # Gráfico de acompanhamento de investimentos vs patrimonio
    graf_investido_total = list()
    graf_patrimonio = list()
    
    # Verifica se foi adicionada alguma operação na data de hoje
    houve_operacao_hoje = False
    
    for item in lista_conjunta:   
        if item.debenture.codigo not in qtd_titulos.keys():
            qtd_titulos[item.debenture.codigo] = Decimal(0)       
        if isinstance(item, OperacaoDebenture):
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                item.tipo = 'Compra'
                item.total = Decimal(-1) * (item.quantidade * item.preco_unitario + \
                item.taxa)
                total_investido += item.total
                qtd_titulos[item.debenture.codigo] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                item.tipo = 'Venda'
                item.total = (item.quantidade * item.preco_unitario - \
                item.taxa)
                total_investido += item.total
                qtd_titulos[item.debenture.codigo] -= item.quantidade
                
        # Prepara data
        data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_investido_total) > 0 and graf_investido_total[-1][0] == data_formatada:
            graf_investido_total[len(graf_investido_total)-1][1] = float(-total_investido)
        else:
            graf_investido_total += [[data_formatada, float(-total_investido)]]
        
        patrimonio = 0
        # Verifica se houve operacao hoje
        if item.data != datetime.date.today():
            for debenture in qtd_titulos.keys():
                # Pegar último dia util com negociação da debenture para calculo do patrimonio
                ultimo_dia_util = item.data
                while not HistoricoValorDebenture.objects.filter(data=ultimo_dia_util, debenture__codigo=debenture):
                    ultimo_dia_util -= datetime.timedelta(days=1)
                patrimonio += (qtd_titulos[debenture] * HistoricoValorDebenture.objects.get(debenture__codigo=debenture, data=ultimo_dia_util).valor_total())
        else:
            houve_operacao_hoje = True
            for fii in qtd_titulos.keys():
                # Busca histórico do último dia útil
                patrimonio += (Decimal(qtd_titulos[fii]) * debenture.objects.filter(debenture__codigo=debenture).order_by('-data')[0].valor_total())
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
            graf_patrimonio[len(graf_patrimonio)-1][1] = float(patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(patrimonio)]]
        
    # Adicionar valor mais atual para todos os gráficos
    if not houve_operacao_hoje:
        data_mais_atual = datetime.date.today()
        graf_investido_total += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(-total_investido)]]
        
        patrimonio = 0
        for debenture in qtd_titulos.keys():
            if qtd_titulos[debenture] > 0:
                patrimonio += (qtd_titulos[debenture] * HistoricoValorDebenture.objects.filter(debenture__codigo=debenture)[0].valor_total())
                
        graf_patrimonio += [[str(calendar.timegm(data_mais_atual.timetuple()) * 1000), float(patrimonio)]]
        
    dados = {}
    dados['total_investido'] = -total_investido
    dados['patrimonio'] = patrimonio
    dados['lucro'] = patrimonio + total_investido
    dados['lucro_percentual'] = (patrimonio + total_investido) / -total_investido * 100
    return TemplateResponse(request, 'debentures/historico.html', {'dados': dados, 'lista_conjunta': lista_conjunta, 'graf_investido_total': graf_investido_total, 
                                                                   'graf_patrimonio': graf_patrimonio, 'usuario_tem_operacoes': True})
    
@login_required
def inserir_operacao_debenture(request):
    investidor = request.user.investidor
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoDebenture, DivisaoOperacaoDebenture, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoDebentureFormSet)
    
    if request.method == 'POST':
        form_operacao_debenture = OperacaoDebentureForm(request.POST)
        formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        print 'Ver se operacao vale'
        if form_operacao_debenture.is_valid():
            print 'vale'
            operacao_debenture = form_operacao_debenture.save(commit=False)
            print 'quantidade:', operacao_debenture.quantidade
            operacao_debenture.investidor = investidor
            if varias_divisoes:
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_debenture, investidor=investidor)
                if formset_divisao.is_valid():
                    operacao_debenture.save()
                    formset_divisao.save()
                        
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('historico_debenture'))
                
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
                    
            else:
                operacao_debenture.save()
                divisao_operacao = DivisaoOperacaoDebenture(operacao=operacao_debenture, quantidade=operacao_debenture.quantidade, divisao=investidor.divisaoprincipal.divisao)
                divisao_operacao.save()
                messages.success(request, 'Operação inserida com sucesso')
                return HttpResponseRedirect(reverse('historico_debenture'))
        for erro in [erro for erro in form_operacao_debenture.non_field_errors()]:
            messages.error(request, erro)
            
    else:
        form_operacao_debenture = OperacaoDebentureForm()
        formset_divisao = DivisaoFormSet(investidor=investidor)
            
    return TemplateResponse(request, 'debentures/inserir_operacao_debenture.html', {'form_operacao_debenture': form_operacao_debenture, 'formset_divisao': formset_divisao, 
                                                                                    'varias_divisoes': varias_divisoes})

@login_required
def listar_debentures(request):
    debentures = Debenture.objects.all()
    
    for debenture in debentures:
        debenture.porcentagem = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.porcentagem))
        
        if hasattr(debenture, 'jurosdebenture'):
            debenture.jurosdebenture.taxa = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.jurosdebenture.taxa))
        if hasattr(debenture, 'amortizacaodebenture'):
            debenture.amortizacaodebenture.taxa = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.amortizacaodebenture.taxa))
        if hasattr(debenture, 'premiodebenture'):
            debenture.premiodebenture.taxa = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(debenture.premiodebenture.taxa))
    
    return TemplateResponse(request, 'debentures/listar_debentures.html', {'debentures': debentures})

@login_required
def listar_debentures_validas_na_data(request):
    # Verifica se é uma data válida
    try:
        data = datetime.datetime.strptime(request.GET['data'], '%d/%m/%Y').date()
    except ValueError:
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': 'Data deve estar no formato DD/MM/AAAA'}), content_type = "application/json") 
    
    if data > datetime.date.today():
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': 'Data não pode ser futura'}), content_type = "application/json") 
    
    debentures_validas = list(Debenture.objects.filter(data_emissao__lte=data).filter((Q(data_fim__gt=data) | Q(data_fim__isnull=True))).values_list('id', flat=True))
    
    return HttpResponse(json.dumps({'resultado': True, 'debentures_validas': debentures_validas}), content_type = "application/json") 

@login_required
def painel(request):
    investidor = request.user.investidor
    
    return TemplateResponse(request, 'debentures/painel.html', {})