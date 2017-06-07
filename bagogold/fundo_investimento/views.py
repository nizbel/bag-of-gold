# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from bagogold.bagogold.decorators import em_construcao, \
	adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import \
	DivisaoOperacaoFundoInvestimentoFormSet
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFundoInvestimento, \
	Divisao
from bagogold.fundo_investimento.forms import OperacaoFundoInvestimentoForm
from bagogold.fundo_investimento.models import OperacaoFundoInvestimento, \
	HistoricoValorCotas, FundoInvestimento
from bagogold.fundo_investimento.utils import \
	calcular_qtd_cotas_ate_dia_por_fundo
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
import calendar
import datetime

@em_construcao('Fundo de investimento')
@login_required
def detalhar_fundo(request, fundo_id):
	pass

@em_construcao('Fundo de investimento')
@login_required
def editar_operacao_fundo_investimento(request, id):
    investidor = request.user.investidor
    
    operacao_fundo_investimento = OperacaoFundoInvestimento.objects.get(pk=id)
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if operacao_fundo_investimento.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoFundoInvestimento, DivisaoOperacaoFundoInvestimento, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoFundoInvestimentoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(request.POST, instance=operacao_fundo_investimento, investidor=investidor)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_fundo_investimento, investidor=investidor) if varias_divisoes else None
            
            if form_operacao_fundo_investimento.is_valid():
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_fundo_investimento.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação editada com sucesso')
                        return HttpResponseRedirect(reverse('fundo_investimento:historico_fundo_investimento'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                        
                else:
                    operacao_fundo_investimento.save()
                    divisao_operacao = DivisaoOperacaoFundoInvestimento.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_fundo_investimento)
                    divisao_operacao.quantidade = operacao_fundo_investimento.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('fundo_investimento:historico_fundo_investimento'))
            for erros in form_operacao_fundo_investimento.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
        elif request.POST.get("delete"):
            # Verifica se, em caso de compra, a quantidade de cotas do investidor não fica negativa
            if operacao_fundo_investimento.tipo_operacao == 'C' and calcular_qtd_cotas_ate_dia_por_fundo(investidor, operacao_fundo_investimento.fundo_investimento.id, datetime.date.today()) - operacao_fundo_investimento.quantidade < 0:
                messages.error(request, 'Operação de compra não pode ser apagada pois quantidade atual para o fundo %s seria negativa' % (operacao_fundo_investimento.fundo_investimento))
            else:
                divisao_fundo_investimento = DivisaoOperacaoFundoInvestimento.objects.filter(operacao=operacao_fundo_investimento)
                for divisao in divisao_fundo_investimento:
                    divisao.delete()
                operacao_fundo_investimento.delete()
                messages.success(request, 'Operação apagada com sucesso')
                return HttpResponseRedirect(reverse('td:historico_td'))
 
    else:
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(instance=operacao_fundo_investimento, investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=operacao_fundo_investimento, investidor=investidor)
            
    return TemplateResponse(request, 'fundo_investimento/editar_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, 'formset_divisao': formset_divisao, \
                                                                                             'varias_divisoes': varias_divisoes})  

@em_construcao('Fundo de investimento')
@login_required
def historico(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data') 
    # Se investidor não tiver operações, retornar vazio
    if not operacoes:
        return TemplateResponse(request, 'fundo_investimento/historico.html', {'dados': {}})
    # Prepara o campo valor atual
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
        else:
            operacao.tipo = 'Venda'
            
    
    total_gasto = 0
    total_patrimonio = 0
    # Guarda quantidade de cotas
    fundos_investimento = {}
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    # Adicionar primeira data com valor 0
    graf_gasto_total = list()
    graf_patrimonio = list()

    for operacao in operacoes:   
        total_patrimonio = 0  
        
        if operacao.fundo_investimento not in fundos_investimento.keys():
            fundos_investimento[operacao.fundo_investimento] = operacao.fundo_investimento
            fundos_investimento[operacao.fundo_investimento].qtd_cotas = 0
            fundos_investimento[operacao.fundo_investimento].valor_cotas = 0
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            operacao.valor_cota = operacao.valor / operacao.quantidade
            total_gasto += operacao.valor
            fundos_investimento[operacao.fundo_investimento].qtd_cotas += operacao.quantidade
            fundos_investimento[operacao.fundo_investimento].valor_cotas = (operacao.valor / operacao.quantidade)
                
        elif operacao.tipo_operacao == 'V':
            total_gasto -= operacao.valor
            fundos_investimento[operacao.fundo_investimento].qtd_cotas -= operacao.quantidade
            fundos_investimento[operacao.fundo_investimento].valor_cotas = (operacao.valor / operacao.quantidade)
        
        for fundo in fundos_investimento:
            total_patrimonio += (fundo.valor_cotas * fundo.qtd_cotas)
            
        # Formatar data para inserir nos gráficos
        data_formatada = str(calendar.timegm(operacao.data.timetuple()) * 1000)    
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_gasto_total) > 0 and graf_gasto_total[-1][0] == data_formatada:
            graf_gasto_total[len(graf_gasto_total)-1][1] = float(total_gasto)
        else:
            graf_gasto_total += [[data_formatada, float(total_gasto)]]
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
            graf_patrimonio[len(graf_patrimonio)-1][1] = float(total_patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(total_patrimonio)]]
        
    # Adicionar data atual
    # Formatar data para inserir nos gráficos
    data_formatada = str(calendar.timegm(datetime.date.today().timetuple()) * 1000)    
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_gasto_total) > 0 and graf_gasto_total[-1][0] == data_formatada:
        graf_gasto_total[len(graf_gasto_total)-1][1] = float(total_gasto)
    else:
        graf_gasto_total += [[data_formatada, float(total_gasto)]]
     
    total_patrimonio = 0  
    # Calcular patrimônio atual
    for fundo in fundos_investimento:
        fundo.data_ultima_operacao = operacoes.filter(fundo_investimento=fundo).order_by('-data')[0].data
        historico_cotas = HistoricoValorCotas.objects.filter(fundo_investimento=fundo, data__gt=fundo.data_ultima_operacao).order_by('-data')
        if historico_cotas:
            total_patrimonio += (fundo.qtd_cotas * historico_cotas[0].valor_cota)
        else:
            total_patrimonio += (fundo.valor_cotas * fundo.qtd_cotas)
    
    # Verifica se altera ultima posicao do grafico ou adiciona novo registro
    if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
        graf_patrimonio[len(graf_patrimonio)-1][1] = float(total_patrimonio)
    else:
        graf_patrimonio += [[data_formatada, float(total_patrimonio)]]
    
    dados = {}
    dados['total_gasto'] = total_gasto
    dados['patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio - total_gasto
    dados['lucro_percentual'] = (total_patrimonio - total_gasto) / total_gasto * 100
    
    return TemplateResponse(request, 'fundo_investimento/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio})
    

@em_construcao('Fundo de investimento')
@login_required
def inserir_operacao_fundo_investimento(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoFundoInvestimentoFormSet = inlineformset_factory(OperacaoFundoInvestimento, DivisaoOperacaoFundoInvestimento, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoFundoInvestimentoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(request.POST, investidor=investidor)
        formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar Fundo de Investimento
        if form_operacao_fundo_investimento.is_valid():
            operacao_fundo_investimento = form_operacao_fundo_investimento.save(commit=False)
            operacao_fundo_investimento.investidor = investidor
            
            # Testar se várias divisões
            if varias_divisoes:
                formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(request.POST, instance=operacao_fundo_investimento, investidor=investidor)
                if formset_divisao_fundo_investimento.is_valid():
                    operacao_fundo_investimento.save()
                    formset_divisao_fundo_investimento.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('fundo_investimento:historico_fundo_investimento'))
                for erro in formset_divisao_fundo_investimento.non_form_errors():
                    messages.error(request, erro)
            else:
                operacao_fundo_investimento.save()
                divisao_operacao = DivisaoOperacaoFundoInvestimento(operacao=operacao_fundo_investimento, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_fundo_investimento.quantidade)
                divisao_operacao.save()
                messages.success(request, 'Operação inserida com sucesso')
                return HttpResponseRedirect(reverse('fundo_investimento:historico_fundo_investimento'))
            
        for erros in form_operacao_fundo_investimento.errors.values():
            for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                messages.error(request, erro.message)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(investidor=investidor)
        formset_divisao_fundo_investimento = DivisaoFundoInvestimentoFormSet(investidor=investidor)
    return TemplateResponse(request, 'fundo_investimento/inserir_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, \
                                                                                              'formset_divisao_fundo_investimento': formset_divisao_fundo_investimento, 'varias_divisoes': varias_divisoes})

@em_construcao('Fundo de investimento')
@login_required
@adiciona_titulo_descricao('Listar fundos de investimento cadastrados', 'Lista os fundos cadastrados no sistema e suas principais características')
def listar_fundos(request):
    filtro = {}
    filtro['situacoes'] = FundoInvestimento.TIPOS_SITUACAO + [(0, u'Não terminados')]
    filtro['classes'] = [(-1, 'Todas')] + FundoInvestimento.TIPOS_CLASSE
    filtro['opcoes_iq'] = [(1, u'Não exclusivos'), (0, u'Exclusivos'), (-1, 'Todos')]

    # Montar filtro
    if request.POST:
        # Situação
        filtro['situacao'] = int(request.POST.get('situacao', 0))
        if filtro['situacao'] == 0:
            filtro_situacao = [codigo for codigo, _ in FundoInvestimento.TIPOS_SITUACAO if codigo != FundoInvestimento.SITUACAO_TERMINADO]
        else:
            filtro_situacao = [filtro['situacao']]

        # Classe
        filtro['classe'] = int(request.POST.get('classe', -1))
        if filtro['classe'] == -1:
            filtro_classe = [codigo for codigo, _ in FundoInvestimento.TIPOS_CLASSE]
        else:
            filtro_classe = [filtro['classe']]

        # Apenas investidores qualificados
        filtro['iq'] = int(request.POST.get('iq', -1))
        if filtro['iq'] == -1:
            filtro_iq = [True, False]
        else:
            filtro_iq = [True] if filtro['iq'] == 0 else [False]

        # Nome
        filtro['nome'] = request.POST.get('nome', '')
        if len(filtro['nome']) > 100:
            filtro_nome = filtro['nome'][:100]
        else:
            filtro_nome = filtro['nome']
    else:
        filtro_situacao = [FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL]
        filtro_classe = [codigo for codigo, _ in FundoInvestimento.TIPOS_CLASSE]
        filtro['iq'] = 1
        filtro_iq = [False]
        filtro_nome = ''
    fundos_investimento = FundoInvestimento.objects.filter(situacao__in=filtro_situacao, classe__in=filtro_classe, exclusivo_qualificados__in=filtro_iq, nome__icontains=filtro_nome)
    
    for fundo in fundos_investimento:
#         # Preparar o valor mais atual de rendimento
#         if HistoricoValorCotas.objects.filter(fundo_investimento=fundo).exists():
#             historico_mais_recente = HistoricoValorCotas.objects.filter(fundo_investimento=fundo).order_by('-data')[0]
#             fundo.data_valor_cota = historico_mais_recente.data
#             fundo.valor_cota = historico_mais_recente.valor_cota
#         else:
#             fundo.data_valor_cota = None
#             fundo.valor_cota = None
        
        # Prazo
        if fundo.tipo_prazo == 'C':
            fundo.tipo_prazo = 'Curto'
        elif fundo.tipo_prazo == 'L':
            fundo.tipo_prazo = 'Longo'

    return TemplateResponse(request, 'fundo_investimento/listar_fundo_investimento.html', {'fundos_investimento': fundos_investimento, 'filtro': filtro})

@em_construcao('Fundo de investimento')
@login_required
@adiciona_titulo_descricao('Painel de Fundos de Investimento', 'Posição atual do investidor em Fundos de Investimento')
def painel(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    # Se não há operações, retornar
    if not operacoes:
        return TemplateResponse(request, 'fundo_investimento/painel.html', {'operacoes': operacoes, 'dados': {}})
    
    # Fundos do investidor
    fundos = {}
    
    # Prepara o campo valor atual
    for operacao in operacoes:
        if operacao.fundo_investimento.nome not in fundos.keys():
            fundos[operacao.fundo_investimento.nome] = operacao.fundo_investimento
        if operacao.tipo_operacao == 'C':
            fundos[operacao.fundo_investimento.nome].quantidade += operacao.quantidade
        else:
            fundos[operacao.fundo_investimento.nome].quantidade -= operacao.quantidade
    
    fundos = [fundo for fundo in fundos if fundo.quantidade > 0]
    
    for fundo in fundos:
        fundo.data_atual = datetime.date.today()
        fundo.valor_cota_atual = fundo.valor_no_dia()
        fundo.total_atual = fundo.valor_cota_atual * fundo.quantidade
        fundo.imposto_renda = Decimal(0)
        fundo.iof = Decimal(0)
    
    total_atual = 0    
    total_ir = 0
    total_iof = 0
    total_ganho_prox_dia = 0
#     for operacao in operacoes:
#         # Calcular impostos
#         qtd_dias = (datetime.date.today() - operacao.data).days
# #         print qtd_dias, calcular_iof_regressivo(qtd_dias)
#         # IOF
#         operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.inicial)
#         # IR
#         if qtd_dias <= 180:
#             operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.inicial - operacao.iof)
#         elif qtd_dias <= 360:
#             operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.inicial - operacao.iof)
#         elif qtd_dias <= 720:
#             operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.inicial - operacao.iof)
#         else: 
#             operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.inicial - operacao.iof)
#         total_ir += operacao.imposto_renda
#         total_iof += operacao.iof
    
    # Popular dados
    dados = {}
    dados['total_atual'] = total_atual
    dados['total_ir'] = total_ir
    dados['total_iof'] = total_iof
    dados['total_ganho_prox_dia'] = total_ganho_prox_dia
    
    return TemplateResponse(request, 'fundo_investimento/painel.html', {'fundos': fundos, 'dados': dados})

@adiciona_titulo_descricao('Sobre Fundos de Investimento', 'Detalha o que são Fundos de Investimento')
def sobre(request):
    return TemplateResponse(request, 'fundo_investimento/sobre.html', {})