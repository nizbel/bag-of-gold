# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoCriptomoedaFormSet, \
    DivisaoTransferenciaCriptomoedaFormSet
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    Divisao, DivisaoTransferenciaCriptomoeda, DivisaoPrincipal
from bagogold.criptomoeda.forms import OperacaoCriptomoedaForm, \
    TransferenciaCriptomoedaForm, OperacaoCriptomoedaLoteForm, \
    TransferenciaCriptomoedaLoteForm
from bagogold.criptomoeda.models import Criptomoeda, OperacaoCriptomoeda, \
    OperacaoCriptomoedaMoeda, OperacaoCriptomoedaTaxa, TransferenciaCriptomoeda, \
    ValorDiarioCriptomoeda
from bagogold.criptomoeda.utils import calcular_qtd_moedas_ate_dia, \
    criar_operacoes_lote, criar_transferencias_lote
from bagogold.fundo_investimento.utils import \
    calcular_qtd_cotas_ate_dia_por_fundo
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from itertools import chain
from operator import attrgetter
import calendar
import datetime
import json
import re
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
                                    
                                formset_divisao.save()
                                messages.success(request, 'Operação editada com sucesso')
                                return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                        except:
                            messages.error(request, 'Houve um erro ao editar a operação')
                            if settings.ENV == 'DEV':
                                raise
                            elif settings.ENV == 'PROD':
                                mail_admins(u'Erro ao editar operação em criptomoeda com várias divisões', traceback.format_exc().decode('utf-8'))
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
                            mail_admins(u'Erro ao editar operação em criptomoeda com uma divisão', traceback.format_exc().decode('utf-8'))
                
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

@login_required
@adiciona_titulo_descricao('Editar transferência para criptomoedas', 'Alterar valores de uma transferência para criptomoedas')
def editar_transferencia(request, id_transferencia):
    investidor = request.user.investidor
    
    transferencia_criptomoeda = TransferenciaCriptomoeda.objects.get(pk=id_transferencia)
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if transferencia_criptomoeda.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(TransferenciaCriptomoeda, DivisaoTransferenciaCriptomoeda, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoTransferenciaCriptomoedaFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_transferencia_criptomoeda = TransferenciaCriptomoedaForm(request.POST, instance=transferencia_criptomoeda, investidor=investidor)
            formset_divisao = DivisaoFormSet(request.POST, instance=transferencia_criptomoeda, investidor=investidor) if varias_divisoes else None
                
            if form_transferencia_criptomoeda.is_valid():
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        try:
                            with transaction.atomic():
                                transferencia_criptomoeda.save()
                                formset_divisao.save()
                                messages.success(request, 'Transferência editada com sucesso')
                                return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                        except:
                            messages.error(request, 'Houve um erro ao editar a transferência')
                            if settings.ENV == 'DEV':
                                raise
                            elif settings.ENV == 'PROD':
                                mail_admins(u'Erro ao editar transferência para criptomoeda com várias divisões', traceback.format_exc().decode('utf-8'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                        
                else:
                    try:
                        with transaction.atomic():
                            transferencia_criptomoeda.save()
                            divisao_operacao = DivisaoOperacaoCriptomoeda.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=transferencia_criptomoeda)
                            divisao_operacao.quantidade = transferencia_criptomoeda.quantidade
                            divisao_operacao.save()
                            messages.success(request, 'Transferência editada com sucesso')
                            return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                    except:
                        messages.error(request, 'Houve um erro ao editar a transferência')
                        if settings.ENV == 'DEV':
                            raise
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro ao editar transferência para criptomoeda com uma divisão', traceback.format_exc().decode('utf-8'))
                
            for erro in [erro for erro in form_transferencia_criptomoeda.non_field_errors()]:
                messages.error(request, erro)
#                         print '%s %s'  % (divisao_criptomoeda.quantidade, divisao_criptomoeda.divisao)
                
        elif request.POST.get("delete"):
            # Verifica se, em caso de compra, a quantidade de cotas do investidor não fica negativa
            if transferencia_criptomoeda.tipo_operacao == 'C' and calcular_qtd_cotas_ate_dia_por_fundo(investidor, transferencia_criptomoeda.criptomoeda.id, datetime.date.today()) - transferencia_criptomoeda.quantidade < 0:
                messages.error(request, 'Operação de compra não pode ser apagada pois quantidade atual para o fundo %s seria negativa' % (transferencia_criptomoeda.criptomoeda))
            else:
                divisao_criptomoeda = DivisaoOperacaoCriptomoeda.objects.filter(operacao=transferencia_criptomoeda)
                for divisao in divisao_criptomoeda:
                    divisao.delete()
                transferencia_criptomoeda.delete()
                messages.success(request, 'Operação apagada com sucesso')
                return HttpResponseRedirect(reverse('td:historico_td'))
 
    else:
        form_transferencia_criptomoeda = TransferenciaCriptomoedaForm(instance=transferencia_criptomoeda, investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=transferencia_criptomoeda, investidor=investidor)
        
    return TemplateResponse(request, 'criptomoedas/editar_transferencia.html', {'form_transferencia_criptomoeda': form_transferencia_criptomoeda, 'formset_divisao': formset_divisao, \
                                                                                             'varias_divisoes': varias_divisoes})  
    

@adiciona_titulo_descricao('Histórico de Criptomoedas', 'Histórico de operações de compra/venda em Criptomoedas')
def historico(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': {}, 'movimentacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
    
    # Transferências do investidor
    transferencias = TransferenciaCriptomoeda.objects.filter(investidor=investidor, data__lte=datetime.date.today()).order_by('data')
        
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCriptomoeda.objects.filter(investidor=investidor, data__lte=datetime.date.today()).order_by('data', '-tipo_operacao') 
    
    # Juntar transferências e operações em uma lista
    lista_movimentacoes = sorted(chain(transferencias, operacoes), key=attrgetter('data'))
    # Se investidor não tiver operações, retornar vazio
    if not lista_movimentacoes:
        return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': {}, 'movimentacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
    
    # Gráficos
    graf_patrimonio = list()
    graf_investido_total = list()
    
    # Totais
    total_investido = 0
    
    moedas = {}
    
    for movimentacao in lista_movimentacoes:
        if isinstance(movimentacao, OperacaoCriptomoeda):
            if movimentacao.criptomoeda.ticker not in moedas.keys():
                moedas[movimentacao.criptomoeda.ticker] = Object()
                moedas[movimentacao.criptomoeda.ticker].preco_medio = 0
                moedas[movimentacao.criptomoeda.ticker].qtd = 0
                
            # Verifica se há taxa cadastrada
            movimentacao.taxa = movimentacao.taxa()
            
            if movimentacao.tipo_operacao == 'C':
                movimentacao.tipo = 'Compra'
                if movimentacao.taxa:
                    # Taxas externas à quantidade comprada
                    if movimentacao.taxa.moeda == movimentacao.criptomoeda:
                        movimentacao.preco_total = (movimentacao.quantidade + movimentacao.taxa.valor) * movimentacao.preco_unitario
                    elif movimentacao.taxa.moeda_utilizada() == movimentacao.moeda_utilizada():
                        movimentacao.preco_total = movimentacao.quantidade * movimentacao.preco_unitario + movimentacao.taxa.valor
                    else:
                        raise ValueError('Moeda utilizada na taxa é inválida')
                else:
                    movimentacao.preco_total = movimentacao.quantidade * movimentacao.preco_unitario
                # Movimentações em real contam como dinheiro investido
                if movimentacao.em_real():
                    moedas[movimentacao.criptomoeda.ticker].preco_medio = (moedas[movimentacao.criptomoeda.ticker].preco_medio * moedas[movimentacao.criptomoeda.ticker].qtd \
                                                                           + movimentacao.preco_total) / (movimentacao.quantidade + moedas[movimentacao.criptomoeda.ticker].qtd)
                else:
                    moedas[movimentacao.operacaocriptomoedamoeda.criptomoeda.ticker].qtd -= movimentacao.preco_total
                    moedas[movimentacao.criptomoeda.ticker].preco_medio = (moedas[movimentacao.criptomoeda.ticker].preco_medio * moedas[movimentacao.criptomoeda.ticker].qtd \
                                                                           + (movimentacao.preco_total * moedas[movimentacao.operacaocriptomoedamoeda.criptomoeda.ticker].preco_medio)) \
                                                                              / (movimentacao.quantidade + moedas[movimentacao.criptomoeda.ticker].qtd)
                
                moedas[movimentacao.criptomoeda.ticker].qtd += movimentacao.quantidade
            else:
                movimentacao.tipo = 'Venda'
                # Taxa entra como negativa na conta do valor total da operação
                if movimentacao.taxa:
                    # Taxas são inclusas na quantidade vendida
                    if movimentacao.taxa.moeda == movimentacao.criptomoeda:
                        movimentacao.preco_total = (movimentacao.quantidade - movimentacao.taxa.valor) * movimentacao.preco_unitario
                    elif movimentacao.taxa.moeda_utilizada() == movimentacao.moeda_utilizada():
                        movimentacao.preco_total = movimentacao.quantidade * movimentacao.preco_unitario - movimentacao.taxa.valor
                    else:
                        raise ValueError('Moeda utilizada na taxa é inválida')
                else:
                    movimentacao.preco_total = movimentacao.quantidade * movimentacao.preco_unitario
                
                # Alterar quantidade de moeda utilizada na operação
                if not movimentacao.em_real():
                    moedas[movimentacao.operacaocriptomoedamoeda.criptomoeda.ticker].preco_medio = (moedas[movimentacao.criptomoeda.ticker].preco_medio * movimentacao.quantidade \
                                                                           + (moedas[movimentacao.operacaocriptomoedamoeda.criptomoeda.ticker].preco_medio \
                                                                              * moedas[movimentacao.operacaocriptomoedamoeda.criptomoeda.ticker].qtd)) \
                                                                              / (movimentacao.preco_total + moedas[movimentacao.operacaocriptomoedamoeda.criptomoeda.ticker].qtd)
                    moedas[movimentacao.operacaocriptomoedamoeda.criptomoeda.ticker].qtd += movimentacao.preco_total
                    
                moedas[movimentacao.criptomoeda.ticker].qtd -= movimentacao.quantidade
        
        elif isinstance(movimentacao, TransferenciaCriptomoeda):
            if movimentacao.moeda and movimentacao.moeda.ticker not in moedas.keys():
                moedas[movimentacao.moeda.ticker] = Object()
                moedas[movimentacao.moeda.ticker].preco_medio = 0
                moedas[movimentacao.moeda.ticker].qtd = 0
                
            movimentacao.tipo = u'Transferência'
            if movimentacao.moeda:
                moedas[movimentacao.moeda.ticker].preco_medio = moedas[movimentacao.moeda.ticker].preco_medio * moedas[movimentacao.moeda.ticker].qtd \
                    / (moedas[movimentacao.moeda.ticker].qtd - movimentacao.taxa)
                moedas[movimentacao.moeda.ticker].qtd -= movimentacao.taxa
            movimentacao.preco_total = movimentacao.quantidade
            movimentacao.quantidade = movimentacao.quantidade - movimentacao.taxa
            # Usar quantidade para guardar valor da taxa
            movimentacao.preco_unitario = movimentacao.taxa
            
            # Preparar taxa
            movimentacao.taxa = Object()
            movimentacao.taxa.moeda = movimentacao.moeda
            movimentacao.taxa.valor = movimentacao.preco_unitario
            
            movimentacao.criptomoeda = movimentacao.moeda
            
        # Limitar valores totais em reais para 2 casas decimais
        if movimentacao.em_real():
            movimentacao.preco_total = movimentacao.preco_total.quantize(Decimal('0.01'))
            
        total_investido = sum([(moeda.preco_medio * moeda.qtd) for moeda in moedas.values() if moeda.qtd > 0])
        
        data_formatada = str(calendar.timegm(movimentacao.data.timetuple()) * 1000)
        # Adicionar no gráfico
        if graf_investido_total and data_formatada == graf_investido_total[-1][0]:
            graf_investido_total[-1][1] = float(total_investido)
        else:
            graf_investido_total += [[data_formatada, float(total_investido)]]
        
        # Gráfico de patrimônio é passado como totais de cada moeda para cálculo de histórico a partir de queries para a API do CryptoCompare
        data_formatada_utc = calendar.timegm(movimentacao.data.timetuple())
        patrimonio = {moeda: float(dados_moeda.qtd) for moeda, dados_moeda in moedas.items()}
        if graf_patrimonio and data_formatada_utc == graf_patrimonio[-1][1]:
            graf_patrimonio[-1][2] = patrimonio
        else:
            graf_patrimonio += [[data_formatada, data_formatada_utc, patrimonio]]
            
    # Adicionar data atual formatada
    data_formatada = str(calendar.timegm(datetime.date.today().timetuple()) * 1000)
    # Se não existe a data em um gráfico, nenhum gráfico tem a data
    if not (graf_investido_total and data_formatada == graf_investido_total[-1][0]):
        graf_investido_total += [[data_formatada, float(total_investido)]]
        graf_patrimonio += [[data_formatada, None, patrimonio]]
    
#     print ['%s: %s' % (ticker, moeda.qtd) for ticker, moeda in moedas.items()]
    
    dados = {}
    dados['total_investido'] = sum([(moeda.preco_medio * moeda.qtd) for moeda in moedas.values() if moeda.qtd > 0])
    dados['patrimonio'] = sum([moedas[ticker].qtd * valor for ticker, valor in {valor_diario.criptomoeda.ticker: valor_diario.valor for \
                                                valor_diario in ValorDiarioCriptomoeda.objects.filter(criptomoeda__ticker__in=moedas.keys(), moeda='BRL')}.items()])
    dados['lucro'] = dados['patrimonio'] - dados['total_investido']
    dados['lucro_percentual'] = dados['lucro'] / (dados['total_investido'] or 1) * 100
    
    return TemplateResponse(request, 'criptomoedas/historico.html', {'dados': dados, 'movimentacoes': lista_movimentacoes, 
                                                    'graf_investido_total': graf_investido_total, 'graf_patrimonio': json.dumps(graf_patrimonio)})

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
        
        # Validar operação
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
                            mail_admins(u'Erro ao gerar operação em criptomoeda com várias divisões', traceback.format_exc().decode('utf-8'))
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
                        mail_admins(u'Erro ao gerar operação em criptomoeda com uma divisão', traceback.format_exc().decode('utf-8'))
            
        for erro in [erro for erro in form_operacao_criptomoeda.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_operacao_criptomoeda = OperacaoCriptomoedaForm(investidor=investidor)
        formset_divisao = DivisaoCriptomoedaFormSet(investidor=investidor)
    
    return TemplateResponse(request, 'criptomoedas/inserir_operacao_criptomoeda.html', {'form_operacao_criptomoeda': form_operacao_criptomoeda, \
                                                                                              'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@login_required
@adiciona_titulo_descricao('Inserir operação em criptomoedas em lote', 'Inserir lote de registros de operação de compra/venda em criptomoeda')
def inserir_operacao_lote(request):
    investidor = request.user.investidor
        
    if request.method == 'POST':
        form_lote_operacoes = OperacaoCriptomoedaLoteForm(request.POST, investidor=investidor)
        
        if form_lote_operacoes.is_valid():
            try:
                # Verificar se foi enviada lista de strings
                if form_lote_operacoes.cleaned_data.get('operacoes_lote'):
                    lista_string = [string_operacao.strip() for string_operacao in form_lote_operacoes.cleaned_data.get('operacoes_lote').split('\n')]
                    
                    divisao = form_lote_operacoes.cleaned_data.get('divisao')
                    if not divisao or divisao.investidor != investidor:
                        raise ValueError('Divisão inválida')
                    
                    # Verificar se foi enviada confirmação de criação
                    if request.POST.get('confirmar') == '1':
                        # Criar operações
                        criar_operacoes_lote(lista_string, investidor, divisao.id, salvar=True)
                        messages.success(request, 'Operações inseridas com sucesso')
                        return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                    
                    # Verificar se foi enviado cancelamento da confirmação
                    if request.POST.get('confirmar') == '0':
                        return TemplateResponse(request, 'criptomoedas/inserir_operacao_criptomoeda_lote.html', {'form_lote_operacoes': form_lote_operacoes, 'operacoes': list(),
                                                                                                                 'confirmacao': False})

                    else:
                        # Validar operações
                        operacoes = formatar_op_lote_confirmacao(criar_operacoes_lote(lista_string, investidor, divisao.id))
                        return TemplateResponse(request, 'criptomoedas/inserir_operacao_criptomoeda_lote.html', {'form_lote_operacoes': form_lote_operacoes, 'operacoes': operacoes,
                                                                                                                 'confirmacao': True})
                else:
                    raise ValueError('Insira as operações no formato indicado')
            except Exception as e:
                messages.error(request, e)
    else:
        # Form do lote de operações
        form_lote_operacoes = OperacaoCriptomoedaLoteForm(investidor=investidor)
        
        # TESTE
#         operacoes = formatar_op_lote_confirmacao(criar_operacoes_lote(['BTC/BRL;0,48784399;9968,99994;06/06/2017;C;0,00343898;BTC',
#                            'FCT/BTC;2,04838866;0,0110499;07/06/2017;C;0,00513381;FCT',
#                            'FCT/BTC;15,40786135;0,01104999;07/06/2017;C;0,03861619;FCT',
#                            'FCT/BTC;0,61136046;0,01080999;07/06/2017;C;0,00153223;FCT',
#                            'FCT/BTC;0,81185596;0,0098302;09/06/2017;V;0,00001995;BTC',
#                            'FCT/BTC;7,68814404;0,0098302;09/06/2017;V;0,00011336;BTC',
#                            'ETH/BTC;0,109725;0,0967;09/06/2017;C;0,000275;ETH',
#                            'ETH/BTC;0,33706492;0,0967;09/06/2017;C;0,00050635;ETH',
#                            'ETH/BTC;0,41450914;0,0967;09/06/2017;C;0,00062269;ETH',
#                            'LSK/BTC;74,8125;0,00117999;09/06/2017;C;0,1875;LSK',
#                            'LSK/BTC;9,48627159;0,00117998;09/06/2017;C;0,02377511;LSK'], investidor, DivisaoPrincipal.objects.get(investidor=investidor).divisao.id))
    
    return TemplateResponse(request, 'criptomoedas/inserir_operacao_criptomoeda_lote.html', {'form_lote_operacoes': form_lote_operacoes, 'operacoes': list(),
                                                                                             'confirmacao': False})
    
def formatar_op_lote_confirmacao(lista_operacoes_lote):
    """
    Formata operações geradas em lote para confirmação
    Parâmetros: Lista de operações geradas no lote
    Retorno: Operações formatadas para mostrar na página
    """
    operacoes_formatadas = list()
    
    # Testar elementos para agrupá-los por operação
    for elemento in lista_operacoes_lote:
        if isinstance(elemento, OperacaoCriptomoeda):
            elemento.tipo_operacao = 'Compra' if elemento.tipo_operacao == 'C' else 'Venda'
            operacoes_formatadas.append(elemento)
            
        elif isinstance(elemento, DivisaoOperacaoCriptomoeda):
            operacoes_formatadas[len(operacoes_formatadas)-1].divisao = elemento.divisao
            
        elif isinstance(elemento, OperacaoCriptomoedaTaxa):
            operacoes_formatadas[len(operacoes_formatadas)-1].taxa = elemento
    return operacoes_formatadas
    
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
                            mail_admins(u'Erro ao gerar transferência para criptomoedas com várias divisões', traceback.format_exc().decode('utf-8'))
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
                        mail_admins(u'Erro ao gerar transferência para criptomoedas com uma divisão', traceback.format_exc().decode('utf-8'))
            
        for erro in [erro for erro in form_transferencia_criptomoeda.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_fundo_investimento.quantidade, divisao_fundo_investimento.divisao)
                
    else:
        form_transferencia_criptomoeda = TransferenciaCriptomoedaForm(investidor=investidor)
        formset_divisao = DivisaoCriptomoedaFormSet(investidor=investidor)
    
    return TemplateResponse(request, 'criptomoedas/inserir_transferencia.html', {'form_transferencia_criptomoeda': form_transferencia_criptomoeda, \
                                                                                              'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})

@login_required
@adiciona_titulo_descricao('Inserir transferência para criptomoedas em lote', 'Inserir lote de registros de transferência para criptomoedas')
def inserir_transferencia_lote(request):
    investidor = request.user.investidor
        
    if request.method == 'POST':
        form_lote_transferencias = TransferenciaCriptomoedaLoteForm(request.POST, investidor=investidor)
        
        if form_lote_transferencias.is_valid():
            try:
                # Verificar se foi enviada lista de strings
                if form_lote_operacoes.cleaned_data.get('transferencias_lote'):
                    lista_string = form_lote_operacoes.cleaned_data.get('transferencias_lote')
                    
                    divisao = form_lote_operacoes.cleaned_data.get('divisao')
                    if not divisao:
                        raise ValueError('Divisão inválida')
                    
                    # Verificar se foi enviada confirmação de criação
                    if request.POST.get('confirmacao') == '1':
                        # Criar operações
                        criar_transferencias_lote(lista_string, investidor, divisao.id, salvar=True)
                        messages.success(request, 'Operações inseridas com sucesso')
                        return HttpResponseRedirect(reverse('criptomoeda:historico_criptomoeda'))
                        
                    else:
                        # Validar operações
                        operacoes = criar_transferencias_lote(lista_string, investidor, divisao.id)
                        return TemplateResponse(request, 'criptomoedas/inserir_transferencia_criptomoeda_lote.html', {'form_lote_transferencias': form_lote_transferencias})
                else:
                    raise ValueError('Insira as transferências no formato indicado')
            except Exception as e:
                messages.error(request, e)
    else:
        # Form do lote de operações
        form_lote_transferencias = TransferenciaCriptomoedaLoteForm(investidor=investidor)
    
    return TemplateResponse(request, 'criptomoedas/inserir_transferencia_criptomoeda_lote.html', {'form_lote_transferencias': form_lote_transferencias})
    
@adiciona_titulo_descricao('Listar criptomoedas cadastradas', 'Lista as criptomoedas cadastradas no sistema')
def listar_criptomoedas(request):
    moedas = Criptomoeda.objects.all()
    valores_diarios = ValorDiarioCriptomoeda.objects.all().values('valor')
    for moeda in moedas:
        moeda.valor_atual = valores_diarios.get(criptomoeda=moeda, moeda=ValorDiarioCriptomoeda.MOEDA_REAL)['valor']
        moeda.valor_atual_dolar = valores_diarios.get(criptomoeda=moeda, moeda=ValorDiarioCriptomoeda.MOEDA_DOLAR)['valor']
    
    return TemplateResponse(request, 'criptomoedas/listar_moedas.html', {'moedas': moedas})


@login_required
@adiciona_titulo_descricao('Listar transferências em criptomoedas', 'Lista as transferências feitas para criptomoedas pelo investidor')
def listar_transferencias(request):
    investidor = request.user.investidor
    transferencias = TransferenciaCriptomoeda.objects.filter(investidor=investidor)
    
    return TemplateResponse(request, 'criptomoedas/listar_transferencias.html', {'transferencias': transferencias})

@login_required
@adiciona_titulo_descricao('Painel de Criptomoedas', 'Posição atual do investidor em Criptomoedas')
def painel(request):
    investidor = request.user.investidor
    qtd_moedas = calcular_qtd_moedas_ate_dia(investidor)
    
    dados = {}
    dados['total_atual'] = Decimal(0)
    
    moedas = Criptomoeda.objects.filter(id__in=qtd_moedas.keys())
    valores_atuais = ValorDiarioCriptomoeda.objects.filter(criptomoeda__in=qtd_moedas.keys(), moeda=ValorDiarioCriptomoeda.MOEDA_REAL).values('valor')
    for moeda in moedas:
        moeda.qtd_atual = qtd_moedas[moeda.id]
        moeda.valor_atual = valores_atuais.get(criptomoeda=moeda)['valor']
        moeda.total_atual = moeda.qtd_atual * moeda.valor_atual
        
        dados['total_atual'] += moeda.total_atual
    
    return TemplateResponse(request, 'criptomoedas/painel.html', {'moedas': moedas, 'dados': dados})

def sobre(request):
    pass