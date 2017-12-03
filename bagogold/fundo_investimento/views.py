# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import \
    DivisaoOperacaoFundoInvestimentoFormSet
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFundoInvestimento, \
    Divisao
from bagogold.bagogold.utils.misc import \
    formatar_zeros_a_direita_apos_2_casas_decimais, calcular_iof_regressivo
from bagogold.fundo_investimento.forms import OperacaoFundoInvestimentoForm
from bagogold.fundo_investimento.models import OperacaoFundoInvestimento, \
    HistoricoValorCotas, FundoInvestimento
from bagogold.fundo_investimento.utils import \
    calcular_qtd_cotas_ate_dia_por_fundo, \
    calcular_valor_fundos_investimento_ate_dia
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_admins
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
import calendar
import datetime
import json
import re
import traceback

@adiciona_titulo_descricao('Detalhar fundo de investimento', 'Traz características do fundo, posição do investidor e histórico de cotações')
def detalhar_fundo(request, id_fundo):
    fundo = get_object_or_404(FundoInvestimento, id=id_fundo)
    
    # Preparar o valor mais atual de rendimento
    if HistoricoValorCotas.objects.filter(fundo_investimento=fundo).exists():
        historico_mais_recente = HistoricoValorCotas.objects.filter(fundo_investimento=fundo).order_by('-data')[0]
        fundo.data_valor_cota = historico_mais_recente.data
        fundo.valor_cota = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(historico_mais_recente.valor_cota))
    else:
        fundo.data_valor_cota = None
        fundo.valor_cota = None
        
    # Prazo
    if fundo.tipo_prazo == 'C':
        fundo.tipo_prazo = 'Curto'
    elif fundo.tipo_prazo == 'L':
        fundo.tipo_prazo = 'Longo'
        
    data_final = datetime.date.today()
    historico = HistoricoValorCotas.objects.filter(fundo_investimento=fundo, data__gte=data_final.replace(year=data_final.year-1)).order_by('-data')
    for registro in historico:
        registro.valor_cota = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(registro.valor_cota))
    # Pegar datas inicial e final do historico
    if len(historico):
        historico_data_inicial = historico[len(historico)-1].data
        historico_data_final = historico[0].data
    else:
        historico_data_inicial = datetime.date.today()
        historico_data_final = datetime.date.today()
    
    dados = {'total_operacoes': 0, 'qtd_cotas_atual': Decimal(0), 'total_atual': Decimal(0), 'total_lucro': Decimal(0), 'lucro_percentual': Decimal(0)}
    if request.user.is_authenticated():
        investidor = request.user.investidor
        
        # TODO Considerar vendas parciais de titulos
        dados['total_operacoes'] = OperacaoFundoInvestimento.objects.filter(fundo_investimento=fundo, investidor=investidor).count()
        dados['qtd_cotas_atual'] = calcular_qtd_cotas_ate_dia_por_fundo(investidor, id_fundo)
        dados['total_atual'] = dados['qtd_cotas_atual'] * fundo.valor_cota if fundo.valor_cota else Decimal(0)
#         preco_medio = (OperacaoFundoInvestimento.objects.filter(fundo_investimento=fundo, investidor=investidor, tipo_operacao='C').annotate(valor_investido=F('quantidade') * F('preco_unitario')) \
#             .aggregate(total_investido=Sum('valor_investido'))['total_investido'] or Decimal(0)) / (OperacaoTitulo.objects.filter(titulo=titulo, investidor=investidor, tipo_operacao='C') \
#             .aggregate(total_titulos=Sum('quantidade'))['total_titulos'] or 1)
        preco_medio = Decimal(1)
        dados['total_lucro'] = dados['total_atual'] - dados['qtd_cotas_atual'] * preco_medio
        dados['lucro_percentual'] = (fundo.valor_cota - preco_medio) / (preco_medio or 1) if dados['qtd_cotas_atual'] > 0 else 0    
    
    return TemplateResponse(request, 'fundo_investimento/detalhar_fundo_investimento.html', {'fundo': fundo, 'dados': dados, 'historico': historico, 'historico_data_inicial': historico_data_inicial,
                                                                 'historico_data_final': historico_data_final})

@login_required
@adiciona_titulo_descricao('Editar operação em Fundo de Investimento', 'Alterar valores de uma operação de compra/venda em Fundo de Investimento')
def editar_operacao_fundo_investimento(request, id_operacao):
    investidor = request.user.investidor
    
    operacao_fundo_investimento = OperacaoFundoInvestimento.objects.get(pk=id_operacao)
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
            
            for erro in [erro for erro in form_operacao_fundo_investimento.non_field_errors()]:
                messages.error(request, erro)
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
    
    # Preparar nome de fundo selecionado
    if request.POST.get('fundo_investimento', -1) != -1:
        fundo_selecionado = FundoInvestimento.objects.get(id=request.POST['fundo_investimento'])
    else:
        fundo_selecionado = operacao_fundo_investimento.fundo_investimento.nome
    return TemplateResponse(request, 'fundo_investimento/editar_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, 'formset_divisao': formset_divisao, \
                                                                                             'varias_divisoes': varias_divisoes, 'fundo_selecionado': fundo_selecionado})  

@adiciona_titulo_descricao('Histórico de Fundos de Investimento', 'Histórico de operações de compra/venda em Fundos de Investimento')
def historico(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'fundo_investimento/historico.html', {'dados': {}, 'graf_investido_total': list(), 'graf_patrimonio': list()})
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data') 
    # Se investidor não tiver operações, retornar vazio
    if not operacoes:
        return TemplateResponse(request, 'fundo_investimento/historico.html', {'dados': {}, 'graf_investido_total': list(), 'graf_patrimonio': list()})
    # Prepara o campo valor atual
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
        else:
            operacao.tipo = 'Venda'
            
    
    total_investido = 0
    total_patrimonio = 0
    # Guarda quantidade de cotas
    fundos_investimento = {}
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    # Adicionar primeira data com valor 0
    graf_investido_total = list()
    graf_patrimonio = list()

    for operacao in operacoes:   
        total_patrimonio = 0  
        
        if operacao.fundo_investimento not in fundos_investimento.keys():
            fundos_investimento[operacao.fundo_investimento] = operacao.fundo_investimento
            fundos_investimento[operacao.fundo_investimento].qtd_cotas = 0
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            total_investido += operacao.valor
            fundos_investimento[operacao.fundo_investimento].qtd_cotas += operacao.quantidade
                
        elif operacao.tipo_operacao == 'V':
            total_investido -= operacao.valor
            fundos_investimento[operacao.fundo_investimento].qtd_cotas -= operacao.quantidade
        
        for fundo in fundos_investimento:
            if HistoricoValorCotas.objects.filter(fundo_investimento=fundo, data=operacao.data).exists():
                total_patrimonio += (fundo.qtd_cotas * HistoricoValorCotas.objects.get(fundo_investimento=fundo, data=operacao.data).valor_cota)
            else:
                total_patrimonio += ((operacao.valor / operacao.quantidade) * fundo.qtd_cotas)
            
        # Formatar data para inserir nos gráficos
        data_formatada = str(calendar.timegm(operacao.data.timetuple()) * 1000)    
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_investido_total) > 0 and graf_investido_total[-1][0] == data_formatada:
            graf_investido_total[len(graf_investido_total)-1][1] = float(total_investido)
        else:
            graf_investido_total += [[data_formatada, float(total_investido)]]
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
            graf_patrimonio[len(graf_patrimonio)-1][1] = float(total_patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(total_patrimonio)]]
    
    # Adicionar data atual, caso não tenha sido adicionada ainda
    if not operacoes.filter(data=datetime.date.today()).exists():
        # Formatar data para inserir nos gráficos
        data_formatada = str(calendar.timegm(datetime.date.today().timetuple()) * 1000)    
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_investido_total) > 0 and graf_investido_total[-1][0] == data_formatada:
            graf_investido_total[len(graf_investido_total)-1][1] = float(total_investido)
        else:
            graf_investido_total += [[data_formatada, float(total_investido)]]
     
        total_patrimonio = 0  
        # Calcular patrimônio atual
        for fundo in fundos_investimento:
            fundo.data_ultima_operacao = operacoes.filter(fundo_investimento=fundo).order_by('-data')[0].data
            if HistoricoValorCotas.objects.filter(fundo_investimento=fundo, data__gte=fundo.data_ultima_operacao).exists():
                total_patrimonio += (fundo.qtd_cotas * HistoricoValorCotas.objects.filter(fundo_investimento=fundo, data__gt=fundo.data_ultima_operacao).order_by('-data')[0].valor_cota)
            else:
                total_patrimonio += (operacoes.filter(fundo_investimento=fundo).order_by('-data')[0].valor_cota() * fundo.qtd_cotas)
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
            graf_patrimonio[len(graf_patrimonio)-1][1] = float(total_patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(total_patrimonio)]]
    
    dados = {}
    dados['total_investido'] = total_investido
    dados['patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio - total_investido
    dados['lucro_percentual'] = (total_patrimonio - total_investido) / total_investido * 100
    
    return TemplateResponse(request, 'fundo_investimento/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_investido_total': graf_investido_total, 'graf_patrimonio': graf_patrimonio})
    

@login_required
@adiciona_titulo_descricao('Inserir operação em fundo de investimento', 'Inserir registro de operação de compra/venda em fundo de investimento')
def inserir_operacao_fundo_investimento(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoFundoInvestimentoFormSet = inlineformset_factory(OperacaoFundoInvestimento, DivisaoOperacaoFundoInvestimento, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoFundoInvestimentoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(request.POST, investidor=investidor)
        formset_divisao = DivisaoFundoInvestimentoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar Fundo de Investimento
        if form_operacao_fundo_investimento.is_valid():
            operacao_fundo_investimento = form_operacao_fundo_investimento.save(commit=False)
            operacao_fundo_investimento.investidor = investidor
            
            # Testar se várias divisões
            if varias_divisoes:
                formset_divisao = DivisaoFundoInvestimentoFormSet(request.POST, instance=operacao_fundo_investimento, investidor=investidor)
                if formset_divisao.is_valid():
                    try:
                        with transaction.atomic():
                            operacao_fundo_investimento.save()
                            formset_divisao.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('fundo_investimento:historico_fundo_investimento'))
                    except:
                        messages.error(request, 'Houve um erro ao inserir a operação')
                        if settings.ENV == 'DEV':
                            raise
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro ao gerar operação em fundo de investimento com várias divisões', traceback.format_exc().decode('utf-8'))
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
            else:
                try:
                    with transaction.atomic():
                        operacao_fundo_investimento.save()
                        divisao_operacao = DivisaoOperacaoFundoInvestimento(operacao=operacao_fundo_investimento, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_fundo_investimento.quantidade)
                        divisao_operacao.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('fundo_investimento:historico_fundo_investimento'))
                except:
                    messages.error(request, 'Houve um erro ao inserir a operação')
                    if settings.ENV == 'DEV':
                        raise
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro ao gerar operação em fundo de investimento com uma divisão', traceback.format_exc().decode('utf-8'))
            
        for erro in [erro for erro in form_operacao_fundo_investimento.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_operacao_fundo_investimento = OperacaoFundoInvestimentoForm(investidor=investidor)
        formset_divisao = DivisaoFundoInvestimentoFormSet(investidor=investidor)
    
    if request.POST.get('fundo_investimento', -1) != -1:
        fundo_selecionado = FundoInvestimento.objects.get(id=request.POST['fundo_investimento'])
    else:
        fundo_selecionado = ''
    return TemplateResponse(request, 'fundo_investimento/inserir_operacao_fundo_investimento.html', {'form_operacao_fundo_investimento': form_operacao_fundo_investimento, \
                                                                                              'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes, 'fundo_selecionado': fundo_selecionado})

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
        # Prazo
        if fundo.tipo_prazo == 'C':
            fundo.tipo_prazo = 'Curto'
        elif fundo.tipo_prazo == 'L':
            fundo.tipo_prazo = 'Longo'

    return TemplateResponse(request, 'fundo_investimento/listar_fundo_investimento.html', {'fundos_investimento': fundos_investimento, 'filtro': filtro})

def listar_fundos_por_nome(request):
    nome_fundo = request.GET.get('nome_fundo', '')
    # Remover caracteres estranhos da string
    nome_fundo = re.sub('[^\w\d\. -]', '', nome_fundo)
    if len(nome_fundo) == 0:
        return HttpResponse(json.dumps({'sucesso': False, 'erro':'Nome do fundo deve contar pelo menos um caractere'}), content_type = "application/json")  
    # Verificar pagina para paginação
    try:
        pagina = int(request.GET.get('pagina', 1))
    except:
        pagina = 1
    
    # Buscar fundos
    fundos = [{'id': fundo['id'], 'text': fundo['nome']} for fundo in FundoInvestimento.objects.filter(nome__icontains=nome_fundo).values('id', 'nome').order_by('nome')]
    # Paginar fundos
    paginador_fundos = Paginator(fundos, 30)
    if pagina > paginador_fundos.num_pages:
        pagina = paginador_fundos.num_pages
    
    return HttpResponse(json.dumps({'sucesso': True, 'dados': paginador_fundos.page(pagina).object_list, 'total_count': paginador_fundos.count}), content_type = "application/json")   

def listar_historico_fundo_investimento(request, id_fundo):
    # Converte datas e realiza validação do formato
    try:
        data_inicial = datetime.datetime.strptime(request.GET.get('dataInicial', ''), '%d/%m/%Y')
    except ValueError:
        return HttpResponse(json.dumps({'sucesso': False, 'erro':'Data inicial inválida'}), content_type = "application/json")  
    try:
        data_final = datetime.datetime.strptime(request.GET.get('dataFinal', ''), '%d/%m/%Y')
    except ValueError:
        return HttpResponse(json.dumps({'sucesso': False, 'erro':'Data final inválida'}), content_type = "application/json")  
    # Pega apenas a parte relacionada a data do datetime
    data_inicial = data_inicial.date()
    data_final = data_final.date()
    if data_final < data_inicial:
        return HttpResponse(json.dumps({'sucesso': False, 'erro':'Data final deve ser maior ou igual a data inicial'}), content_type = "application/json")  
    if data_final > data_inicial.replace(year=data_inicial.year+1):
        return HttpResponse(json.dumps({'sucesso': False, 'erro':'O período limite para a escolha é de 1 ano'}), content_type = "application/json")  
    # Retorno OK
    historico = HistoricoValorCotas.objects.filter(data__range=[data_inicial, data_final], fundo_investimento__id=id_fundo)
    for registro in historico:
        registro.valor_cota = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(registro.valor_cota))
    return HttpResponse(json.dumps({'sucesso': True, 'dados': render_to_string('fundo_investimento/utils/listar_historico_fundo_investimento.html', {'historico': historico})}), content_type = "application/json")   

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
        if operacao.fundo_investimento not in fundos.keys():
            fundos[operacao.fundo_investimento] = operacao.fundo_investimento
            fundos[operacao.fundo_investimento].quantidade = 0
        if operacao.tipo_operacao == 'C':
            fundos[operacao.fundo_investimento].quantidade += operacao.quantidade
        else:
            fundos[operacao.fundo_investimento].quantidade -= operacao.quantidade
    
    fundos = [fundo for fundo in fundos.values() if fundo.quantidade > 0]
    
    # Totais da tabela do painel
    total_atual = 0    
    total_ir = 0
    total_iof = 0
    
    for fundo in fundos:
        fundo.data_atual = max(HistoricoValorCotas.objects.filter(fundo_investimento=fundo).order_by('-data')[0].data, OperacaoFundoInvestimento.objects.filter(investidor=investidor, fundo_investimento=fundo) \
                               .order_by('-data')[0].data)
        fundo.valor_cota_atual = fundo.valor_no_dia(investidor, fundo.data_atual)
        fundo.total_atual = fundo.valor_cota_atual * fundo.quantidade
        fundo.iof = Decimal(0)
        fundo.imposto_renda = Decimal(0)        
#         fundo.preco_medio = sum([operacao.valor for operacao in operacoes.filter(fundo_investimento=fundo)]) \
#             / sum([operacao.quantidade for operacao in operacoes.filter(fundo_investimento=fundo)])
        # Verificar IOF e IR nas operações 
        for operacao in operacoes.filter(fundo_investimento=fundo):
            valorizacao = fundo.valor_cota_atual - operacao.valor_cota()
            if valorizacao > 0:
                qtd_dias = (datetime.date.today() - operacao.data).days
        #         print qtd_dias, calcular_iof_regressivo(qtd_dias)
                # IOF
                operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * operacao.valor * valorizacao
                fundo.iof += operacao.iof
                # IR
                if qtd_dias <= 180:
                    fundo.imposto_renda += Decimal(0.225) * (operacao.valor * valorizacao - operacao.iof)
                elif qtd_dias <= 360:
                    fundo.imposto_renda += Decimal(0.2) * (operacao.valor * valorizacao - operacao.iof)
                elif qtd_dias <= 720:
                    fundo.imposto_renda += Decimal(0.175) * (operacao.valor * valorizacao - operacao.iof)
                else: 
                    fundo.imposto_renda += Decimal(0.15) * (operacao.valor * valorizacao - operacao.iof)
            else:
                # IR
                fundo.imposto_renda += valorizacao
        
        # Zerar valor negativo
        fundo.imposto_renda = max(Decimal(0), fundo.imposto_renda)
                
        total_atual += fundo.total_atual    
        total_ir += fundo.imposto_renda
        total_iof += fundo.iof
    
    # Popular dados
    dados = {}
    dados['total_atual'] = total_atual
    dados['total_ir'] = total_ir
    dados['total_iof'] = total_iof
    
    return TemplateResponse(request, 'fundo_investimento/painel.html', {'fundos': fundos, 'dados': dados})

@adiciona_titulo_descricao('Sobre Fundos de Investimento', 'Detalha o que são Fundos de Investimento')
def sobre(request):
    # Calcular total atual do investidor
    if request.user.is_authenticated():
        total_atual = sum(calcular_valor_fundos_investimento_ate_dia(request.user.investidor).values())
    else:
        total_atual = 0
    return TemplateResponse(request, 'fundo_investimento/sobre.html', {'total_atual': total_atual})

def verificar_historico_fundo_na_data(request):
    try:
        # Tenta pegar o id do fundo como inteiro
        id_fundo = request.GET['fundo']
    except:
        return HttpResponse(json.dumps({'sucesso': False, 'erro':'Valor inválido para fundo de investimento'}), content_type = "application/json")  
    try:
        # Tenta pegar data no formato dd/mm/YYYY
        data = datetime.datetime.strptime(request.GET['data'], '%d/%m/%Y')
    except:
        return HttpResponse(json.dumps({'sucesso': False, 'erro':'Data inválida'}), content_type = "application/json")  
    
    # Buscar histórico
    if HistoricoValorCotas.objects.filter(fundo_investimento__id=id_fundo, data=data).exists():
        historico_valor = str(formatar_zeros_a_direita_apos_2_casas_decimais(HistoricoValorCotas.objects.get(fundo_investimento__id=id_fundo, data=data).valor_cota))
    else:
        historico_valor = '0.00'
    
    return HttpResponse(json.dumps({'sucesso': True, 'valor': historico_valor}), content_type = "application/json")   