# -*- coding: utf-8 -*-

from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoCDB_RDBFormSet
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCDB_RDB, Divisao
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.models.td import HistoricoIPCA
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa_di, \
    calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.bagogold.utils.misc import calcular_iof_regressivo, \
    qtd_dias_uteis_no_periodo, calcular_iof_e_ir_longo_prazo
from bagogold.cdb_rdb.forms import OperacaoCDB_RDBForm, \
    HistoricoPorcentagemCDB_RDBForm, CDB_RDBForm, HistoricoCarenciaCDB_RDBForm, \
    HistoricoVencimentoCDB_RDBForm
from bagogold.cdb_rdb.models import OperacaoCDB_RDB, HistoricoPorcentagemCDB_RDB, \
    CDB_RDB, HistoricoCarenciaCDB_RDB, OperacaoVendaCDB_RDB, \
    HistoricoVencimentoCDB_RDB
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia,\
    buscar_operacoes_vigentes_ate_data
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
import calendar
import datetime

@login_required
@adiciona_titulo_descricao('Detalhar CDB/RDB', 'Detalhar CDB/RDB, incluindo histórico de carência e '
                                                'porcentagem de rendimento, além de dados da posição do investidor')
def detalhar_cdb_rdb(request, cdb_rdb_id):
    investidor = request.user.investidor
    
    cdb_rdb = get_object_or_404(CDB_RDB, id=cdb_rdb_id)
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    historico_porcentagem = HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=cdb_rdb)
    historico_carencia = HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cdb_rdb)
    historico_vencimento = HistoricoVencimentoCDB_RDB.objects.filter(cdb_rdb=cdb_rdb)
    
    # Inserir dados do investimento
    cdb_rdb.tipo = cdb_rdb.descricao_tipo()
    cdb_rdb.carencia_atual = cdb_rdb.carencia_atual()
    cdb_rdb.porcentagem_atual = cdb_rdb.porcentagem_atual()
    
    # Preparar estatísticas zeradas
    cdb_rdb.total_investido = Decimal(0)
    cdb_rdb.saldo_atual = Decimal(0)
    cdb_rdb.total_ir = Decimal(0)
    cdb_rdb.total_iof = Decimal(0)
    cdb_rdb.lucro = Decimal(0)
    cdb_rdb.lucro_percentual = Decimal(0)
    
    operacoes = OperacaoCDB_RDB.objects.filter(investimento=cdb_rdb).order_by('data')
    # Contar total de operações já realizadas 
    cdb_rdb.total_operacoes = len(operacoes)
    # Remover operacoes totalmente vendidas
    operacoes = [operacao for operacao in operacoes if operacao.qtd_disponivel_venda() > 0]
    if operacoes:
        historico_di = HistoricoTaxaDI.objects.filter(data__range=[operacoes[0].data, datetime.date.today()])
        for operacao in operacoes:
            # Total investido
            cdb_rdb.total_investido += operacao.qtd_disponivel_venda()
            
            # Saldo atual
            taxas = historico_di.filter(data__gte=operacao.data).values('taxa').annotate(qtd_dias=Count('taxa'))
            taxas_dos_dias = {}
            for taxa in taxas:
                taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.qtd_disponivel_venda(), operacao.porcentagem())
            cdb_rdb.saldo_atual += operacao.atual
            
            # Calcular impostos
            qtd_dias = (datetime.date.today() - operacao.data).days
            # IOF
            operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.quantidade)
            # IR
            if qtd_dias <= 180:
                operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.quantidade - operacao.iof)
            elif qtd_dias <= 360:
                operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.quantidade - operacao.iof)
            elif qtd_dias <= 720:
                operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.quantidade - operacao.iof)
            else: 
                operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.quantidade - operacao.iof)
            cdb_rdb.total_ir += operacao.imposto_renda
            cdb_rdb.total_iof += operacao.iof
    
        # Pegar outras estatísticas
        str_auxiliar = str(cdb_rdb.saldo_atual.quantize(Decimal('.0001')))
        cdb_rdb.saldo_atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        
        cdb_rdb.lucro = cdb_rdb.saldo_atual - cdb_rdb.total_investido
        cdb_rdb.lucro_percentual = cdb_rdb.lucro / cdb_rdb.total_investido * 100
    try: 
        cdb_rdb.dias_prox_vencimento = (min(operacao.data + datetime.timedelta(days=operacao.vencimento()) for operacao in operacoes if \
                                             (operacao.data + datetime.timedelta(days=operacao.vencimento())) > datetime.date.today()) - datetime.date.today()).days
    except ValueError:
        cdb_rdb.dias_prox_vencimento = 0
    
    
    return TemplateResponse(request, 'cdb_rdb/detalhar_cdb_rdb.html', {'cdb_rdb': cdb_rdb, 'historico_porcentagem': historico_porcentagem,
                                                                       'historico_carencia': historico_carencia, 'historico_vencimento': historico_vencimento})

@login_required
@adiciona_titulo_descricao('Editar CDB/RDB', 'Editar os dados de um CDB/RDB')
def editar_cdb_rdb(request, cdb_rdb_id):
    investidor = request.user.investidor
    cdb_rdb = get_object_or_404(CDB_RDB, id=cdb_rdb_id)
    
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_cdb_rdb = CDB_RDBForm(request.POST, instance=cdb_rdb)
            
            if form_cdb_rdb.is_valid():
                cdb_rdb.save()
                messages.success(request, 'CDB/RDB editado com sucesso')
                return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': cdb_rdb.id}))
                
        # TODO verificar o que pode acontecer na exclusão
        elif request.POST.get("delete"):
            if OperacaoCDB_RDB.objects.filter(investimento=cdb_rdb).exists():
                messages.error(request, 'Não é possível excluir o %s pois existem operações cadastradas' % (cdb_rdb.descricao_tipo()))
                return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': cdb_rdb.id}))
            else:
                cdb_rdb.delete()
                messages.success(request, 'CDB/RDB excluído com sucesso')
                return HttpResponseRedirect(reverse('cdb_rdb:listar_cdb_rdb'))
 
    else:
        form_cdb_rdb = CDB_RDBForm(instance=cdb_rdb)
            
    return TemplateResponse(request, 'cdb_rdb/editar_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'cdb_rdb': cdb_rdb})  
    
@login_required
@adiciona_titulo_descricao('Editar registro de carência de um CDB/RDB', 'Alterar um registro de carência no '
                                                                        'histórico do CDB/RDB')
def editar_historico_carencia(request, historico_carencia_id):
    investidor = request.user.investidor
    historico_carencia = get_object_or_404(HistoricoCarenciaCDB_RDB, id=historico_carencia_id)
    
    if historico_carencia.cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_carencia.data is None:
                inicial = True
                form_historico_carencia = HistoricoCarenciaCDB_RDBForm(request.POST, instance=historico_carencia, cdb_rdb=historico_carencia.cdb_rdb, \
                                                                       investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_carencia = HistoricoCarenciaCDB_RDBForm(request.POST, instance=historico_carencia, cdb_rdb=historico_carencia.cdb_rdb, \
                                                                       investidor=investidor)
            if form_historico_carencia.is_valid():
                historico_carencia.save()
                messages.success(request, 'Histórico de carência editado com sucesso')
                return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': historico_carencia.cdb_rdb.id}))
            
            for erro in [erro for erro in form_historico_carencia.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_carencia.data is None:
                messages.error(request, 'Valor inicial de carência não pode ser excluído')
                return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': historico_carencia.cdb_rdb.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            inicial = False
            cdb_rdb = historico_carencia.cdb_rdb
            historico_carencia.delete()
            messages.success(request, 'Histórico de carência excluído com sucesso')
            return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': cdb_rdb.id}))
 
    else:
        if historico_carencia.data is None:
            inicial = True
            form_historico_carencia = HistoricoCarenciaCDB_RDBForm(instance=historico_carencia, cdb_rdb=historico_carencia.cdb_rdb, \
                                                                   investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_carencia = HistoricoCarenciaCDB_RDBForm(instance=historico_carencia, cdb_rdb=historico_carencia.cdb_rdb, \
                                                                   investidor=investidor)
            
    return TemplateResponse(request, 'cdb_rdb/editar_historico_carencia.html', {'form_historico_carencia': form_historico_carencia, 'inicial': inicial}) 
    
@login_required
@adiciona_titulo_descricao('Editar registro de porcentagem de rendimento de um CDB/RDB', 'Alterar um registro de porcentagem de rendimento no '
                                                                                         'histórico do CDB/RDB')
def editar_historico_porcentagem(request, historico_porcentagem_id):
    investidor = request.user.investidor
    historico_porcentagem = get_object_or_404(HistoricoPorcentagemCDB_RDB, id=historico_porcentagem_id)
    
    if historico_porcentagem.cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_porcentagem.data is None:
                inicial = True
                form_historico_porcentagem = HistoricoPorcentagemCDB_RDBForm(request.POST, instance=historico_porcentagem, cdb_rdb=historico_porcentagem.cdb_rdb, \
                                                                             investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_porcentagem = HistoricoPorcentagemCDB_RDBForm(request.POST, instance=historico_porcentagem, cdb_rdb=historico_porcentagem.cdb_rdb, \
                                                                             investidor=investidor)
            if form_historico_porcentagem.is_valid():
                historico_porcentagem.save(force_update=True)
                messages.success(request, 'Histórico de porcentagem editado com sucesso')
                return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': historico_porcentagem.cdb_rdb.id}))
                
            for erro in [erro for erro in form_historico_porcentagem.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_porcentagem.data is None:
                messages.error(request, 'Valor inicial de porcentagem não pode ser excluído')
                return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': historico_porcentagem.cdb_rdb.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            inicial = False
            cdb_rdb = historico_porcentagem.cdb_rdb
            historico_porcentagem.delete()
            messages.success(request, 'Histórico de porcentagem excluído com sucesso')
            return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': cdb_rdb.id}))
 
    else:
        if historico_porcentagem.data is None:
            inicial = True
            form_historico_porcentagem = HistoricoPorcentagemCDB_RDBForm(instance=historico_porcentagem, cdb_rdb=historico_porcentagem.cdb_rdb, \
                                                                         investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_porcentagem = HistoricoPorcentagemCDB_RDBForm(instance=historico_porcentagem, cdb_rdb=historico_porcentagem.cdb_rdb, \
                                                                         investidor=investidor)
            
    return TemplateResponse(request, 'cdb_rdb/editar_historico_porcentagem.html', {'form_historico_porcentagem': form_historico_porcentagem, 'inicial': inicial}) 
    
@login_required
@adiciona_titulo_descricao('Editar registro de vencimento de um CDB/RDB', 'Alterar um registro de vencimento no '
                                                                        'histórico do CDB/RDB')
def editar_historico_vencimento(request, historico_vencimento_id):
    investidor = request.user.investidor
    historico_vencimento = get_object_or_404(HistoricoVencimentoCDB_RDB, id=historico_vencimento_id)
    
    if historico_vencimento.cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            if historico_vencimento.data is None:
                inicial = True
                form_historico_carencia = HistoricoVencimentoCDB_RDBForm(request.POST, instance=historico_vencimento, cdb_rdb=historico_vencimento.cdb_rdb, \
                                                                       investidor=investidor, inicial=inicial)
            else:
                inicial = False
                form_historico_carencia = HistoricoVencimentoCDB_RDBForm(request.POST, instance=historico_vencimento, cdb_rdb=historico_vencimento.cdb_rdb, \
                                                                       investidor=investidor)
            if form_historico_carencia.is_valid():
                historico_vencimento.save()
                messages.success(request, 'Histórico de carência editado com sucesso')
                return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': historico_vencimento.cdb_rdb.id}))
            
            for erro in [erro for erro in form_historico_carencia.non_field_errors()]:
                messages.error(request, erro)
                
        elif request.POST.get("delete"):
            if historico_vencimento.data is None:
                messages.error(request, 'Valor inicial de carência não pode ser excluído')
                return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': historico_vencimento.cdb_rdb.id}))
            # Pegar investimento para o redirecionamento no caso de exclusão
            inicial = False
            cdb_rdb = historico_vencimento.cdb_rdb
            historico_vencimento.delete()
            messages.success(request, 'Histórico de carência excluído com sucesso')
            return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': cdb_rdb.id}))
 
    else:
        if historico_vencimento.data is None:
            inicial = True
            form_historico_vencimento = HistoricoVencimentoCDB_RDBForm(instance=historico_vencimento, cdb_rdb=historico_vencimento.cdb_rdb, \
                                                                   investidor=investidor, inicial=inicial)
        else: 
            inicial = False
            form_historico_vencimento = HistoricoVencimentoCDB_RDBForm(instance=historico_vencimento, cdb_rdb=historico_vencimento.cdb_rdb, \
                                                                   investidor=investidor)
            
    return TemplateResponse(request, 'cdb_rdb/editar_historico_vencimento.html', {'form_historico_vencimento': form_historico_vencimento, 'inicial': inicial})     

@login_required
@adiciona_titulo_descricao('Editar operação em CDB/RDB', 'Alterar valores de uma operação de compra/venda em CDB/RDB')
def editar_operacao_cdb_rdb(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_cdb_rdb = get_object_or_404(OperacaoCDB_RDB, id=operacao_id)
    if operacao_cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoCDB_RDB, DivisaoOperacaoCDB_RDB, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoCDB_RDBFormSet)
    
    if request.method == 'POST':
        form_operacao_cdb_rdb = OperacaoCDB_RDBForm(request.POST, instance=operacao_cdb_rdb, investidor=investidor)
        formset_divisao = DivisaoFormSet(request.POST, instance=operacao_cdb_rdb, investidor=investidor) if varias_divisoes else None
        
        if request.POST.get("save"):
            if form_operacao_cdb_rdb.is_valid():
                operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_cdb_rdb, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_cdb_rdb.save()
                        if operacao_cdb_rdb.tipo_operacao == 'V':
                            if not OperacaoVendaCDB_RDB.objects.filter(operacao_venda=operacao_cdb_rdb):
                                operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                                operacao_venda_cdb_rdb.save()
                            else: 
                                operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb)
                                if operacao_venda_cdb_rdb.operacao_compra != operacao_compra:
                                    operacao_venda_cdb_rdb.operacao_compra = operacao_compra
                                    operacao_venda_cdb_rdb.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação editada com sucesso')
                        return HttpResponseRedirect(reverse('cdb_rdb:historico_cdb_rdb'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                        
                else:
                    operacao_cdb_rdb.save()
                    if operacao_cdb_rdb.tipo_operacao == 'V':
                        if not OperacaoVendaCDB_RDB.objects.filter(operacao_venda=operacao_cdb_rdb):
                            operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                            operacao_venda_cdb_rdb.save()
                        else: 
                            operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb)
                            if operacao_venda_cdb_rdb.operacao_compra != operacao_compra:
                                operacao_venda_cdb_rdb.operacao_compra = operacao_compra
                                operacao_venda_cdb_rdb.save()
                    divisao_operacao = DivisaoOperacaoCDB_RDB.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_cdb_rdb)
                    divisao_operacao.quantidade = operacao_cdb_rdb.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('cdb_rdb:historico_cdb_rdb'))
                
            for erro in [erro for erro in form_operacao_cdb_rdb.non_field_errors()]:
                messages.error(request, erro)
#                         print '%s %s'  % (divisao_cdb_rdb.quantidade, divisao_cdb_rdb.divisao)
                
        elif request.POST.get("delete"):
            # Testa se operação a excluir não é uma operação de compra com vendas já registradas
            if not OperacaoVendaCDB_RDB.objects.filter(operacao_compra=operacao_cdb_rdb):
                divisao_cdb_rdb = DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao_cdb_rdb)
                for divisao in divisao_cdb_rdb:
                    divisao.delete()
                if operacao_cdb_rdb.tipo_operacao == 'V':
                    OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb).delete()
                operacao_cdb_rdb.delete()
                messages.success(request, 'Operação excluída com sucesso')
                return HttpResponseRedirect(reverse('cdb_rdb:historico_cdb_rdb'))
            else:
                messages.error(request, 'Não é possível excluir operação de compra que já tenha vendas registradas')
 
    else:
        form_operacao_cdb_rdb = OperacaoCDB_RDBForm(instance=operacao_cdb_rdb, initial={'operacao_compra': operacao_cdb_rdb.operacao_compra_relacionada(),}, \
                                                    investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=operacao_cdb_rdb, investidor=investidor)
            
    return TemplateResponse(request, 'cdb_rdb/editar_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})  

    
@adiciona_titulo_descricao('Histórico de CDB/RDB', 'Histórico de operações de compra/venda em CDB/RDB')
def historico(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'cdb_rdb/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_gasto_total': list(), 'graf_patrimonio': list()})
    
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    # Verifica se não há operações
    if not operacoes:
        return TemplateResponse(request, 'cdb_rdb/historico.html', {'dados': {}})
    
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.atual = operacao.quantidade
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
            operacao.taxa = operacao.porcentagem()
        else:
            operacao.tipo = 'Venda'
    
    # Pegar data inicial
    data_inicial = operacoes.order_by('data')[0].data
    
    # Pegar data final
    data_final = max(HistoricoTaxaDI.objects.filter().order_by('-data')[0].data, datetime.date.today())
    
    data_iteracao = data_inicial
    
    total_gasto = 0
    total_patrimonio = 0
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    graf_gasto_total = list()
    graf_patrimonio = list()

    while data_iteracao <= data_final:
        try:
            taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
        except:
            taxa_do_dia = 0
            
        # Calcular o valor atualizado do patrimonio diariamente
        total_patrimonio = 0
        
        # Processar operações
        for operacao in operacoes:     
            if (operacao.data <= data_iteracao):     
                # Verificar se se trata de compra ou venda
                if operacao.tipo_operacao == 'C':
                    if (operacao.data == data_iteracao):
                        operacao.total = operacao.quantidade
                        total_gasto += operacao.total
                    # Calcular o valor atualizado para cada operacao
                    if operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_DI and taxa_do_dia > 0:
                        # DI
                        operacao.atual = calcular_valor_atualizado_com_taxa_di(taxa_do_dia, operacao.atual, operacao.taxa)
                    elif operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
                        # Prefixado
                        operacao.atual = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa)
                    # Arredondar na última iteração
                    if (data_iteracao == data_final):
                        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                    total_patrimonio += operacao.atual
                        
                elif operacao.tipo_operacao == 'V':
                    if (operacao.data == data_iteracao):
                        operacao.total = operacao.quantidade
                        total_gasto -= operacao.total
                        # Remover quantidade da operação de compra
                        operacao_compra_id = operacao.operacao_compra_relacionada().id
                        for operacao_c in operacoes:
                            if (operacao_c.id == operacao_compra_id):
                                # Configurar taxa para a mesma quantidade da compra
                                operacao.taxa = operacao_c.taxa
                                operacao.atual = (operacao.quantidade/operacao_c.quantidade) * operacao_c.atual
                                operacao_c.atual -= operacao.atual
                                operacao.atual -= sum(calcular_iof_e_ir_longo_prazo(operacao.atual - operacao.quantidade, (operacao.data - operacao_c.data).days))
                                str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
                                operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                                break
                
        if len(operacoes.filter(data=data_iteracao)) > 0 or data_iteracao == data_final:
            graf_gasto_total += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_gasto)]]
            graf_patrimonio += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_patrimonio)]]
        
        # Proximo dia útil
        proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
        if len(proximas_datas) > 0:
            data_iteracao = proximas_datas[0].data
        elif data_iteracao < data_final:
            data_iteracao = data_final
        else:
            break

    dados = {}
    dados['total_gasto'] = total_gasto
    dados['patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio - total_gasto
    dados['lucro_percentual'] = (total_patrimonio - total_gasto) / total_gasto * 100
    
    return TemplateResponse(request, 'cdb_rdb/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio})
    

@login_required
@adiciona_titulo_descricao('Inserir CDB/RDB', 'Inserir um novo CDB/RDB nas opções do investidor')
def inserir_cdb_rdb(request):
    investidor = request.user.investidor
    
    # Preparar formsets 
    PorcentagemFormSet = inlineformset_factory(CDB_RDB, HistoricoPorcentagemCDB_RDB, fields=('porcentagem',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True)
    CarenciaFormSet = inlineformset_factory(CDB_RDB, HistoricoCarenciaCDB_RDB, fields=('carencia',), form=LocalizedModelForm,
                                            extra=1, can_delete=False, max_num=1, validate_max=True, labels = {'carencia': 'Período de carência (em dias)',})
    
    if request.method == 'POST':
        form_cdb_rdb = CDB_RDBForm(request.POST)
        formset_porcentagem = PorcentagemFormSet(request.POST)
        formset_carencia = CarenciaFormSet(request.POST)
        if form_cdb_rdb.is_valid():
            cdb_rdb = form_cdb_rdb.save(commit=False)
            cdb_rdb.investidor = investidor
            formset_porcentagem = PorcentagemFormSet(request.POST, instance=cdb_rdb)
            formset_porcentagem.forms[0].empty_permitted=False
            formset_carencia = CarenciaFormSet(request.POST, instance=cdb_rdb)
            formset_carencia.forms[0].empty_permitted=False
            
            if formset_porcentagem.is_valid():
                if formset_carencia.is_valid():
                    try:
                        cdb_rdb.save()
                        formset_porcentagem.save()
                        formset_carencia.save()
                    # Capturar erros oriundos da hora de salvar os objetos
                    except Exception as erro:
                        messages.error(request, erro.message)
                        return TemplateResponse(request, 'cdb_rdb/inserir_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'formset_porcentagem': formset_porcentagem,
                                                          'formset_carencia': formset_carencia})
                        
                    return HttpResponseRedirect(reverse('cdb_rdb:listar_cdb_rdb'))
                
        for erro in [erro for erro in form_cdb_rdb.non_field_errors()]:
            messages.error(request, erro)
        for erro in formset_porcentagem.non_form_errors():
            messages.error(request, erro)
        for erro in formset_carencia.non_form_errors():
            messages.error(request, erro)
            
    else:
        form_cdb_rdb = CDB_RDBForm()
        formset_porcentagem = PorcentagemFormSet()
        formset_carencia = CarenciaFormSet()
    return TemplateResponse(request, 'cdb_rdb/inserir_cdb_rdb.html', {'form_cdb_rdb': form_cdb_rdb, 'formset_porcentagem': formset_porcentagem,
                                                              'formset_carencia': formset_carencia})

@login_required
@adiciona_titulo_descricao('Inserir registro de carência para um CDB/RDB', 'Inserir registro de alteração de carência ao histórico de '
                                                                           'um CDB/RDB')
def inserir_historico_carencia_cdb_rdb(request, cdb_rdb_id):
    investidor = request.user.investidor
    cdb_rdb = get_object_or_404(CDB_RDB, id=cdb_rdb_id)
    
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoCarenciaCDB_RDBForm(request.POST, initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de carência para %s alterado com sucesso' % historico.cdb_rdb)
            return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': cdb_rdb.id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoCarenciaCDB_RDBForm(initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb, investidor=investidor)
            
    return TemplateResponse(request, 'cdb_rdb/inserir_historico_carencia_cdb_rdb.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir registro de porcentagem para um CDB/RDB', 'Inserir registro de alteração de porcentagem de rendimento '
                                                                              'ao histórico de um CDB/RDB')
def inserir_historico_porcentagem_cdb_rdb(request, cdb_rdb_id):
    investidor = request.user.investidor
    cdb_rdb = get_object_or_404(CDB_RDB, id=cdb_rdb_id)
    
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoPorcentagemCDB_RDBForm(request.POST, initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de porcentagem de rendimento para %s alterado com sucesso' % historico.cdb_rdb)
            return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': cdb_rdb.id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoPorcentagemCDB_RDBForm(initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb, investidor=investidor)
            
    return TemplateResponse(request, 'cdb_rdb/inserir_historico_porcentagem_cdb_rdb.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir registro de vencimento para um CDB/RDB', 'Inserir registro de alteração de vencimento ao histórico de '
                                                                           'um CDB/RDB')
def inserir_historico_vencimento_cdb_rdb(request, cdb_rdb_id):
    investidor = request.user.investidor
    cdb_rdb = get_object_or_404(CDB_RDB, id=cdb_rdb_id)
    
    if cdb_rdb.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HistoricoVencimentoCDB_RDBForm(request.POST, initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb, investidor=investidor)
        if form.is_valid():
            historico = form.save()
            messages.success(request, 'Histórico de período de vencimento para %s alterado com sucesso' % historico.cdb_rdb)
            return HttpResponseRedirect(reverse('cdb_rdb:detalhar_cdb_rdb', kwargs={'cdb_rdb_id': cdb_rdb.id}))
        
        for erro in [erro for erro in form.non_field_errors()]:
            messages.error(request, erro)
    else:
        form = HistoricoVencimentoCDB_RDBForm(initial={'cdb_rdb': cdb_rdb.id}, cdb_rdb=cdb_rdb, investidor=investidor)
            
    return TemplateResponse(request, 'cdb_rdb/inserir_historico_vencimento_cdb_rdb.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir operação em CDB/RDB', 'Inserir registro de operação de compra/venda em CDB/RDB')
def inserir_operacao_cdb_rdb(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoCDB_RDBFormSet = inlineformset_factory(OperacaoCDB_RDB, DivisaoOperacaoCDB_RDB, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoCDB_RDBFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_operacao_cdb_rdb = OperacaoCDB_RDBForm(request.POST, investidor=investidor)
        formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar CDB/RDB
        if form_operacao_cdb_rdb.is_valid():
            operacao_cdb_rdb = form_operacao_cdb_rdb.save(commit=False)
            operacao_cdb_rdb.investidor = investidor
            operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
            formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(request.POST, instance=operacao_cdb_rdb, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                
            # Validar em caso de venda
            if form_operacao_cdb_rdb.cleaned_data['tipo_operacao'] == 'V':
                operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
                # Caso de venda total do cdb/rdb
                if form_operacao_cdb_rdb.cleaned_data['quantidade'] == operacao_compra.quantidade:
                    # Desconsiderar divisões inseridas, copiar da operação de compra
                    operacao_cdb_rdb.save()
                    for divisao_cdb_rdb in DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao_compra):
                        divisao_cdb_rdb_venda = DivisaoOperacaoCDB_RDB(quantidade=divisao_cdb_rdb.quantidade, divisao=divisao_cdb_rdb.divisao, \
                                                             operacao=operacao_cdb_rdb)
                        divisao_cdb_rdb_venda.save()
                    operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                    operacao_venda_cdb_rdb.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('cdb_rdb:historico_cdb_rdb'))
                # Vendas parciais
                else:
                    # Verificar se varias divisões
                    if varias_divisoes:
                        if formset_divisao_cdb_rdb.is_valid():
                            operacao_cdb_rdb.save()
                            formset_divisao_cdb_rdb.save()
                            operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                            operacao_venda_cdb_rdb.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('cdb_rdb:historico_cdb_rdb'))
                        for erro in formset_divisao_cdb_rdb.non_form_errors():
                            messages.error(request, erro)
                                
                    else:
                        operacao_cdb_rdb.save()
                        divisao_operacao = DivisaoOperacaoCDB_RDB(operacao=operacao_cdb_rdb, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_cdb_rdb.quantidade)
                        divisao_operacao.save()
                        operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                        operacao_venda_cdb_rdb.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('cdb_rdb:historico_cdb_rdb'))
            
            # Compra
            else:
                # Verificar se várias divisões
                if varias_divisoes:
                    if formset_divisao_cdb_rdb.is_valid():
                        operacao_cdb_rdb.save()
                        formset_divisao_cdb_rdb.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('cdb_rdb:historico_cdb_rdb'))
                    for erro in formset_divisao_cdb_rdb.non_form_errors():
                        messages.error(request, erro)
                                
                else:
                    operacao_cdb_rdb.save()
                    divisao_operacao = DivisaoOperacaoCDB_RDB(operacao=operacao_cdb_rdb, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_cdb_rdb.quantidade)
                    divisao_operacao.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('cdb_rdb:historico_cdb_rdb'))
                    
        for erro in [erro for erro in form_operacao_cdb_rdb.non_field_errors()]:
            messages.error(request, erro)
#                         print '%s %s'  % (divisao_cdb_rdb.quantidade, divisao_cdb_rdb.divisao)
                
    else:
        form_operacao_cdb_rdb = OperacaoCDB_RDBForm(investidor=investidor)
        formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(investidor=investidor)
    return TemplateResponse(request, 'cdb_rdb/inserir_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao': formset_divisao_cdb_rdb,
                                                                        'varias_divisoes': varias_divisoes})

@adiciona_titulo_descricao('Listar CDB/RDB', 'Lista de CDBs e RDBs cadastrados pelo investidor')
def listar_cdb_rdb(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'cdb_rdb/listar_cdb_rdb.html', {'cdb_rdb': list()})
    
    cdb_rdb = CDB_RDB.objects.filter(investidor=investidor)
    
    for investimento in cdb_rdb:
        # Preparar o valor mais atual para carência
        investimento.carencia_atual = investimento.carencia_atual()
        # Preparar o valor mais atual de rendimento
        investimento.rendimento_atual = investimento.porcentagem_atual()
        
        if investimento.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
            investimento.str_tipo_rendimento = 'Prefixado'
        elif investimento.tipo_rendimento in [CDB_RDB.CDB_RDB_DI, CDB_RDB.CDB_RDB_IPCA]:
            investimento.str_tipo_rendimento = 'Pós-fixado'
        
    return TemplateResponse(request, 'cdb_rdb/listar_cdb_rdb.html', {'cdb_rdb': cdb_rdb})

@adiciona_titulo_descricao('Painel de CDB/RDB', 'Posição atual do investidor em CDB/RDB')
def painel(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'cdb_rdb/painel.html', {'operacoes': list(), 'dados': {}})
         
    # Processa primeiro operações de venda (V), depois compra (C)
#     operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
#     print operacoes, len(operacoes)
     
    operacoes = buscar_operacoes_vigentes_ate_data(investidor).order_by('data') 
    if not operacoes:
        dados = {}
        dados['total_atual'] = Decimal(0)
        dados['total_ir'] = Decimal(0)
        dados['total_iof'] = Decimal(0)
        dados['total_ganho_prox_dia'] = Decimal(0)
        return TemplateResponse(request, 'cdb_rdb/painel.html', {'operacoes': {}, 'dados': dados})
     
    # Pegar data final, nivelar todas as operações para essa data
    data_final = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
     
    # Prepara o campo valor atual
    for operacao in operacoes:
        operacao.quantidade = operacao.qtd_disponivel_venda
        operacao.atual = operacao.quantidade
        operacao.inicial = operacao.quantidade
        operacao.taxa = operacao.porcentagem()
        data_final_valorizacao = min(data_final, operacao.data_vencimento() - datetime.timedelta(days=1))
        # Calcular o valor atualizado
        if operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
            # DI
            historico = HistoricoTaxaDI.objects.filter(data__range=[operacao.data, data_final_valorizacao])
            taxas_dos_dias = dict(historico.values('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
            operacao.atual = calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, operacao.atual, operacao.taxa)
        elif operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO:
            # Prefixado
            # Calcular quantidade dias para valorização, adicionar 1 pois a função exclui a data final
            qtd_dias = qtd_dias_uteis_no_periodo(operacao.data, data_final_valorizacao) + 1
            operacao.atual = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa, qtd_dias)
        # Arredondar valores
        str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
        operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                         
    # Remover operações que não estejam mais rendendo
    operacoes = [operacao for operacao in operacoes if (operacao.atual > 0 and operacao.tipo_operacao == 'C')]
     
    total_atual = 0
    total_ir = 0
    total_iof = 0
    total_ganho_prox_dia = 0
    total_vencimento = 0
     
    ultima_taxa_di = HistoricoTaxaDI.objects.filter().order_by('-data')[0].taxa
     
    for operacao in operacoes:
        # Calcular o ganho no dia seguinte
        if data_final < operacao.data_vencimento():
            # Se prefixado apenas pegar rendimento de 1 dia
            if operacao.investimento.eh_prefixado():
                operacao.ganho_prox_dia = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa) - operacao.atual
            elif operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
                # Considerar rendimento do dia anterior
                operacao.ganho_prox_dia = calcular_valor_atualizado_com_taxa_di(ultima_taxa_di, operacao.atual, operacao.taxa) - operacao.atual
            # Formatar
            str_auxiliar = str(operacao.ganho_prox_dia.quantize(Decimal('.0001')))
            operacao.ganho_prox_dia = Decimal(str_auxiliar[:len(str_auxiliar)-2])
            total_ganho_prox_dia += operacao.ganho_prox_dia
        else:
            operacao.ganho_prox_dia = Decimal('0.00')
         
        # Calcular impostos
        qtd_dias = (datetime.date.today() - operacao.data).days
#         print qtd_dias, calcular_iof_regressivo(qtd_dias)
        # IOF
        operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.inicial)
        # IR
        if qtd_dias <= 180:
            operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.inicial - operacao.iof)
        elif qtd_dias <= 360:
            operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.inicial - operacao.iof)
        elif qtd_dias <= 720:
            operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.inicial - operacao.iof)
        else: 
            operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.inicial - operacao.iof)
         
        # Valor líquido
        operacao.valor_liquido = operacao.atual - operacao.imposto_renda - operacao.iof
         
        # Estimativa para o valor do investimento na data de vencimento
        if data_final < operacao.data_vencimento():
            qtd_dias_uteis_ate_vencimento = qtd_dias_uteis_no_periodo(data_final + datetime.timedelta(days=1), operacao.data_vencimento())
            # Se prefixado apenas pegar rendimento de 1 dia
            if operacao.investimento.eh_prefixado():
                operacao.valor_vencimento = calcular_valor_atualizado_com_taxa_prefixado(operacao.atual, operacao.taxa, qtd_dias_uteis_ate_vencimento)
            elif operacao.investimento.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
                # Considerar rendimento do dia anterior
                operacao.valor_vencimento = calcular_valor_atualizado_com_taxas_di({HistoricoTaxaDI.objects.get(data=data_final).taxa: qtd_dias_uteis_ate_vencimento},
                                                     operacao.atual, operacao.taxa)
            str_auxiliar = str(operacao.valor_vencimento.quantize(Decimal('.0001')))
            operacao.valor_vencimento = Decimal(str_auxiliar[:len(str_auxiliar)-2])
        else:
            operacao.valor_vencimento = operacao.atual
         
        total_atual += operacao.atual
        total_ir += operacao.imposto_renda
        total_iof += operacao.iof
        total_vencimento += operacao.valor_vencimento
     
    # Popular dados
    dados = {}
    dados['data_di_mais_recente'] = data_final
    dados['total_atual'] = total_atual
    dados['total_ir'] = total_ir
    dados['total_iof'] = total_iof
    dados['total_liquido'] = total_atual - total_ir - total_iof
    dados['total_ganho_prox_dia'] = total_ganho_prox_dia
    dados['total_vencimento'] = total_vencimento
     
    return TemplateResponse(request, 'cdb_rdb/painel.html', {'operacoes': operacoes, 'dados': dados})

@adiciona_titulo_descricao('Sobre CDB/RDB', 'Detalha o que são CDB e RDB')
def sobre(request):
    data_atual = datetime.date.today()
    historico_di = HistoricoTaxaDI.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3))
    graf_historico_di = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(valor_historico.taxa)] for valor_historico in historico_di]
    
    historico_ipca = HistoricoIPCA.objects.filter(ano__gte=(data_atual.year-3)).exclude(mes__lt=data_atual.month, ano=data_atual.year-3)
    graf_historico_ipca = [[str(calendar.timegm(valor_historico.data().timetuple()) * 1000), float(valor_historico.valor)] for valor_historico in historico_ipca]
    
    if request.user.is_authenticated():
        total_atual = sum(calcular_valor_cdb_rdb_ate_dia(request.user.investidor).values())
    else:
        total_atual = 0
    
    return TemplateResponse(request, 'cdb_rdb/sobre.html', {'graf_historico_di': graf_historico_di, 'graf_historico_ipca': graf_historico_ipca,
                                                            'total_atual': total_atual})