# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoForm, \
    TransferenciaEntreDivisoesForm
from bagogold.bagogold.models.acoes import ValorDiarioAcao, HistoricoAcao, Acao
from bagogold.cdb_rdb.models import CDB_RDB, \
    HistoricoPorcentagemCDB_RDB
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoLC, \
    DivisaoOperacaoFII, DivisaoOperacaoTD, DivisaoOperacaoAcao, \
    TransferenciaEntreDivisoes, DivisaoOperacaoFundoInvestimento, \
    DivisaoOperacaoCDB_RDB
from bagogold.bagogold.models.fii import ValorDiarioFII, HistoricoFII, FII
from bagogold.bagogold.models.lc import HistoricoPorcentagemLetraCredito, \
    LetraCredito
from bagogold.bagogold.models.td import ValorDiarioTitulo, HistoricoTitulo, \
    Titulo
from bagogold.bagogold.utils.acoes import calcular_qtd_acoes_ate_dia_por_divisao
from bagogold.cdb_rdb.utils import \
    calcular_valor_cdb_rdb_ate_dia_por_divisao
from bagogold.bagogold.utils.debenture import \
    calcular_valor_debentures_ate_dia_por_divisao
from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_divisao
from bagogold.bagogold.utils.lc import calcular_valor_lc_ate_dia_por_divisao
from bagogold.bagogold.utils.td import calcular_qtd_titulos_ate_dia_por_divisao
from bagogold.cri_cra.utils.utils import \
    calcular_valor_cri_cra_ate_dia_para_divisao
from bagogold.criptomoeda.models import Criptomoeda
from bagogold.criptomoeda.utils import calcular_qtd_moedas_ate_dia_por_divisao, \
    buscar_valor_criptomoedas_atual
from bagogold.fundo_investimento.models import FundoInvestimento, \
    HistoricoValorCotas, OperacaoFundoInvestimento
from bagogold.fundo_investimento.utils import \
    calcular_qtd_cotas_ate_dia_por_divisao
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
import datetime

@login_required
@adiciona_titulo_descricao('Gerar transferências', 'Insere transferências no histórico automaticamente '
    'considerando as operações que o usuário já inseriu')
def criar_transferencias(request):
    investidor = request.user.investidor
    
    if request.method == 'POST':
        print 'POST'
    
    divisoes = Divisao.objects.filter(investidor=investidor)
    
    # Transferências criadas
    transferencias = list()
    
    for divisao in divisoes:
        print divisao
        # Letra de crédito
        for divisao_operacao in DivisaoOperacaoLC.objects.filter(divisao=divisao, operacao__tipo_operacao='C').order_by('operacao__data'):
            saldo_no_dia = divisao.saldo_lc(divisao_operacao.operacao.data) + sum([transferencia.quantidade for transferencia in transferencias if transferencia.investimento_destino == 'L'])
#             print 'Compra na Data:', divisao_operacao.operacao.data, divisao_operacao.quantidade
#             print 'Saldo:', divisao.saldo_lc(divisao_operacao.operacao.data)
            
            if saldo_no_dia < 0:
                transferencia = TransferenciaEntreDivisoes(divisao_recebedora=divisao, investimento_destino='L', quantidade=-saldo_no_dia, data=divisao_operacao.operacao.data, descricao='Gerada automaticamente')
#                 transferencia.save()
                print transferencia
                transferencias.append(transferencia)
                
        # CDB / RDB
        for divisao_operacao in DivisaoOperacaoCDB_RDB.objects.filter(divisao=divisao, operacao__tipo_operacao='C').order_by('operacao__data'):
            saldo_no_dia = divisao.saldo_cdb_rdb(divisao_operacao.operacao.data) + sum([transferencia.quantidade for transferencia in transferencias if transferencia.investimento_destino == 'C'])
#             print 'Compra na Data:', divisao_operacao.operacao.data, divisao_operacao.quantidade
#             print 'Saldo:', divisao.saldo_cdb_rdb(divisao_operacao.operacao.data)
            
            if saldo_no_dia < 0:
                transferencia = TransferenciaEntreDivisoes(divisao_recebedora=divisao, investimento_destino='C', quantidade=-saldo_no_dia, data=divisao_operacao.operacao.data, descricao='Gerada automaticamente')
#                 transferencia.save()
                print transferencia
                transferencias.append(transferencia)
                
        # Tesouro Direto
        for divisao_operacao in DivisaoOperacaoTD.objects.filter(divisao=divisao, operacao__tipo_operacao='C').order_by('operacao__data'):
            saldo_no_dia = divisao.saldo_td(divisao_operacao.operacao.data) + sum([transferencia.quantidade for transferencia in transferencias if transferencia.investimento_destino == 'T'])
            print 'Compra na Data:', divisao_operacao.operacao.data, divisao_operacao.quantidade
            print 'Saldo:', divisao.saldo_td(divisao_operacao.operacao.data)
            
            if saldo_no_dia < 0:
                transferencia = TransferenciaEntreDivisoes(divisao_recebedora=divisao, investimento_destino='T', quantidade=-saldo_no_dia, data=divisao_operacao.operacao.data, descricao='Gerada automaticamente')
#                 transferencia.save()
                print transferencia
                transferencia.operacao = divisao_operacao.operacao
                transferencias.append(transferencia)
        
    return TemplateResponse(request, 'divisoes/criar_transferencias.html', {'transferencias': transferencias})

@login_required
@adiciona_titulo_descricao('Detalhar divisão', 'Detalha a composição de uma divisão')
def detalhar_divisao(request, id):
    investidor = request.user.investidor
    
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    divisao = Divisao.objects.get(id=id)
    if divisao.investidor != investidor:
        raise PermissionDenied
    
    divisao.valor_total = 0
    
    composicao = {}
    
    # Adicionar Acoes
    composicao['acoes'] = Object()
    composicao['acoes'].nome = 'Ações (Buy and Hold)'
    composicao['acoes'].patrimonio = 0
    composicao['acoes'].composicao = {}
    # Pegar FIIs contidos na divisão
    qtd_acoes_dia = calcular_qtd_acoes_ate_dia_por_divisao(datetime.date.today(), divisao.id)
    for ticker in qtd_acoes_dia.keys():
        acao_valor = Acao.objects.get(ticker=ticker).valor_no_dia(datetime.date.today())
#         print ticker, qtd_acoes_dia[ticker] * acao_valor
        composicao['acoes'].patrimonio += qtd_acoes_dia[ticker] * acao_valor
        composicao['acoes'].composicao[ticker] = Object()
        composicao['acoes'].composicao[ticker].nome = ticker
        composicao['acoes'].composicao[ticker].patrimonio = qtd_acoes_dia[ticker] * acao_valor
        composicao['acoes'].composicao[ticker].composicao = {}
        # Pegar operações dos FIIs
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=divisao, operacao__acao__ticker=ticker):
            composicao['acoes'].composicao[ticker].composicao[operacao_divisao.operacao.id] = Object()
            composicao['acoes'].composicao[ticker].composicao[operacao_divisao.operacao.id].nome = operacao_divisao.operacao.tipo_operacao
            composicao['acoes'].composicao[ticker].composicao[operacao_divisao.operacao.id].data = operacao_divisao.operacao.data
            composicao['acoes'].composicao[ticker].composicao[operacao_divisao.operacao.id].quantidade = operacao_divisao.quantidade
            composicao['acoes'].composicao[ticker].composicao[operacao_divisao.operacao.id].valor_unitario = Acao.objects.get(ticker=ticker).valor_no_dia(operacao_divisao.operacao.data)
#             print composicao['acoes'].composicao[ticker].composicao[operacao_divisao.operacao.id].valor_unitario
            composicao['acoes'].composicao[ticker].composicao[operacao_divisao.operacao.id].patrimonio = operacao_divisao.quantidade * \
                composicao['acoes'].composicao[ticker].composicao[operacao_divisao.operacao.id].valor_unitario
    
    # Adicionar FIIs
    composicao['fii'] = Object()
    composicao['fii'].nome = 'Fundos de Invest. Imob.'
    composicao['fii'].patrimonio = 0
    composicao['fii'].composicao = {}
    # Pegar FIIs contidos na divisão
    qtd_fiis_dia = calcular_qtd_fiis_ate_dia_por_divisao(datetime.date.today(), divisao.id)
    for ticker in qtd_fiis_dia.keys():
        fii_valor = FII.objects.get(ticker=ticker).valor_no_dia(datetime.date.today())
        composicao['fii'].patrimonio += qtd_fiis_dia[ticker] * fii_valor
        composicao['fii'].composicao[ticker] = Object()
        composicao['fii'].composicao[ticker].nome = ticker
        composicao['fii'].composicao[ticker].patrimonio = qtd_fiis_dia[ticker] * fii_valor
        composicao['fii'].composicao[ticker].composicao = {}
        # Pegar operações dos FIIs
        for operacao_divisao in DivisaoOperacaoFII.objects.filter(divisao=divisao, operacao__fii__ticker=ticker):
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id] = Object()
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].nome = operacao_divisao.operacao.tipo_operacao
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].data = operacao_divisao.operacao.data
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].quantidade = operacao_divisao.quantidade
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].valor_unitario = FII.objects.get(ticker=ticker).valor_no_dia(operacao_divisao.operacao.data)
            composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].patrimonio = operacao_divisao.quantidade * \
                composicao['fii'].composicao[ticker].composicao[operacao_divisao.operacao.id].valor_unitario
                
    # Adicionar Fundos de investimento
    composicao['fundo-investimento'] = Object()
    composicao['fundo-investimento'].nome = 'Fundos de Investimento'
    composicao['fundo-investimento'].patrimonio = 0
    composicao['fundo-investimento'].composicao = {}
    # Pegar fundos de investimento contidos na divisão
    qtd_fundos_dia = calcular_qtd_cotas_ate_dia_por_divisao(datetime.date.today(), divisao.id)
    for fundo_id in qtd_fundos_dia.keys():
        fundo_valor = FundoInvestimento.objects.get(id=fundo_id).valor_no_dia(investidor, datetime.date.today())
        composicao['fundo-investimento'].patrimonio += qtd_fundos_dia[fundo_id] * fundo_valor
        composicao['fundo-investimento'].composicao[fundo_id] = Object()
        composicao['fundo-investimento'].composicao[fundo_id].nome = FundoInvestimento.objects.get(id=fundo_id).nome
        composicao['fundo-investimento'].composicao[fundo_id].patrimonio = qtd_fundos_dia[fundo_id] * fundo_valor
        composicao['fundo-investimento'].composicao[fundo_id].composicao = {}
        # Pegar operações dos fundos de investimento
        for operacao_divisao in DivisaoOperacaoFundoInvestimento.objects.filter(divisao=divisao, operacao__fundo_investimento__id=fundo_id):
            composicao['fundo-investimento'].composicao[fundo_id].composicao[operacao_divisao.operacao.id] = Object()
            composicao['fundo-investimento'].composicao[fundo_id].composicao[operacao_divisao.operacao.id].nome = operacao_divisao.operacao.tipo_operacao
            composicao['fundo-investimento'].composicao[fundo_id].composicao[operacao_divisao.operacao.id].data = operacao_divisao.operacao.data
            composicao['fundo-investimento'].composicao[fundo_id].composicao[operacao_divisao.operacao.id].quantidade = operacao_divisao.quantidade
            composicao['fundo-investimento'].composicao[fundo_id].composicao[operacao_divisao.operacao.id].valor_unitario = operacao_divisao.operacao.valor_cota()
            composicao['fundo-investimento'].composicao[fundo_id].composicao[operacao_divisao.operacao.id].patrimonio = operacao_divisao.quantidade * \
                composicao['fundo-investimento'].composicao[fundo_id].composicao[operacao_divisao.operacao.id].valor_unitario
    
    # Adicionar letras de crédito
    composicao['lc'] = Object()
    composicao['lc'].nome = 'Letras de Crédito'
    composicao['lc'].patrimonio = 0
    composicao['lc'].composicao = {}
    valores_letras_credito_dia = calcular_valor_lc_ate_dia_por_divisao(datetime.date.today(), divisao.id)
    for lc_id in valores_letras_credito_dia.keys():
        composicao['lc'].patrimonio += valores_letras_credito_dia[lc_id]
        composicao['lc'].composicao[lc_id] = Object()
        composicao['lc'].composicao[lc_id].nome = LetraCredito.objects.get(id=lc_id).nome
        composicao['lc'].composicao[lc_id].patrimonio = valores_letras_credito_dia[lc_id]
        composicao['lc'].composicao[lc_id].composicao = {}
        # Pegar operações dos LCs
        for operacao_divisao in DivisaoOperacaoLC.objects.filter(divisao=divisao, operacao__letra_credito__id=lc_id):
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id] = Object()
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].nome = operacao_divisao.operacao.tipo_operacao
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].data = operacao_divisao.operacao.data
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].quantidade = operacao_divisao.quantidade
            try:
                composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].valor_unitario = HistoricoPorcentagemLetraCredito.objects.filter(letra_credito=operacao_divisao.operacao.letra_credito, \
                                                                                                                                        data__lte=operacao_divisao.operacao.data).order_by('-data')[0].porcentagem_di
            except:
                composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].valor_unitario = HistoricoPorcentagemLetraCredito.objects.get(data__isnull=True, letra_credito=operacao_divisao.operacao.letra_credito).porcentagem_di
            
            composicao['lc'].composicao[lc_id].composicao[operacao_divisao.operacao.id].patrimonio = operacao_divisao.quantidade
            
    # Adicionar cdb-rdb
    composicao['cdb-rdb'] = Object()
    composicao['cdb-rdb'].nome = 'CDB/RDB'
    composicao['cdb-rdb'].patrimonio = 0
    composicao['cdb-rdb'].composicao = {}
    valores_cdb_rdb_dia = calcular_valor_cdb_rdb_ate_dia_por_divisao(datetime.date.today(), divisao.id)
    for cdb_rdb_id in valores_cdb_rdb_dia.keys():
        composicao['cdb-rdb'].patrimonio += valores_cdb_rdb_dia[cdb_rdb_id]
        composicao['cdb-rdb'].composicao[cdb_rdb_id] = Object()
        composicao['cdb-rdb'].composicao[cdb_rdb_id].nome = CDB_RDB.objects.get(id=cdb_rdb_id).nome
        composicao['cdb-rdb'].composicao[cdb_rdb_id].patrimonio = valores_cdb_rdb_dia[cdb_rdb_id]
        composicao['cdb-rdb'].composicao[cdb_rdb_id].composicao = {}
        # Pegar operações dos cdb-rdbs
        for operacao_divisao in DivisaoOperacaoCDB_RDB.objects.filter(divisao=divisao, operacao__investimento__id=cdb_rdb_id):
            composicao['cdb-rdb'].composicao[cdb_rdb_id].composicao[operacao_divisao.operacao.id] = Object()
            composicao['cdb-rdb'].composicao[cdb_rdb_id].composicao[operacao_divisao.operacao.id].nome = operacao_divisao.operacao.tipo_operacao
            composicao['cdb-rdb'].composicao[cdb_rdb_id].composicao[operacao_divisao.operacao.id].data = operacao_divisao.operacao.data
            composicao['cdb-rdb'].composicao[cdb_rdb_id].composicao[operacao_divisao.operacao.id].quantidade = operacao_divisao.quantidade
            try:
                composicao['cdb-rdb'].composicao[cdb_rdb_id].composicao[operacao_divisao.operacao.id].valor_unitario = HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=operacao_divisao.operacao.investimento, \
                                                                                                                                        data__lte=operacao_divisao.operacao.data).order_by('-data')[0].porcentagem
            except:
                composicao['cdb-rdb'].composicao[cdb_rdb_id].composicao[operacao_divisao.operacao.id].valor_unitario = HistoricoPorcentagemCDB_RDB.objects.get(data__isnull=True, cdb_rdb=operacao_divisao.operacao.investimento).porcentagem
            
            composicao['cdb-rdb'].composicao[cdb_rdb_id].composicao[operacao_divisao.operacao.id].patrimonio = operacao_divisao.quantidade
    
    # Adicionar TDs
    composicao['td'] = Object()
    composicao['td'].nome = 'Tesouro Direto'
    composicao['td'].patrimonio = 0
    composicao['td'].composicao = {}
    # Pegar TDs contidos na divisão
    qtd_tds_dia = calcular_qtd_titulos_ate_dia_por_divisao(datetime.date.today(), divisao.id)
    for titulo_id in qtd_tds_dia.keys():
        try:
            td_valor = ValorDiarioTitulo.objects.filter(titulo__id=titulo_id, data_hora__day=datetime.date.today().day, data_hora__month=datetime.date.today().month).order_by('-data_hora')[0].preco_venda
        except:
            td_valor = HistoricoTitulo.objects.filter(titulo__id=titulo_id).order_by('-data')[0].preco_venda
        composicao['td'].patrimonio += qtd_tds_dia[titulo_id] * td_valor
        composicao['td'].composicao[titulo_id] = Object()
        composicao['td'].composicao[titulo_id].nome = Titulo.objects.get(id=titulo_id).nome
        composicao['td'].composicao[titulo_id].patrimonio = qtd_tds_dia[titulo_id] * td_valor
        composicao['td'].composicao[titulo_id].composicao = {}
        # Pegar operações dos TDs
        for operacao_divisao in DivisaoOperacaoTD.objects.filter(divisao=divisao, operacao__titulo__id=titulo_id):
            composicao['td'].composicao[titulo_id].composicao[operacao_divisao.operacao.id] = Object()
            composicao['td'].composicao[titulo_id].composicao[operacao_divisao.operacao.id].nome = operacao_divisao.operacao.tipo_operacao
            composicao['td'].composicao[titulo_id].composicao[operacao_divisao.operacao.id].data = operacao_divisao.operacao.data
            composicao['td'].composicao[titulo_id].composicao[operacao_divisao.operacao.id].quantidade = operacao_divisao.quantidade
            composicao['td'].composicao[titulo_id].composicao[operacao_divisao.operacao.id].valor_unitario = td_valor
            composicao['td'].composicao[titulo_id].composicao[operacao_divisao.operacao.id].patrimonio = operacao_divisao.quantidade * td_valor
    
    # Calcular valor total da divisão
    for key, item in composicao.items():
        if item.patrimonio == 0:
            del composicao[key]
        else:
            divisao.valor_total += item.patrimonio
        
    # Calcular valor percentual para cada item da composição da divisão
    for item in composicao.values():
        item.percentual = item.patrimonio / divisao.valor_total * 100
        # Calcular valor percentual para cada operação
        for operacao in item.composicao.values():
            operacao.percentual = operacao.patrimonio / item.patrimonio * 100
        
    return TemplateResponse(request, 'divisoes/detalhar_divisao.html', {'divisao': divisao, 'composicao': composicao})

@login_required
@adiciona_titulo_descricao('Editar divisão', 'Alterar dados de uma divisão')
def editar_divisao(request, id):
    investidor = request.user.investidor
    
    divisao = Divisao.objects.get(pk=id)
    if divisao.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = DivisaoForm(request.POST, instance=divisao)
        if request.POST.get("save"):            
            if form.is_valid():
                divisao.save()
                messages.success(request, 'Divisão editada com sucesso')
                return HttpResponseRedirect(reverse('divisoes:listar_divisoes'))
            for erros in form.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
            return TemplateResponse(request, 'divisoes/editar_divisao.html', {'form': form, 'divisao': divisao})
                
        elif request.POST.get("delete"):
            if divisao.divisao_principal():
                messages.error(request, 'Divisão principal não pode ser excluída')
                return TemplateResponse(request, 'divisoes/editar_divisao.html', {'form': form, 'divisao': divisao})
            elif divisao.possui_operacoes_registradas():
                messages.error(request, 'Divisão possui operações registradas')
                return TemplateResponse(request, 'divisoes/editar_divisao.html', {'form': form, 'divisao': divisao})
            divisao.delete()
            messages.success(request, 'Divisão excluída com sucesso')
            return HttpResponseRedirect(reverse('divisoes:listar_divisoes'))
 
    else:
        form = DivisaoForm(instance=divisao)
            
    return TemplateResponse(request, 'divisoes/editar_divisao.html', {'form': form, 'divisao': divisao})
    
@login_required
@adiciona_titulo_descricao('Editar transferência', 'Alterar valores de uma transferência no histórico')
def editar_transferencia(request, id):
    investidor = request.user.investidor
    
    # Checar ambas as divisões
    transferencia = TransferenciaEntreDivisoes.objects.get(pk=id)
    if transferencia.divisao_cedente and transferencia.divisao_cedente.investidor != investidor:
        raise PermissionDenied
    if transferencia.divisao_recebedora and transferencia.divisao_recebedora.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form = TransferenciaEntreDivisoesForm(request.POST, instance=transferencia, investidor=investidor)
            
            if form.is_valid():
                transferencia.save()
                messages.success(request, 'Transferência editada com sucesso')
                return HttpResponseRedirect(reverse('divisoes:listar_transferencias'))
            for erros in form.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
            return TemplateResponse(request, 'divisoes/editar_transferencia.html', {'form': form})
                
        elif request.POST.get("delete"):
            transferencia.delete()
            messages.success(request, 'Operação excluída com sucesso')
            return HttpResponseRedirect(reverse('divisoes:listar_transferencias'))
 
    else:
        form = TransferenciaEntreDivisoesForm(instance=transferencia, investidor=investidor)
            
    return TemplateResponse(request, 'divisoes/editar_transferencia.html', {'form': form})
    
@login_required
@adiciona_titulo_descricao('Inserir divisão', 'Inserir divisão para o investidor')
def inserir_divisao(request):
    investidor = request.user.investidor
    
    if request.method == 'POST':
        form = DivisaoForm(request.POST)
        if form.is_valid():
            divisao = form.save(commit=False)
            divisao.investidor = investidor
            divisao.save()
            return HttpResponseRedirect(reverse('divisoes:listar_divisoes'))
    else:
        form = DivisaoForm()
            
    return TemplateResponse(request, 'divisoes/inserir_divisao.html', {'form': form})

@login_required
@adiciona_titulo_descricao('Inserir transferência', 'Inserir registro de transferência do histórico do investidor')
def inserir_transferencia(request):
    investidor = request.user.investidor
    
    if request.method == 'POST':
        form = TransferenciaEntreDivisoesForm(request.POST, investidor=investidor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transferência inserida com sucesso')
            return HttpResponseRedirect(reverse('divisoes:listar_transferencias'))
        # Imprimir erors nas mensagens
        for erro in form.non_field_errors():
#             print erro
            messages.error(request, erro)
    else:
        form = TransferenciaEntreDivisoesForm(investidor=investidor)
            
    return TemplateResponse(request, 'divisoes/inserir_transferencia.html', {'form': form})

@adiciona_titulo_descricao('Listar divisões', 'Valores atuais para totais investidos e saldos de cada divisão do investidor')
def listar_divisoes(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'divisoes/listar_divisoes.html', {'divisoes': list()})
    
    divisoes = Divisao.objects.filter(investidor=investidor)
    
    for divisao in divisoes:
        divisao.valor_atual = 0
        divisao.valor_atual_bh = 0
        divisao.valor_atual_trade = 0
        divisao.valor_atual_cdb_rdb = 0
        divisao.valor_atual_cri_cra = 0
        divisao.valor_atual_criptomoeda = 0
        divisao.valor_atual_debentures = 0
        divisao.valor_atual_fii = 0
        divisao.valor_atual_fundo_investimento = 0
        divisao.valor_atual_lc = 0
        divisao.valor_atual_td = 0
        
        data_atual = datetime.date.today()
        
        # Ações (B&H)
        acao_divisao = calcular_qtd_acoes_ate_dia_por_divisao(data_atual, divisao.id, destinacao='B')
        for ticker in acao_divisao.keys():
            if ValorDiarioAcao.objects.filter(acao__ticker=ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
                acao_valor = ValorDiarioAcao.objects.filter(acao__ticker=ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_unitario
            else:
                acao_valor = HistoricoAcao.objects.filter(acao__ticker=ticker).order_by('-data')[0].preco_unitario
            divisao.valor_atual_bh += (acao_divisao[ticker] * acao_valor)
        
        # Ações (Trade)
        acao_divisao = calcular_qtd_acoes_ate_dia_por_divisao(data_atual, divisao.id, destinacao='T')
        for ticker in acao_divisao.keys():
            if ValorDiarioAcao.objects.filter(acao__ticker=ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
                acao_valor = ValorDiarioAcao.objects.filter(acao__ticker=ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_unitario
            else:
                acao_valor = HistoricoAcao.objects.filter(acao__ticker=ticker).order_by('-data')[0].preco_unitario
            divisao.valor_atual_trade += (acao_divisao[ticker] * acao_valor)
        divisao.valor_atual += divisao.valor_atual_bh + divisao.valor_atual_trade
         
        # CDB / RDB
        cdb_rdb_divisao = calcular_valor_cdb_rdb_ate_dia_por_divisao(data_atual, divisao.id)
        divisao.valor_atual_cdb_rdb += sum(cdb_rdb_divisao.values())
        divisao.valor_atual += divisao.valor_atual_cdb_rdb
         
        # CRI / CRA
        cri_cra_divisao = calcular_valor_cri_cra_ate_dia_para_divisao(divisao.id, data_atual)
        divisao.valor_atual_cri_cra += sum(cri_cra_divisao.values())
        divisao.valor_atual += divisao.valor_atual_cri_cra
        
        # Criptomoedas
        criptomoedas_divisao = calcular_qtd_moedas_ate_dia_por_divisao(divisao.id, data_atual)
        moedas = Criptomoeda.objects.filter(id__in=criptomoedas_divisao.keys())
        valores_criptomoedas = buscar_valor_criptomoedas_atual([moeda.ticker for moeda in moedas])
        divisao.valor_atual_criptomoeda += sum([(criptomoedas_divisao[moeda.id] * valores_criptomoedas[moeda.ticker]) for moeda in moedas])
        divisao.valor_atual += divisao.valor_atual_criptomoeda
        
        # Debêntures
        debentures_divisao = calcular_valor_debentures_ate_dia_por_divisao(divisao.id, data_atual)
        divisao.valor_atual_debentures += sum(debentures_divisao.values())
        divisao.valor_atual += divisao.valor_atual_debentures
         
        # Fundos de investimento imobiliário
        fii_divisao = calcular_qtd_fiis_ate_dia_por_divisao(data_atual, divisao.id)
        for ticker in fii_divisao.keys():
            if ValorDiarioFII.objects.filter(fii__ticker=ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
                fii_valor = ValorDiarioFII.objects.filter(fii__ticker=ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_unitario
            else:
                fii_valor = HistoricoFII.objects.filter(fii__ticker=ticker).order_by('-data')[0].preco_unitario
            divisao.valor_atual_fii += (fii_divisao[ticker] * fii_valor)
        divisao.valor_atual += divisao.valor_atual_fii
         
        # Fundos de investimento
        fundo_investimento_divisao = calcular_qtd_cotas_ate_dia_por_divisao(data_atual, divisao.id)
        print fundo_investimento_divisao
        for fundo_id in fundo_investimento_divisao.keys():
            historico_fundo = HistoricoValorCotas.objects.filter(fundo_investimento__id=fundo_id).order_by('-data')
            ultima_operacao_fundo = OperacaoFundoInvestimento.objects.filter(fundo_investimento__id=fundo_id).order_by('-data')[0]
            if historico_fundo and historico_fundo[0].data > ultima_operacao_fundo.data:
                valor_cota = historico_fundo[0].valor_cota
            else:
                valor_cota = ultima_operacao_fundo.valor_cota()
            divisao.valor_atual_fundo_investimento += (fundo_investimento_divisao[fundo_id] * valor_cota)
        divisao.valor_atual += divisao.valor_atual_fundo_investimento
             
        # Letras de crédito
        lc_divisao = calcular_valor_lc_ate_dia_por_divisao(data_atual, divisao.id)
        divisao.valor_atual_lc += sum(lc_divisao.values())
        divisao.valor_atual += divisao.valor_atual_lc
         
        # Tesouro Direto
        td_divisao = calcular_qtd_titulos_ate_dia_por_divisao(data_atual, divisao.id)
        for titulo_id in td_divisao.keys():
            if ValorDiarioTitulo.objects.filter(titulo__id=titulo_id, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
                td_valor = ValorDiarioTitulo.objects.filter(titulo__id=titulo_id, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_venda
            else:
                td_valor = HistoricoTitulo.objects.filter(titulo__id=titulo_id).order_by('-data')[0].preco_venda
            divisao.valor_atual_td += (td_divisao[titulo_id] * td_valor)
        divisao.valor_atual += divisao.valor_atual_td
#             print 'valor:', divisao.valor_atual
         
        if not divisao.objetivo_indefinido():
            divisao.quantidade_percentual = divisao.valor_atual / divisao.valor_objetivo * 100
        else:
            divisao.quantidade_percentual = 100
            
        # Calcular saldo da divisão
        divisao.saldo_bh = divisao.saldo_acoes_bh()
        divisao.saldo_cdb_rdb = divisao.saldo_cdb_rdb()
        divisao.saldo_cri_cra = divisao.saldo_cri_cra()
        divisao.saldo_criptomoeda = divisao.saldo_criptomoeda()
        divisao.saldo_debentures = divisao.saldo_debentures()
        divisao.saldo_fii = divisao.saldo_fii()
        divisao.saldo_fundo_investimento = divisao.saldo_fundo_investimento()
        divisao.saldo_lc = divisao.saldo_lc()
        divisao.saldo_td = divisao.saldo_td()
        divisao.saldo_trade = divisao.saldo_acoes_trade()
        divisao.saldo = divisao.saldo_bh + divisao.saldo_cdb_rdb + divisao.saldo_cri_cra + divisao.saldo_criptomoeda \
            + divisao.saldo_debentures + divisao.saldo_fii + divisao.saldo_fundo_investimento + divisao.saldo_lc \
            + divisao.saldo_td + divisao.saldo_trade
              
    return TemplateResponse(request, 'divisoes/listar_divisoes.html', {'divisoes': divisoes})

@adiciona_titulo_descricao('Listar transferências', 'Histórico de transferências feitas para as divisões do investidor')
def listar_transferencias(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'divisoes/listar_transferencias.html', {'transferencias': list()})
    
    transferencias = TransferenciaEntreDivisoes.objects.filter(Q(divisao_cedente__investidor=investidor) | Q(divisao_recebedora__investidor=investidor))
    
    for transferencia in transferencias:
        transferencia.investimento_origem = transferencia.investimento_origem_completo()
        transferencia.investimento_destino = transferencia.investimento_destino_completo()
    
    return TemplateResponse(request, 'divisoes/listar_transferencias.html', {'transferencias': transferencias})
