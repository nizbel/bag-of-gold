# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.debenture import OperacaoDebentureForm
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoDebentureFormSet
from bagogold.bagogold.models.debentures import OperacaoDebenture, Debenture, \
    HistoricoValorDebenture
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoDebenture
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic
from bagogold.bagogold.models.td import HistoricoIPCA
from bagogold.bagogold.utils.debenture import calcular_valor_debentures_ate_dia
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas
from bagogold.bagogold.utils.misc import \
    formatar_zeros_a_direita_apos_2_casas_decimais, qtd_dias_uteis_no_periodo
from bagogold.bagogold.utils.td import calcular_valor_acumulado_ipca
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
        return HttpResponseRedirect(reverse('debentures:listar_debentures'))
    
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
                        return HttpResponseRedirect(reverse('debentures:historico_debenture'))
                    
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                    
                else:    
                    operacao_debenture.save()
                    divisao_operacao = DivisaoOperacaoDebenture.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_debenture)
                    divisao_operacao.quantidade = operacao_debenture.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação alterada com sucesso')
                    return HttpResponseRedirect(reverse('debentures:historico_debenture'))
                        
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
            return HttpResponseRedirect(reverse('debentures:historico_debenture'))

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
                item.total = -(item.quantidade * item.preco_unitario + item.taxa)
                total_investido += item.total
                qtd_titulos[item.debenture.codigo] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                item.tipo = 'Venda'
                item.total = (item.quantidade * item.preco_unitario - item.taxa)
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
    if total_investido != 0:
        dados['lucro_percentual'] = (patrimonio + total_investido) / -total_investido * 100
    else:
        dados['lucro_percentual'] = 0
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
        if form_operacao_debenture.is_valid():
            operacao_debenture = form_operacao_debenture.save(commit=False)
            operacao_debenture.investidor = investidor
            if varias_divisoes:
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_debenture, investidor=investidor)
                if formset_divisao.is_valid():
                    operacao_debenture.save()
                    formset_divisao.save()
                        
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('debentures:historico_debenture'))
                
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
                    
            else:
                operacao_debenture.save()
                divisao_operacao = DivisaoOperacaoDebenture(operacao=operacao_debenture, quantidade=operacao_debenture.quantidade, divisao=investidor.divisaoprincipal.divisao)
                divisao_operacao.save()
                messages.success(request, 'Operação inserida com sucesso')
                return HttpResponseRedirect(reverse('debentures:historico_debenture'))
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
    
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoDebenture.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data') 
    if not operacoes:
        dados = {}
        dados['total_investido'] = Decimal(0)
        dados['total_nominal'] = Decimal(0)
        dados['total_juros'] = Decimal(0)
        dados['total_premio'] = Decimal(0)
        dados['total_somado'] = Decimal(0)
        dados['total_rendimento_ate_vencimento'] = Decimal(0)
        return TemplateResponse(request, 'debentures/painel.html', {'debentures': {}, 'dados': dados})
    
    # Quantidade de debêntures do investidor
    debentures = {}
    
    # Prepara o campo valor atual
    for operacao in operacoes:
        if operacao.debenture.id not in debentures.keys():
            debentures[operacao.debenture.id] = operacao.debenture
            debentures[operacao.debenture.id].quantidade = 0
            debentures[operacao.debenture.id].preco_medio = 0
        if operacao.tipo_operacao == 'C':
            debentures[operacao.debenture.id].preco_medio = (debentures[operacao.debenture.id].preco_medio * debentures[operacao.debenture.id].quantidade \
                + operacao.quantidade * operacao.preco_unitario + operacao.taxa)/(debentures[operacao.debenture.id].quantidade + operacao.quantidade)
            debentures[operacao.debenture.id].quantidade += operacao.quantidade
        else:
            debentures[operacao.debenture.id].preco_medio = (debentures[operacao.debenture.id].preco_medio * debentures[operacao.debenture.id].quantidade \
                - operacao.quantidade * operacao.preco_unitario + operacao.taxa)/(debentures[operacao.debenture.id].quantidade - operacao.quantidade)
            debentures[operacao.debenture.id].quantidade -= operacao.quantidade
    
    # Remover debentures com quantidade zerada
    for debenture_id in debentures.keys():
        if debentures[debenture_id].quantidade == 0:
            del debentures[debenture_id]
    
    total_investido = Decimal(0)
    total_nominal = Decimal(0)
    total_juros = Decimal(0)
    total_premio = Decimal(0)
    total_somado = Decimal(0)
    total_rendimento_ate_vencimento = Decimal(0)
    
    ultima_taxa_di = HistoricoTaxaDI.objects.all().order_by('-data')[0]
    ultima_taxa_selic = HistoricoTaxaSelic.objects.all().order_by('-data')[0]
    ultima_taxa_ipca = HistoricoIPCA.objects.all().order_by('-ano', '-mes')[0]
    
    for debenture_id in debentures.keys():
        debentures[debenture_id].total_investido = debentures[debenture_id].quantidade * debentures[debenture_id].preco_medio
        total_investido += debentures[debenture_id].total_investido
        
        valores_atuais_debenture = HistoricoValorDebenture.objects.filter(debenture__id=debenture_id).order_by('-data')[0]
        debentures[debenture_id].juros_atual = valores_atuais_debenture.juros * debentures[debenture_id].quantidade
        debentures[debenture_id].valor_nominal_atual = valores_atuais_debenture.valor_nominal * debentures[debenture_id].quantidade
        debentures[debenture_id].premio_atual = valores_atuais_debenture.premio * debentures[debenture_id].quantidade
        debentures[debenture_id].total = valores_atuais_debenture.valor_total() * debentures[debenture_id].quantidade
        total_juros += valores_atuais_debenture.juros * debentures[debenture_id].quantidade
        total_nominal += valores_atuais_debenture.valor_nominal * debentures[debenture_id].quantidade
        total_premio += valores_atuais_debenture.premio * debentures[debenture_id].quantidade
        total_somado += valores_atuais_debenture.valor_total() * debentures[debenture_id].quantidade
        
        # Calcular valor estimado no vencimento
        qtd_dias_uteis_ate_vencimento = qtd_dias_uteis_no_periodo(valores_atuais_debenture.data, debentures[debenture_id].data_vencimento)
        if debentures[debenture_id].indice == Debenture.PREFIXADO:
            taxa_anual_pre_mais_juros = debentures[debenture_id].porcentagem + debentures[debenture_id].taxa_juros_atual()
            taxa_mensal_pre_mais_juros = pow(1 + taxa_anual_pre_mais_juros/100, Decimal(1)/12) - 1
            taxa_diaria_pre_mais_juros = pow(1 + taxa_mensal_pre_mais_juros, Decimal(1)/12) - 1
            debentures[debenture_id].valor_rendimento_ate_vencimento = debentures[debenture_id].total * pow(1 + taxa_diaria_pre_mais_juros, qtd_dias_uteis_ate_vencimento)
        elif debentures[debenture_id].indice == Debenture.IPCA:
            # Transformar taxa mensal em anual para somar aos juros da debenture
            ipca_anual = pow(1 + ultima_taxa_ipca.valor * (debentures[debenture_id].porcentagem/100) /Decimal(100), Decimal(12)) - 1
            taxa_mensal_ipca_mais_juros = pow(1 + (ipca_anual + debentures[debenture_id].taxa_juros_atual())/Decimal(100), Decimal(1)/12) - 1
            taxa_diaria_ipca_mais_juros = pow(1 + taxa_mensal_ipca_mais_juros, Decimal(1)/30) - 1
            debentures[debenture_id].valor_rendimento_ate_vencimento = debentures[debenture_id].total * pow(1 + taxa_diaria_ipca_mais_juros, qtd_dias_uteis_ate_vencimento)
        elif debentures[debenture_id].indice == Debenture.DI:
            debentures[debenture_id].valor_rendimento_ate_vencimento = calcular_valor_atualizado_com_taxas({Decimal(ultima_taxa_di.taxa): qtd_dias_uteis_ate_vencimento},
                                                                                                           debentures[debenture_id].total, 
                                                                                                           debentures[debenture_id].porcentagem + debentures[debenture_id].taxa_juros_atual())
        elif debentures[debenture_id].indice == Debenture.SELIC:
            # Transformar SELIC em anual para adicionar juros
            selic_mensal = pow(1 + ultima_taxa_selic.taxa, 30) - 1
            selic_anual = pow(1 + selic_mensal, 12) - 1
            taxa_anual_selic_mais_juros = selic_anual * (debentures[debenture_id].porcentagem / 100) + debentures[debenture_id].taxa_juros_atual() / 100
            taxa_mensal_selic_mais_juros = pow(1 + taxa_anual_selic_mais_juros, Decimal(1)/12) - 1
            taxa_diaria_selic_mais_juros = pow(1 + taxa_mensal_selic_mais_juros, Decimal(1)/30) - 1
            debentures[debenture_id].valor_rendimento_ate_vencimento = debentures[debenture_id].total * pow(1 + taxa_diaria_selic_mais_juros, qtd_dias_uteis_ate_vencimento)
            
        total_rendimento_ate_vencimento += debentures[debenture_id].valor_rendimento_ate_vencimento
    
    # Popular dados
    dados = {}
    dados['total_investido'] = total_investido
    dados['total_nominal'] = total_nominal
    dados['total_juros'] = total_juros
    dados['total_premio'] = total_premio
    dados['total_somado'] = total_somado
    dados['total_rendimento_ate_vencimento'] = total_rendimento_ate_vencimento
    
    return TemplateResponse(request, 'debentures/painel.html', {'debentures': debentures, 'dados': dados})

@login_required
def sobre(request):
    data_atual = datetime.date.today()
    historico_di = HistoricoTaxaDI.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3))
    graf_historico_di = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(valor_historico.taxa)] for valor_historico in historico_di]
        
    historico_ipca = HistoricoIPCA.objects.filter(ano__gte=(data_atual.year-3)).exclude(mes__lt=data_atual.month, ano=data_atual.year-3)
    graf_historico_ipca = [[str(calendar.timegm(valor_historico.data().timetuple()) * 1000), float(valor_historico.valor)] for valor_historico in historico_ipca]
    
    historico_selic = HistoricoTaxaSelic.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3))
    graf_historico_selic = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(pow(valor_historico.taxa_diaria, 252) - 1)*100] for valor_historico in historico_selic]
    
    if request.user.is_authenticated():
        total_atual = sum(calcular_valor_debentures_ate_dia(request.user.investidor).values()).quantize(Decimal('0.01'))
    else:
        total_atual = 0
    
    
    return TemplateResponse(request, 'debentures/sobre.html', {'graf_historico_di': graf_historico_di, 'graf_historico_ipca': graf_historico_ipca, 
                                                               'graf_historico_selic': graf_historico_selic, 'total_atual': total_atual})