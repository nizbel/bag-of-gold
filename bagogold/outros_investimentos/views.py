# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoInvestimentoFormSet
from bagogold.bagogold.models.divisoes import DivisaoInvestimento, Divisao
from bagogold.bagogold.utils.misc import converter_date_para_utc
from bagogold.outros_investimentos.forms import InvestimentoForm, RendimentoForm, \
    AmortizacaoForm, EncerramentoForm
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
from itertools import chain
from operator import attrgetter
import calendar
import datetime
import traceback

@login_required
@adiciona_titulo_descricao('Detalhar investimento', 'Detalhar investimento, incluindo histórico de rendimentos e '
                                                'amortizações, além de dados da posição do investidor')
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
    investimento.total_investido = investimento.quantidade + investimento.taxa
    investimento.total_amortizacoes = sum(investimento.amortizacao_set.filter(data__lte=datetime.date.today()).values_list('valor', flat=True))
    investimento.saldo_atual = investimento.quantidade - investimento.total_amortizacoes
    investimento.total_rendimentos = sum(investimento.rendimento_set.filter(data__lte=datetime.date.today()).values_list('valor', flat=True))
#     cdb_rdb.total_ir = Decimal(0)
#     cdb_rdb.total_iof = Decimal(0)
    investimento.lucro = investimento.total_amortizacoes + investimento.total_rendimentos - investimento.total_investido
    investimento.lucro_percentual = investimento.lucro / 1 if investimento.total_investido == 0 else 100 * Decimal(investimento.lucro) / Decimal(investimento.total_investido)
    
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

@login_required
@adiciona_titulo_descricao('Editar amortização de um investimento', 'Editar registro de amortização de um investimento')
def editar_amortizacao(request, id_amortizacao):
    investidor = request.user.investidor
    amortizacao = get_object_or_404(Amortizacao, id=id_amortizacao)
     
    if amortizacao.investimento.investidor != investidor:
        raise PermissionDenied
     
    if request.method == 'POST':
        if request.POST.get("save"):
            form_amortizacao = AmortizacaoForm(request.POST, instance=amortizacao, investimento=amortizacao.investimento, \
                                                                         investidor=investidor)
            if form_amortizacao.is_valid():
                amortizacao.save(force_update=True)
                messages.success(request, 'Amortização editada com sucesso')
                return HttpResponseRedirect(reverse('outros_investimentos:detalhar_investimento', kwargs={'id_investimento': amortizacao.investimento.id}))
                 
            for erro in [erro for erro in form_amortizacao.non_field_errors()]:
                messages.error(request, erro)
                 
        elif request.POST.get("delete"):
            # Pegar investimento para o redirecionamento no caso de exclusão
            investimento = amortizacao.investimento
            amortizacao.delete()
            messages.success(request, 'Amortização excluída com sucesso')
            return HttpResponseRedirect(reverse('outros_investimentos:detalhar_investimento', kwargs={'id_investimento': investimento.id}))
  
    else:
        form_amortizacao = AmortizacaoForm(instance=amortizacao, investimento=amortizacao.investimento, investidor=investidor)
             
    return TemplateResponse(request, 'outros_investimentos/editar_amortizacao.html', {'form_amortizacao': form_amortizacao}) 

@login_required
@adiciona_titulo_descricao('Editar investimento', 'Alterar valores de um investimento')
def editar_investimento(request, id_investimento):
    investidor = request.user.investidor
    
    investimento = Investimento.objects.get(pk=id_investimento)
    # Verifica se o investimento é do investidor, senão, jogar erro de permissão
    if investimento.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(Investimento, DivisaoInvestimento, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoInvestimentoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_outros_invest = InvestimentoForm(request.POST, instance=investimento, investidor=investidor)
            formset_divisao = DivisaoFormSet(request.POST, instance=investimento, investidor=investidor) if varias_divisoes else None
                
            if form_outros_invest.is_valid():
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        try:
                            with transaction.atomic():
                                investimento.save()
                                # Caso o valor para a taxa da moeda comprada/vendida seja maior que 0, criar ou editar taxa
                                if form_outros_invest.cleaned_data['taxa'] > 0:
                                    InvestimentoTaxa.objects.update_or_create(investimento=investimento, 
                                                                              defaults={'valor': form_outros_invest.cleaned_data['taxa']})
                                # Caso contrário, apagar taxa para a moeda, caso exista
                                elif InvestimentoTaxa.objects.filter(investimento=investimento).exists():
                                    InvestimentoTaxa.objects.get(investimento=investimento).delete()
                                
                                formset_divisao.save()
                                messages.success(request, 'Investimento editado com sucesso')
                                return HttpResponseRedirect(reverse('outros_investimentos:historico_outros_invest'))
                        except:
                            messages.error(request, 'Houve um erro ao editar o investimento')
                            if settings.ENV == 'DEV':
                                raise
                            elif settings.ENV == 'PROD':
                                mail_admins(u'Erro ao editar investimento com várias divisões', traceback.format_exc().decode('utf-8'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                        
                else:
                    try:
                        with transaction.atomic():
                            investimento.save()
                            # Caso o valor para a taxa da moeda comprada/vendida seja maior que 0, criar ou editar taxa
                            if form_outros_invest.cleaned_data['taxa'] > 0:
                                InvestimentoTaxa.objects.update_or_create(investimento=investimento, 
                                                                          defaults={'valor': form_outros_invest.cleaned_data['taxa']})
                            # Caso contrário, apagar taxa para a moeda, caso exista
                            elif InvestimentoTaxa.objects.filter(investimento=investimento).exists():
                                InvestimentoTaxa.objects.get(investimento=investimento).delete()
                            divisao_operacao = DivisaoInvestimento.objects.get(divisao=investidor.divisaoprincipal.divisao, investimento=investimento)
                            divisao_operacao.quantidade = investimento.quantidade
                            divisao_operacao.save()
                            messages.success(request, 'Investimento editado com sucesso')
                            return HttpResponseRedirect(reverse('outros_investimentos:historico_outros_invest'))
                    except:
                        messages.error(request, 'Houve um erro ao editar o investimento')
                        if settings.ENV == 'DEV':
                            raise
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro ao editar investimento com uma divisão', traceback.format_exc().decode('utf-8'))
                
            for erro in [erro for erro in form_outros_invest.non_field_errors()]:
                messages.error(request, erro)
#                         print '%s %s'  % (divisao_criptomoeda.quantidade, divisao_criptomoeda.divisao)
                
        elif request.POST.get("delete"):
            # Verifica se, em caso de compra, a quantidade de cotas do investidor não fica negativa
            if Rendimento.objects.filter(investimento=investimento).exists() or Amortizacao.objects.filter(investimento=investimento).exists():
                messages.error(request, 'Investimento não pode ser apagado pois já possui rendimentos e/ou amortizações cadastrados')
            else:
                divisao_investimento = DivisaoInvestimento.objects.filter(investimento=investimento)
                for divisao in divisao_investimento:
                    divisao.delete()
                investimento.delete()
                messages.success(request, 'Investimento apagado com sucesso')
                return HttpResponseRedirect(reverse('outros_investimentos:historico_outros_invest'))
 
    else:
        if InvestimentoTaxa.objects.filter(investimento=investimento).exists():
            taxa = InvestimentoTaxa.objects.get(investimento=investimento).valor
        else:
            taxa = 0
        form_outros_invest = InvestimentoForm(instance=investimento, investidor=investidor, initial={'taxa': taxa})
        formset_divisao = DivisaoFormSet(instance=investimento, investidor=investidor)
        
    return TemplateResponse(request, 'outros_investimentos/editar_investimento.html', {'form_outros_invest': form_outros_invest, 'formset_divisao': formset_divisao, \
                                                                                             'varias_divisoes': varias_divisoes}) 

@login_required
@adiciona_titulo_descricao('Editar rendimento de um investimento', 'Editar registro de rendimento de um investimento')
def editar_rendimento(request, id_rendimento):
    investidor = request.user.investidor
    rendimento = get_object_or_404(Rendimento, id=id_rendimento)
     
    if rendimento.investimento.investidor != investidor:
        raise PermissionDenied
     
    if request.method == 'POST':
        if request.POST.get("save"):
            form_rendimento = RendimentoForm(request.POST, instance=rendimento, investimento=rendimento.investimento, \
                                                                         investidor=investidor)
            if form_rendimento.is_valid():
                rendimento.save(force_update=True)
                messages.success(request, 'Rendimento editado com sucesso')
                return HttpResponseRedirect(reverse('outros_investimentos:detalhar_investimento', kwargs={'id_investimento': rendimento.investimento.id}))
                 
            for erro in [erro for erro in form_rendimento.non_field_errors()]:
                messages.error(request, erro)
                 
        elif request.POST.get("delete"):
            # Pegar investimento para o redirecionamento no caso de exclusão
            investimento = rendimento.investimento
            rendimento.delete()
            messages.success(request, 'Rendimento excluído com sucesso')
            return HttpResponseRedirect(reverse('outros_investimentos:detalhar_investimento', kwargs={'id_investimento': investimento.id}))
  
    else:
        form_rendimento = RendimentoForm(instance=rendimento, investimento=rendimento.investimento, investidor=investidor)
             
    return TemplateResponse(request, 'outros_investimentos/editar_rendimento.html', {'form_rendimento': form_rendimento}) 

@login_required
@adiciona_titulo_descricao('Encerrar investimento', 'Alterar data de encerramento de um investimento')
def encerrar_investimento(request, id_investimento):
    investidor = request.user.investidor
    
    investimento = Investimento.objects.get(pk=id_investimento)
    # Verifica se o investimento é do investidor, senão, jogar erro de permissão
    if investimento.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_encerramento = EncerramentoForm(request.POST, instance=investimento, investidor=investidor)
                
            if form_encerramento.is_valid():
                try:
                    with transaction.atomic():
                        investimento.save()
                        # Caso o valor para a taxa da moeda comprada/vendida seja maior que 0, criar ou editar taxa
                        if form_encerramento.cleaned_data['amortizacao'] > 0:
                            Amortizacao.objects.update_or_create(investimento=investimento, data=form_encerramento.cleaned_data['data_encerramento'],
                                                                      defaults={'valor': form_encerramento.cleaned_data['amortizacao']})
                        # Caso contrário, apagar taxa para a moeda, caso exista
                        elif Amortizacao.objects.filter(investimento=investimento, data=form_encerramento.cleaned_data['data_encerramento']).exists():
                            Amortizacao.objects.get(investimento=investimento, data=form_encerramento.cleaned_data['data_encerramento']).delete()
                        messages.success(request, 'Data de encerramento editada com sucesso')
                        return HttpResponseRedirect(reverse('outros_investimentos:detalhar_investimento', kwargs={'id_investimento': investimento.id}))
                except:
                    messages.error(request, 'Houve um erro ao editar a data de encerramento')
                    if settings.ENV == 'DEV':
                        raise
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro ao editar data de encerramento para investimento de id %s' % (investimento.id), traceback.format_exc().decode('utf-8'))
                
            for erro in [erro for erro in form_encerramento.non_field_errors()]:
                messages.error(request, erro)
#                         print '%s %s'  % (divisao_criptomoeda.quantidade, divisao_criptomoeda.divisao)
        
        # Delete apaga data de encerramento
        elif request.POST.get("delete"):
            investimento.data_encerramento = None
            investimento.save()
            messages.success(request, 'Data de encerramento editada com sucesso')
            return HttpResponseRedirect(reverse('outros_investimentos:detalhar_investimento', kwargs={'id_investimento': investimento.id}))
 
    else:
        if investimento.data_encerramento and Amortizacao.objects.filter(investimento=investimento, data=investimento.data_encerramento).exists():
            amortizacao = Amortizacao.objects.get(investimento=investimento, data=investimento.data_encerramento).valor
        else:
            amortizacao = 0
        form_encerramento = EncerramentoForm(instance=investimento, investidor=investidor, initial={'amortizacao': amortizacao})
        
    return TemplateResponse(request, 'outros_investimentos/encerrar_investimento.html', {'form_encerramento': form_encerramento}) 

@adiciona_titulo_descricao('Histórico de outros investimentos', 'Histórico de movimentações em outros tipos de investimento')
def historico(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    # Usada para guardar eventos de encerramento
    class Encerramento(object):
        def __init__(self, investimento):
            self.investimento = investimento
            self.data = investimento.data_encerramento
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'outros_investimentos/historico.html', {'dados': {}, 'graf_rendimentos': list(), 'graf_investido_total': list(), 
                                                                                 'graf_amortizacoes': list(), 'lista_eventos': list()})
    
    investimentos = Investimento.objects.filter(investidor=investidor).order_by('data')
    
    rendimentos = Rendimento.objects.filter(investimento__investidor=investidor).order_by('data')
    
    amortizacoes = Amortizacao.objects.filter(investimento__investidor=investidor).order_by('data')
    
    if not investimentos:
        return TemplateResponse(request, 'outros_investimentos/historico.html', {'dados': {}, 'graf_rendimentos': list(), 'graf_investido_total': list(),
                                                                                 'graf_amortizacoes': list(), 'lista_eventos': list()})

    # TODO add encerramentos
    encerramentos = [Encerramento(investimento) for investimento in investimentos.filter(data_encerramento__isnull=False)]

    # Juntar todos os eventos
    lista_eventos = sorted(chain(investimentos, rendimentos, amortizacoes, encerramentos), key=attrgetter('data'))
        
    dados = {}
    
    qtd_investimentos = {}
    
    graf_rendimentos = list()
    graf_investido_total = list()
    graf_amortizacoes = list()
    
    total_rendimentos = 0
    total_investido = 0
    total_amortizado = 0
    
    for evento in lista_eventos:
        if isinstance(evento, Investimento):
            evento.tipo_evento = u'Investimento'
            evento.investimento = evento
            
            qtd_investimentos[evento.id] = Object()
            qtd_investimentos[evento.id].investido = evento.quantidade + evento.taxa
            qtd_investimentos[evento.id].amortizado = 0
            qtd_investimentos[evento.id].rendimentos = 0
        
        elif isinstance(evento, Rendimento):
            evento.tipo_evento = u'Rendimento'
            evento.quantidade = evento.valor
            
            qtd_investimentos[evento.investimento.id].rendimentos += evento.quantidade
            
        elif isinstance(evento, Amortizacao):
            evento.tipo_evento = u'Amortização'
            evento.quantidade = evento.valor
            
            qtd_investimentos[evento.investimento.id].amortizado += evento.quantidade
            
        else:
            evento.tipo_evento = u'Encerramento'
            
#             del qtd_investimentos[evento.investimento.id]
            
        total_rendimentos = sum([investimento.rendimentos for investimento in qtd_investimentos.values()])
        total_investido = sum([investimento.investido for investimento in qtd_investimentos.values()])
        total_amortizado = sum([investimento.amortizado for investimento in qtd_investimentos.values()])
    
        # Formatar data para inserir nos gráficos
        data_formatada = str(calendar.timegm(converter_date_para_utc(evento.data).timetuple()) * 1000)    
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_investido_total) > 0 and graf_investido_total[-1][0] == data_formatada:
            graf_investido_total[len(graf_investido_total)-1][1] = float(total_investido)
        else:
            graf_investido_total += [[data_formatada, float(total_investido)]]
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_rendimentos) > 0 and graf_rendimentos[-1][0] == data_formatada:
            graf_rendimentos[len(graf_rendimentos)-1][1] = float(total_rendimentos)
        else:
            graf_rendimentos += [[data_formatada, float(total_rendimentos)]]
            
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_amortizacoes) > 0 and graf_amortizacoes[-1][0] == data_formatada:
            graf_amortizacoes[len(graf_amortizacoes)-1][1] = float(total_amortizado)
        else:
            graf_amortizacoes += [[data_formatada, float(total_amortizado)]]
    
        
    total_rendimentos = sum([investimento.rendimentos for investimento in qtd_investimentos.values()])
    total_investido = sum([investimento.investido for investimento in qtd_investimentos.values()])
    total_amortizado = sum([investimento.amortizado for investimento in qtd_investimentos.values()])
    
    # Adicionar data atual se não houver sido adicionada ainda
    if lista_eventos and lista_eventos[-1].data < datetime.date.today():
        # Formatar data para inserir nos gráficos
        data_formatada = str(calendar.timegm(converter_date_para_utc(datetime.date.today()).timetuple()) * 1000)    
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_investido_total) > 0 and graf_investido_total[-1][0] == data_formatada:
            graf_investido_total[len(graf_investido_total)-1][1] = float(total_investido)
        else:
            graf_investido_total += [[data_formatada, float(total_investido)]]
        
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_rendimentos) > 0 and graf_rendimentos[-1][0] == data_formatada:
            graf_rendimentos[len(graf_rendimentos)-1][1] = float(total_rendimentos)
        else:
            graf_rendimentos += [[data_formatada, float(total_rendimentos)]]
            
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_amortizacoes) > 0 and graf_amortizacoes[-1][0] == data_formatada:
            graf_amortizacoes[len(graf_amortizacoes)-1][1] = float(total_amortizado)
        else:
            graf_amortizacoes += [[data_formatada, float(total_amortizado)]]
    
    dados['total_investido'] = total_investido
    dados['total_rendimentos'] = total_rendimentos
    dados['total_amortizado'] = total_amortizado
    dados['lucro'] = total_rendimentos + total_amortizado - total_investido
    dados['lucro_percentual'] = dados['lucro'] / 1 if total_investido == 0 else dados['lucro'] / dados['total_investido'] * 100
    
    return TemplateResponse(request, 'outros_investimentos/historico.html', {'dados': dados, 'graf_rendimentos': graf_rendimentos, 
                                                                             'graf_investido_total': graf_investido_total,
                                                                             'graf_amortizacoes': graf_amortizacoes,
                                                                             'lista_eventos': lista_eventos})

@login_required
@adiciona_titulo_descricao('Inserir amortização para um investimento', 'Inserir registro de amortização '
                                                                    'ao histórico de um investimento')
def inserir_amortizacao(request, investimento_id):
    investidor = request.user.investidor
    investimento = get_object_or_404(Investimento, id=investimento_id)
    
    if investimento.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form_amortizacao = AmortizacaoForm(request.POST, initial={'investimento': investimento.id}, investimento=investimento, investidor=investidor)
        if form_amortizacao.is_valid():
            amortizacao = form_amortizacao.save()
            messages.success(request, 'Amortização para %s incluída com sucesso' % amortizacao.investimento)
            return HttpResponseRedirect(reverse('outros_investimentos:detalhar_investimento', kwargs={'id_investimento': investimento.id}))
        
        for erro in [erro for erro in form_amortizacao.non_field_errors()]:
            messages.error(request, erro)
    else:
        form_amortizacao = AmortizacaoForm(initial={'investimento': investimento.id}, investimento=investimento, investidor=investidor)
            
    return TemplateResponse(request, 'outros_investimentos/inserir_amortizacao.html', {'form_amortizacao': form_amortizacao})

@login_required
@adiciona_titulo_descricao('Inserir investimento', 'Inserir registro de investimento')
def inserir_investimento(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(Investimento, DivisaoInvestimento, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoInvestimentoFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_outros_invest = InvestimentoForm(request.POST, investidor=investidor)
        formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar operação
        if form_outros_invest.is_valid():
            investimento = form_outros_invest.save(commit=False)
            investimento.investidor = investidor
                
            # Testar se várias divisões
            if varias_divisoes:
                formset_divisao = DivisaoFormSet(request.POST, instance=investimento, investidor=investidor)
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
                            mail_admins(u'Erro ao gerar investimento na seção outros investimentos, com várias divisões', traceback.format_exc().decode('utf-8'))
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
                        mail_admins(u'Erro ao gerar investimento na seção outros investimentos, com uma divisão', traceback.format_exc().decode('utf-8'))
            
        for erro in [erro for erro in form_outros_invest.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_outros_invest = InvestimentoForm(investidor=investidor)
        formset_divisao = DivisaoFormSet(investidor=investidor)
    
    return TemplateResponse(request, 'outros_investimentos/inserir_investimento.html', {'form_outros_invest': form_outros_invest, \
                                                                                              'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@login_required
@adiciona_titulo_descricao('Inserir rendimento para um investimento', 'Inserir registro de rendimento '
                                                                    'ao histórico de um investimento')
def inserir_rendimento(request, investimento_id):
    investidor = request.user.investidor
    investimento = get_object_or_404(Investimento, id=investimento_id)
    
    if investimento.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form_rendimento = RendimentoForm(request.POST, initial={'investimento': investimento.id}, investimento=investimento, investidor=investidor)
        if form_rendimento.is_valid():
            rendimento = form_rendimento.save()
            messages.success(request, 'Histórico de porcentagem de rendimento para %s alterado com sucesso' % rendimento.investimento)
            return HttpResponseRedirect(reverse('outros_investimentos:detalhar_investimento', kwargs={'id_investimento': investimento.id}))
        
        for erro in [erro for erro in form_rendimento.non_field_errors()]:
            messages.error(request, erro)
    else:
        form_rendimento = RendimentoForm(initial={'investimento': investimento.id}, investimento=investimento, investidor=investidor)
            
    return TemplateResponse(request, 'outros_investimentos/inserir_rendimento.html', {'form_rendimento': form_rendimento})

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
    
    investimentos = Investimento.objects.filter(investidor=investidor, data_encerramento__isnull=True)
    
    if not investimentos:
        return TemplateResponse(request, 'outros_investimentos/historico.html', {'dados': {}, 'investimentos': list()})
        
    dados = {}
    
    total_investido = 0
    total_taxas = 0
    total_rendimentos = 0
    total_amortizacoes = 0
    total_lucro = 0
    
    for investimento in investimentos:
        investimento.rendimentos = sum(investimento.rendimento_set.values_list('valor', flat=True))
        investimento.amortizacoes = sum(investimento.amortizacao_set.values_list('valor', flat=True))
        investimento.lucro = investimento.rendimentos + investimento.amortizacoes - investimento.quantidade - investimento.taxa
        
        total_investido += investimento.quantidade
        total_taxas += investimento.taxa
        total_rendimentos += investimento.rendimentos
        total_amortizacoes += investimento.amortizacoes
        total_lucro += investimento.lucro
        
    dados['total_atual'] = total_investido
    dados['total_taxa'] = total_taxas
    dados['total_rendimentos'] = total_rendimentos
    dados['total_amortizacoes'] = total_amortizacoes
    dados['total_lucro'] = total_lucro
    
    return TemplateResponse(request, 'outros_investimentos/painel.html', {'dados': dados, 'investimentos': investimentos})
    

@adiciona_titulo_descricao('', '')
def sobre(request):
    
    return TemplateResponse(request, 'outros_investimentos/sobre.html', {})