# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.models.acoes import OperacaoAcao, HistoricoAcao, Provento, \
    ValorDiarioAcao
from bagogold.bagogold.models.cdb_rdb import OperacaoCDB_RDB
from bagogold.bagogold.models.debentures import OperacaoDebenture, \
    HistoricoValorDebenture
from bagogold.bagogold.models.fii import OperacaoFII, HistoricoFII, ProventoFII, \
    ValorDiarioFII
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento, HistoricoValorCotas
from bagogold.bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI
from bagogold.bagogold.models.td import OperacaoTitulo, HistoricoTitulo, \
    ValorDiarioTitulo
from bagogold.bagogold.utils.acoes import calcular_poupanca_prov_acao_ate_dia
from bagogold.bagogold.utils.cdb_rdb import calcular_valor_cdb_rdb_ate_dia, \
    calcular_valor_venda_cdb_rdb
from bagogold.bagogold.utils.debenture import calcular_valor_debentures_ate_dia
from bagogold.bagogold.utils.fii import calcular_poupanca_prov_fii_ate_dia
from bagogold.bagogold.utils.investidores import buscar_ultimas_operacoes, \
    buscar_totais_atuais_investimentos, buscar_proventos_a_receber, \
    buscar_proventos_a_receber_data_ex_futura
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas, \
    calcular_valor_lc_ate_dia, calcular_valor_venda_lc
from bagogold.bagogold.utils.misc import calcular_rendimentos_ate_data, \
    verificar_feriado_bovespa
from bagogold.bagogold.utils.td import calcular_valor_td_ate_dia
from bagogold.cri_cra.models.cri_cra import OperacaoCRI_CRA
from bagogold.cri_cra.utils.utils import calcular_valor_cri_cra_ate_dia
from bagogold.cri_cra.utils.valorizacao import calcular_valor_um_cri_cra_na_data
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When
from django.db.models.fields import DecimalField
from django.template.response import TemplateResponse
from itertools import chain
from operator import attrgetter
import calendar
import datetime
import math

# TODO remover login_required
# @login_required
@adiciona_titulo_descricao('Painel inicial', 'Traz informações gerais sobre a posição atual em cada tipo de investimento')
def inicio(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'inicio.html')
    # Guardar data atual
    data_atual = datetime.datetime.now()
    
    ultimas_operacoes = buscar_ultimas_operacoes(request.user.investidor, 5) 

    investimentos_atuais = list()
    investimentos = buscar_totais_atuais_investimentos(request.user.investidor) 
    for chave, valor in investimentos.items():
        investimento = Object()
        investimento.valor = valor
        investimento.descricao = chave
        if chave == 'Ações':
            investimento.link = 'acoes:painel_bh'
        elif chave == 'CDB/RDB':
            investimento.link = 'cdb_rdb:painel_cdb_rdb'
        elif chave == 'CRI/CRA':
            investimento.link = 'cri_cra:painel_cri_cra'
        elif chave == 'Debêntures':
            investimento.link = 'debentures:painel_debenture'
        elif chave == 'FII':
            investimento.link = 'fii:painel_fii'
        elif chave == 'Fundos de Inv.':
            investimento.link = 'fundo_investimento:painel_fundo_investimento'
        elif chave == 'Letras de Crédito':
            investimento.link = 'lci_lca:painel_lci_lca'
        elif chave == 'Tesouro Direto':
            investimento.link = 'td:painel_td'
            
        investimentos_atuais.append(investimento)
#         print chave, investimento.link
    # Pegar total atual de todos os investimentos
    total_atual_investimentos = sum([valor for valor in investimentos.values()])
    
    # Ordenar proventos a receber e separar por grupos
    # Proventos a receber com data EX já passada
    proventos_a_receber = buscar_proventos_a_receber(request.user.investidor)
    
    # Recebidos hoje
    proventos_acoes_recebidos_hoje = [provento for provento in proventos_a_receber if isinstance(provento, Provento) and provento.data_pagamento == data_atual.date()]
    proventos_acoes_recebidos_hoje.sort(key=lambda provento: provento.acao)
    
    proventos_fiis_recebidos_hoje = [provento for provento in proventos_a_receber if isinstance(provento, ProventoFII) and provento.data_pagamento == data_atual.date()]
    proventos_fiis_recebidos_hoje.sort(key=lambda provento: provento.fii)
    
    # A receber futuramente
    proventos_acoes_a_receber = [provento for provento in proventos_a_receber if isinstance(provento, Provento) and provento.data_pagamento > data_atual.date()]
    proventos_acoes_a_receber.sort(key=lambda provento: provento.data_pagamento)
    
    proventos_fiis_a_receber = [provento for provento in proventos_a_receber if isinstance(provento, ProventoFII) and provento.data_pagamento > data_atual.date()]
    proventos_fiis_a_receber.sort(key=lambda provento: provento.data_pagamento)
    
    # Proventos a receber com data EX ainda não passada
    proventos_futuros = buscar_proventos_a_receber_data_ex_futura(request.user.investidor)
    proventos_acoes_futuros = [provento for provento in proventos_futuros if isinstance(provento, Provento)]
    proventos_acoes_futuros.sort(key=lambda provento: provento.data_ex)
    
    proventos_fiis_futuros = [provento for provento in proventos_futuros if isinstance(provento, ProventoFII)]
    proventos_fiis_futuros.sort(key=lambda provento: provento.data_ex)
    
    # Buscar dados para o acumulado mensal
    ultimo_dia_mes_anterior = data_atual.date().replace(day=1) - datetime.timedelta(days=1)
    acumulado_mensal_atual = sum(calcular_rendimentos_ate_data(investidor, data_atual).values()) - sum(calcular_rendimentos_ate_data(investidor, ultimo_dia_mes_anterior).values())
                                                                                          
    ultimo_dia_mes_antes_do_anterior = ultimo_dia_mes_anterior.replace(day=1) - datetime.timedelta(days=1)         
    acumulado_mensal_anterior = sum(calcular_rendimentos_ate_data(investidor, ultimo_dia_mes_anterior).values()) - sum(calcular_rendimentos_ate_data(investidor, ultimo_dia_mes_antes_do_anterior).values())
    
    qtd_ultimos_dias = 22
    # Guardar valores totais
    diario_cdb_rdb = {}
    diario_lc = {}
    diario_td = {}
    diario_debentures = {}
    diario_cri_cra = {}
    
    total_lc_dia_anterior = float(sum(calcular_valor_lc_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
    total_cdb_rdb_dia_anterior = float(sum(calcular_valor_cdb_rdb_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
    total_td_dia_anterior = float(sum(calcular_valor_td_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
    total_debentures_dia_anterior = float(sum(calcular_valor_debentures_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
    total_cri_cra_dia_anterior = float(sum(calcular_valor_cri_cra_ate_dia(investidor, (data_atual - datetime.timedelta(days=qtd_ultimos_dias)).date()).values()))
    
    operacoes_lci_lca_no_periodo = OperacaoLetraCredito.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
    operacoes_cdb_rdb_no_periodo = OperacaoCDB_RDB.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
    operacoes_td_no_periodo = OperacaoTitulo.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
    operacoes_debenture_no_periodo = OperacaoDebenture.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], investidor=investidor)
    operacoes_cri_cra_no_periodo = OperacaoCRI_CRA.objects.filter(data__range=[data_atual - datetime.timedelta(qtd_ultimos_dias), data_atual], cri_cra__investidor=investidor)
    
    for dia in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))]:
        dia = dia.date()
        diario_cdb_rdb[dia] = 0
        diario_lc[dia] = 0
        diario_td[dia] = 0
        diario_debentures[dia] = 0
        diario_cri_cra[dia] = 0
        
        if dia.weekday() < 5 and not verificar_feriado_bovespa(dia):
            # Letra de Crédito
            total_lc = float(sum(calcular_valor_lc_ate_dia(investidor, dia).values()))
#                     print '(%s) %s - %s =' % (dia, total_lc, total_lc_dia_anterior), total_lc - total_lc_dia_anterior
            # Removendo operações do dia
            diario_lc[dia] += total_lc - total_lc_dia_anterior - float(operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='C').aggregate(soma_compras=Sum('quantidade'))['soma_compras'] or Decimal(0)) + \
                float(sum([calcular_valor_venda_lc(operacao_venda) for operacao_venda in operacoes_lci_lca_no_periodo.filter(data=dia, tipo_operacao='V')]))
            total_lc_dia_anterior = total_lc
            
            # CDB / RDB
            total_cdb_rdb = float(sum(calcular_valor_cdb_rdb_ate_dia(investidor, dia).values()))
#                     print '(%s) %s - %s =' % (dia, total_cdb_rdb, total_cdb_rdb_dia_anterior), total_cdb_rdb - total_cdb_rdb_dia_anterior
            # Removendo operações do dia
            diario_cdb_rdb[dia] += total_cdb_rdb - total_cdb_rdb_dia_anterior - float(operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='C').aggregate(soma_compras=Sum('quantidade'))['soma_compras'] or Decimal(0)) + \
                float(sum([calcular_valor_venda_cdb_rdb(operacao_venda) for operacao_venda in operacoes_cdb_rdb_no_periodo.filter(data=dia, tipo_operacao='V')]))
            total_cdb_rdb_dia_anterior = total_cdb_rdb
            
            # Tesouro Direto
            total_td = float(sum(calcular_valor_td_ate_dia(investidor, dia).values()))
            # Removendo operações do dia
            operacoes_do_dia = operacoes_td_no_periodo.filter(data=dia).aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('preco_unitario')*F('quantidade')),
                            When(tipo_operacao='V', then=F('preco_unitario')*F('quantidade')*-1),
                            output_field=DecimalField())))['total'] or Decimal(0)
            diario_td[dia] += total_td - total_td_dia_anterior - float(operacoes_do_dia)
            total_td_dia_anterior = total_td
            
            # Debêntures
            total_debentures = float(sum(calcular_valor_debentures_ate_dia(investidor, dia).values()))
            # Removendo operações do dia
            operacoes_do_dia = operacoes_debenture_no_periodo.filter(data=dia).aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('preco_unitario')*F('quantidade') + F('taxa')),
                            When(tipo_operacao='V', then=F('preco_unitario')*F('quantidade')*-1 - F('taxa')),
                            output_field=DecimalField())))['total'] or Decimal(0)
            diario_debentures[dia] += total_debentures - total_debentures_dia_anterior - float(operacoes_do_dia)
            total_debentures_dia_anterior = total_debentures
            
            # CRI / CRA
            total_cri_cra = float(sum(calcular_valor_cri_cra_ate_dia(investidor, dia).values()))
            # Removendo operações do dia
            operacoes_do_dia = operacoes_cri_cra_no_periodo.filter(data=dia).aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('preco_unitario')*F('quantidade') + F('taxa')),
                            When(tipo_operacao='V', then=F('preco_unitario')*F('quantidade')*-1 - F('taxa')),
                            output_field=DecimalField())))['total'] or Decimal(0)
            diario_cri_cra[dia] += total_cri_cra - total_cri_cra_dia_anterior - float(operacoes_do_dia)
            total_cri_cra_dia_anterior = total_cri_cra
                
    graf_rendimentos_mensal_cdb_rdb = [[str(calendar.timegm(data.replace(hour=3).timetuple()) * 1000), diario_cdb_rdb[data.date()] ] \
                               for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ] 
    graf_rendimentos_mensal_lc = [[str(calendar.timegm(data.replace(hour=6).timetuple()) * 1000), diario_lc[data.date()] ] \
                               for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ] 
    graf_rendimentos_mensal_td = [[str(calendar.timegm(data.replace(hour=9).timetuple()) * 1000), diario_td[data.date()] ] \
                               for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ] 
    graf_rendimentos_mensal_debentures = [[str(calendar.timegm(data.replace(hour=12).timetuple()) * 1000), diario_debentures[data.date()] ] \
                               for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ] 
    graf_rendimentos_mensal_cri_cra = [[str(calendar.timegm(data.replace(hour=15).timetuple()) * 1000), diario_cri_cra[data.date()] ] \
                               for data in [(data_atual - datetime.timedelta(dias_subtrair)) for dias_subtrair in reversed(range(qtd_ultimos_dias))] ]
    
    return TemplateResponse(request, 'inicio.html', {'ultimas_operacoes': ultimas_operacoes, 'investimentos_atuais': investimentos_atuais, 'acumulado_mensal_atual': acumulado_mensal_atual,
                                                     'acumulado_mensal_anterior': acumulado_mensal_anterior, 'proventos_acoes_recebidos_hoje': proventos_acoes_recebidos_hoje,
                                                     'proventos_fiis_recebidos_hoje': proventos_fiis_recebidos_hoje, 'proventos_acoes_a_receber': proventos_acoes_a_receber,
                                                     'proventos_fiis_a_receber': proventos_fiis_a_receber, 'proventos_acoes_futuros': proventos_acoes_futuros,
                                                     'proventos_fiis_futuros': proventos_fiis_futuros,'graf_rendimentos_mensal_lc': graf_rendimentos_mensal_lc,
                                                     'total_atual_investimentos': total_atual_investimentos, 'graf_rendimentos_mensal_cdb_rdb': graf_rendimentos_mensal_cdb_rdb,
                                                     'graf_rendimentos_mensal_td': graf_rendimentos_mensal_td, 'graf_rendimentos_mensal_debentures': graf_rendimentos_mensal_debentures,
                                                     'graf_rendimentos_mensal_cri_cra': graf_rendimentos_mensal_cri_cra})

@login_required
@adiciona_titulo_descricao('Histórico detalhado', 'Histórico detalhado das operações feitas pelo investidor')
def detalhamento_investimentos(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass

    investidor = request.user.investidor
    
    # Adicionar FIIs do investidor
    operacoes_fii = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    if operacoes_fii:
        proventos_fii = ProventoFII.objects.exclude(data_ex__isnull=True).filter(fii__in=operacoes_fii.values_list('fii', flat=True), data_ex__range=[operacoes_fii[0].data, datetime.date.today()]) \
            .order_by('data_ex').annotate(data=F('data_ex'))
    else:
        proventos_fii = list()
    
    # Adicionar operações de Tesouro Direto do investidor
    operacoes_td = OperacaoTitulo.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Adicionar operações de Buy and Hold do investidor
    operacoes_bh = OperacaoAcao.objects.filter(investidor=investidor, destinacao='B').exclude(data__isnull=True).order_by('data')
    if operacoes_bh:
        proventos_bh = Provento.objects.exclude(data_ex__isnull=True).filter(acao__in=operacoes_bh.values_list('acao', flat=True), data_ex__range=[operacoes_bh[0].data, datetime.date.today()]) \
            .order_by('data_ex').annotate(data=F('data_ex'))
    else:
        proventos_bh = list()
        
    # Adicionar operações de Trading do investidor
    operacoes_t = OperacaoAcao.objects.filter(investidor=investidor, destinacao='T').exclude(data__isnull=True).order_by('data')
    
    # Adicionar operações de LCI/LCA do investidor
    operacoes_lc = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  

    # Adicionar operações de CDB/RDB do investidor    
    operacoes_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  
    
    # Adicionar operações de CRI/CRA do investidor    
    operacoes_cri_cra = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor).exclude(data__isnull=True).order_by('data') 
    
    # Adicionar operações de Debêntures do investidor
    operacoes_debentures = OperacaoDebenture.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Adicionar operações de Fundo de Investimento do investidor
    operacoes_fundo_investimento = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    # Juntar todas as operações
    lista_operacoes = sorted(chain(proventos_fii, operacoes_fii, operacoes_td, proventos_bh,  operacoes_bh, operacoes_t, operacoes_lc, operacoes_cdb_rdb, 
                                   operacoes_cri_cra, operacoes_debentures, operacoes_fundo_investimento),
                            key=attrgetter('data'))

	# Se não houver operações, retornar vazio
    if not lista_operacoes:
        data_anterior = str(calendar.timegm((datetime.date.today() - datetime.timedelta(days=365)).timetuple()) * 1000)
        data_atual = str(calendar.timegm(datetime.date.today().timetuple()) * 1000)
        return TemplateResponse(request, 'detalhamento_investimentos.html', {'graf_patrimonio': [[data_anterior, float(0)], [data_atual, float(0)]], 'patrimonio_anual': list(), 'estatisticas': list()})
    
    # Pegar ano da primeira operacao feita
    ano_corrente = lista_operacoes[0].data.year
    
    datas_finais_ano = set()
    # Adicionar datas finais de cada ano
    for ano in range(ano_corrente, datetime.date.today().year):
        ultima_operacao = Object()
        ultima_operacao.data = datetime.date(ano, 12, 31)
        datas_finais_ano.add(ultima_operacao)
        
    # Adicionar data atual
    data_atual = Object()
    data_atual.data = datetime.date.today()
    datas_finais_ano.add(data_atual)
    
    # Adicionar datas para estatísticas
    datas_estatisticas = set()
    # Dia anterior
    data_dia_anterior = Object()
    data_dia_anterior.data = datetime.date.today() + datetime.timedelta(days=-1)
    if data_dia_anterior.data >= lista_operacoes[0].data:
        data_dia_anterior.descricao = "1 dia"
        datas_estatisticas.add(data_dia_anterior)
    # 1 semana
    data_1_semana = Object()
    data_1_semana.data = datetime.date.today() + datetime.timedelta(days=-7)
    if data_1_semana.data >= lista_operacoes[0].data:
        data_1_semana.descricao = "7 dias"
        datas_estatisticas.add(data_1_semana)
    # 30 dias
    data_30_dias = Object()
    data_30_dias.data = datetime.date.today() + datetime.timedelta(days=-30)
    if data_30_dias.data >= lista_operacoes[0].data:
        data_30_dias.descricao = "30 dias"
        datas_estatisticas.add(data_30_dias)
    # 3 meses
    data_3_meses = Object()
    data_3_meses.data = datetime.date.today() + datetime.timedelta(days=-90)
    if data_3_meses.data >= lista_operacoes[0].data:
        data_3_meses.descricao = "3 meses"
        datas_estatisticas.add(data_3_meses)
    # 1 semestre
    data_1_semestre = Object()
    data_1_semestre.data = datetime.date.today() + datetime.timedelta(days=-180)
    if data_1_semestre.data >= lista_operacoes[0].data:
        data_1_semestre.descricao = "1 semestre"
        datas_estatisticas.add(data_1_semestre)
    # 1 ano
    data_1_ano = Object()
    data_1_ano.data = datetime.date.today() + datetime.timedelta(days=-365)
    if data_1_ano.data >= lista_operacoes[0].data:
        data_1_ano.descricao = "1 ano"
        datas_estatisticas.add(data_1_ano)
    
    lista_conjunta = sorted(chain(lista_operacoes, datas_finais_ano, datas_estatisticas),
                            key=attrgetter('data'))
    
    fii = {}
    acoes_bh = {}
    acoes_t = {}
    titulos_td = {}
    letras_credito = {}
    # Caso haja LC, preparar para o cálculo
    try:
        ultima_data_calculada_lc = operacoes_lc[0].data
    except:
        ultima_data_calculada_lc = datetime.date.today()
    cdb_rdb = {}
    # Caso haja CDB/RDB, preparar para o cálculo
    try:
        ultima_data_calculada_cdb_rdb = operacoes_cdb_rdb[0].data
    except:
        ultima_data_calculada_cdb_rdb = datetime.date.today()
    cri_cra = {}
    fundos_investimento = {}
    debentures = {}
    total_proventos_fii = 0
    total_proventos_bh = 0
    
    patrimonio = {}
    patrimonio_anual = list()
    graf_patrimonio = list()
    estatisticas = list()
    
    ############# TESTE
#     total_acoes_bh = datetime.timedelta(hours=0)
#     total_acoes_t = datetime.timedelta(hours=0)
#     total_prov_acoes_bh = datetime.timedelta(hours=0)
#     total_fii = datetime.timedelta(hours=0)
#     total_prov_fii = datetime.timedelta(hours=0)
#     total_td = datetime.timedelta(hours=0)
#     total_lc = datetime.timedelta(hours=0)
#     total_cdb_rdb = datetime.timedelta(hours=0)
#     total_cri_cra = datetime.timedelta(hours=0)
#     total_debentures = datetime.timedelta(hours=0)
#     total_fundo_investimento = datetime.timedelta(hours=0)
    ############# TESTE
    
    for index, item in enumerate(lista_conjunta):    
        # Atualizar lista de patrimonio atual ao trocar de ano
        if item.data.year != ano_corrente:
            if len(patrimonio_anual) > 0:
                diferenca = patrimonio['patrimonio_total'] - patrimonio_anual[len(patrimonio_anual) - 1][1]['patrimonio_total']
            else:
                diferenca = patrimonio['patrimonio_total']
            patrimonio_anual += [[str(ano_corrente).replace('.', ''), patrimonio, diferenca]]
            ano_corrente = item.data.year
        
        if isinstance(item, OperacaoAcao):
            if item.destinacao == 'B':
                if item.acao.ticker not in acoes_bh.keys():
                    acoes_bh[item.acao.ticker] = 0 
                if item.tipo_operacao == 'C':
                    acoes_bh[item.acao.ticker] += item.quantidade
                    if len(item.usoproventosoperacaoacao_set.all()) > 0:
                        total_proventos_bh -= item.qtd_proventos_utilizada()
                elif item.tipo_operacao == 'V':
                    acoes_bh[item.acao.ticker] -= item.quantidade
            
            elif item.destinacao == 'T':
                if item.acao.ticker not in acoes_t.keys():
                    acoes_t[item.acao.ticker] = 0 
                if item.tipo_operacao == 'C':
                    acoes_t[item.acao.ticker] += item.quantidade
#                     if len(item.usoproventosoperacaoacao_set.all()) > 0:
#                         total_proventos_t -= item.qtd_proventos_utilizada()
                elif item.tipo_operacao == 'V':
                    acoes_t[item.acao.ticker] -= item.quantidade
                
        elif isinstance(item, Provento):
            if item.data_pagamento <= datetime.date.today():
                if item.acao.ticker not in acoes_bh.keys():
                    acoes_bh[item.acao.ticker] = 0 
                if item.tipo_provento in ['D', 'J']:
                    total_recebido = acoes_bh[item.acao.ticker] * item.valor_unitario
                    if item.tipo_provento == 'J':
                        total_recebido = total_recebido * Decimal(0.85)
                    total_proventos_bh += total_recebido
                elif item.tipo_provento == 'A':
                    provento_acao = item.acaoprovento_set.all()[0]
                    if provento_acao.acao_recebida.ticker not in acoes_bh.keys():
                        acoes_bh[provento_acao.acao_recebida.ticker] = 0
                    acoes_recebidas = int((acoes_bh[item.acao.ticker] * item.valor_unitario ) / 100 )
                    acoes_bh[provento_acao.acao_recebida.ticker] += acoes_recebidas
                    if provento_acao.valor_calculo_frac > 0:
                        if provento_acao.data_pagamento_frac <= datetime.date.today():
                            total_proventos_bh += (((acoes_bh[item.acao.ticker] * item.valor_unitario ) / 100 ) % 1 * provento_acao.valor_calculo_frac)
                
        elif isinstance(item, OperacaoTitulo):  
            if item.titulo not in titulos_td.keys():
                titulos_td[item.titulo] = 0
            if item.tipo_operacao == 'C':
                titulos_td[item.titulo] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                titulos_td[item.titulo] -= item.quantidade
                
        elif isinstance(item, OperacaoFII):
            if item.fii.ticker not in fii.keys():
                fii[item.fii.ticker] = 0    
            if item.tipo_operacao == 'C':
                fii[item.fii.ticker] += item.quantidade
                if len(item.usoproventosoperacaofii_set.all()) > 0:
                    total_proventos_fii -= float(item.usoproventosoperacaofii_set.all()[0].qtd_utilizada)
                
            elif item.tipo_operacao == 'V':
                fii[item.fii.ticker] -= item.quantidade
                
        elif isinstance(item, ProventoFII):
            if item.fii.ticker not in fii.keys():
                fii[item.fii.ticker] = 0    
            item.total = math.floor(fii[item.fii.ticker] * item.valor_unitario * 100) / 100
            total_proventos_fii += item.total
                
        elif isinstance(item, OperacaoLetraCredito):
            if item.tipo_operacao == 'C':
                letras_credito[item.id] = item
                
            elif item.tipo_operacao == 'V':
                if item.quantidade == item.operacao_compra_relacionada().qtd_disponivel_venda_na_data(item.data):
                    del letras_credito[item.operacao_compra_relacionada().id]
                else:
                    letras_credito[item.operacao_compra_relacionada().id].quantidade -= letras_credito[item.operacao_compra_relacionada().id].quantidade * item.quantidade / item.operacao_compra_relacionada().quantidade
                    
        elif isinstance(item, OperacaoCDB_RDB):
            if item.tipo_operacao == 'C':
                cdb_rdb[item.id] = item
                
            elif item.tipo_operacao == 'V':
                if item.quantidade == item.operacao_compra_relacionada().qtd_disponivel_venda_na_data(item.data):
                    del cdb_rdb[item.operacao_compra_relacionada().id]
                else:
                    cdb_rdb[item.operacao_compra_relacionada().id].quantidade -= cdb_rdb[item.operacao_compra_relacionada().id].quantidade * item.quantidade / item.operacao_compra_relacionada().quantidade
                    
        elif isinstance(item, OperacaoCRI_CRA):
            if item.cri_cra not in cri_cra.keys():
                cri_cra[item.cri_cra] = 0    
            if item.tipo_operacao == 'C':
                cri_cra[item.cri_cra] += item.quantidade 
                
            elif item.tipo_operacao == 'V':
                cri_cra[item.cri_cra] -= item.quantidade 
            
        elif isinstance(item, OperacaoDebenture):
            if item.debenture not in debentures.keys():
                debentures[item.debenture] = 0    
            if item.tipo_operacao == 'C':
                debentures[item.debenture] += item.quantidade 
                
            elif item.tipo_operacao == 'V':
                debentures[item.debenture] -= item.quantidade 
                
        elif isinstance(item, OperacaoFundoInvestimento):
            if item.fundo_investimento not in fundos_investimento.keys():
                fundos_investimento[item.fundo_investimento] = 0    
            if item.tipo_operacao == 'C':
                fundos_investimento[item.fundo_investimento] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                fundos_investimento[item.fundo_investimento] -= item.quantidade

        # Se não cair em nenhum dos anteriores: item vazio
        
        # Se última operação feita no dia, calcular patrimonio
        if index == len(lista_conjunta)-1 or item.data < lista_conjunta[index+1].data:
            patrimonio = {}
            patrimonio['patrimonio_total'] = 0
    
            # Rodar calculo de patrimonio
            # Acoes (B&H)
#             inicio_acoes_bh = datetime.datetime.now()
            patrimonio['Ações (Buy and Hold)'] = 0
            periodo_1_ano = item.data - datetime.timedelta(days=365)
            for acao, quantidade in acoes_bh.items():
                if quantidade > 0:
                    # Verifica se valor foi preenchido com valor mais atual (válido apenas para data atual)
                    preenchido = False
                    if item.data == datetime.date.today():
                        try:
                            valor_diario_mais_recente = ValorDiarioAcao.objects.filter(acao__ticker=acao).order_by('-data_hora')
                            if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
                                valor_acao = valor_diario_mais_recente[0].preco_unitario
                                preenchido = True
                        except:
                            preenchido = False
                    if (not preenchido):
                        # Pegar último dia util com negociação da ação para calculo do patrimonio
                        valor_acao = HistoricoAcao.objects.filter(acao__ticker=acao, data__range=[periodo_1_ano, item.data]).order_by('-data')[0].preco_unitario
                    patrimonio['Ações (Buy and Hold)'] += (valor_acao * quantidade)
            patrimonio['patrimonio_total'] += patrimonio['Ações (Buy and Hold)'] 
#             fim_acoes_bh = datetime.datetime.now()
#             total_acoes_bh += fim_acoes - inicio_acoes_bh
            
            # Proventos Acoes
#             inicio_prov_acoes = datetime.datetime.now()
            patrimonio['Proventos Ações'] = Decimal(int(total_proventos_bh * 100) / Decimal(100))
            patrimonio['patrimonio_total'] += patrimonio['Proventos Ações']
#             fim_prov_acoes_bh = datetime.datetime.now()
#             total_prov_acoes_bh += fim_prov_acoes - inicio_prov_acoes_bh
            
            # Acoes (Trading)
#             inicio_acoes_t = datetime.datetime.now()
            patrimonio['Ações (Trading)'] = 0
            periodo_1_ano = item.data - datetime.timedelta(days=365)
            for acao, quantidade in acoes_t.items():
                if quantidade > 0:
                    # Verifica se valor foi preenchido com valor mais atual (válido apenas para data atual)
                    preenchido = False
                    if item.data == datetime.date.today():
                        try:
                            valor_diario_mais_recente = ValorDiarioAcao.objects.filter(acao__ticker=acao).order_by('-data_hora')
                            if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
                                valor_acao = valor_diario_mais_recente[0].preco_unitario
                                preenchido = True
                        except:
                            preenchido = False
                    if (not preenchido):
                        # Pegar último dia util com negociação da ação para calculo do patrimonio
                        valor_acao = HistoricoAcao.objects.filter(acao__ticker=acao, data__range=[periodo_1_ano, item.data]).order_by('-data')[0].preco_unitario
                    patrimonio['Ações (Trading)'] += (valor_acao * quantidade)
            patrimonio['patrimonio_total'] += patrimonio['Ações (Trading)'] 
#             fim_acoes_t = datetime.datetime.now()
#             total_acoes_t += fim_acoes - inicio_acoes_t
            
            # TD
#             inicio_td = datetime.datetime.now()
            patrimonio['Tesouro Direto'] = 0
            for titulo in titulos_td.keys():
                if item.data is not datetime.date.today():
                    ultimo_dia_util = item.data
                    while not HistoricoTitulo.objects.filter(data=ultimo_dia_util, titulo=titulo):
                        ultimo_dia_util -= datetime.timedelta(days=1)
                    patrimonio['Tesouro Direto'] += (titulos_td[titulo] * HistoricoTitulo.objects.get(data=ultimo_dia_util, titulo=titulo).preco_venda)
                else:
                    # Buscar valor mais atual de valor diário, se existir
                    if ValorDiarioTitulo.objects.filter(titulo=titulo, data_hora__date=datetime.date.today()).order_by('-data_hora'):
                        valor_diario = ValorDiarioTitulo.objects.filter(titulo=titulo, data_hora__date=datetime.date.today()).order_by('-data_hora')[0]
                        patrimonio['Tesouro Direto'] += (titulos_td[titulo] * valor_diario.preco_venda)
                        break
                    else:
                        # Se não há valor diário, buscar histórico mais atual mesmo
                        patrimonio['Tesouro Direto'] += (titulos_td[titulo] * HistoricoTitulo.objects.filter(titulo=titulo).order_by('-data')[0].preco_venda)
            patrimonio['patrimonio_total'] += patrimonio['Tesouro Direto'] 
#             fim_td = datetime.datetime.now()
#             total_td += fim_td - inicio_td
                
            # FII
#             inicio_fii = datetime.datetime.now()
            patrimonio['FII'] = 0
            periodo_1_ano = item.data - datetime.timedelta(days=365)
            for papel, quantidade in fii.items():
                # Verifica se valor foi preenchido com valor mais atual (válido apenas para data atual)
                preenchido = False
                if item.data == datetime.date.today():
                    try:
                        valor_diario_mais_recente = ValorDiarioFII.objects.filter(fii__ticker=papel).order_by('-data_hora')
                        if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
                            valor_fii = valor_diario_mais_recente[0].preco_unitario
                            preenchido = True
                    except:
                        preenchido = False
                if (not preenchido):
                    # Pegar último dia util com negociação da ação para calculo do patrimonio
                    valor_fii = HistoricoFII.objects.filter(fii__ticker=papel, data__range=[periodo_1_ano, item.data]).order_by('-data')[0].preco_unitario
                patrimonio['FII'] += (quantidade * valor_fii)
            patrimonio['patrimonio_total'] += patrimonio['FII']  
#             fim_fii = datetime.datetime.now()
#             total_fii += fim_fii - inicio_fii
                    
            # Proventos FII
#             inicio_prov_fii = datetime.datetime.now()
            patrimonio['Proventos FII'] = Decimal(int(total_proventos_fii * 100) / Decimal(100))
            patrimonio['patrimonio_total'] += patrimonio['Proventos FII'] 
#             fim_prov_fii = datetime.datetime.now()
#             total_prov_fii += fim_prov_fii - inicio_prov_fii
            
            # LC
#             inicio_lc = datetime.datetime.now()
            patrimonio_lc = 0
            # Rodar calculo com as datas desde o último calculo, com 1 dia de atraso pois a atualização é a do dia anterior
            dia_anterior = item.data - datetime.timedelta(days=1)
            if item.data > ultima_data_calculada_lc:
                # Retira a data limite (item.data) do cálculo
                taxas = HistoricoTaxaDI.objects.filter(data__range=[ultima_data_calculada_lc, dia_anterior]).values('taxa').annotate(qtd_dias=Count('taxa'))
                taxas_dos_dias = {}
                for taxa in taxas:
                    taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
                for operacao_id, operacao in letras_credito.items():
                    if operacao.data < item.data:
                        operacao.quantidade = calcular_valor_atualizado_com_taxas(taxas_dos_dias, operacao.quantidade, OperacaoLetraCredito.objects.get(id=operacao_id).porcentagem_di())
                # Guardar ultima data de calculo
                ultima_data_calculada_lc = item.data
            for letra_credito in letras_credito.values():
                patrimonio_lc += letra_credito.quantidade.quantize(Decimal('.01'), ROUND_DOWN)
            patrimonio['Letras de Crédito'] = patrimonio_lc
            patrimonio['patrimonio_total'] += patrimonio['Letras de Crédito'] 
#             fim_lc = datetime.datetime.now()
#             total_lc += fim_lc - inicio_lc
            
            # CDB/RDB
#             inicio_cdb_rdb = datetime.datetime.now()
            patrimonio_cdb_rdb = 0
            # Rodar calculo com as datas desde o último calculo, com 1 dia de atraso pois a atualização é a do dia anterior
            dia_anterior = item.data - datetime.timedelta(days=1)
            if item.data > ultima_data_calculada_cdb_rdb:
                # Retira a data limite (item.data) do cálculo
                taxas = HistoricoTaxaDI.objects.filter(data__range=[ultima_data_calculada_cdb_rdb, dia_anterior]).values('taxa').annotate(qtd_dias=Count('taxa'))
                taxas_dos_dias = {}
                for taxa in taxas:
                    taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
                for operacao_id, operacao in cdb_rdb.items():
                    if operacao.data < item.data:
                        operacao.quantidade = calcular_valor_atualizado_com_taxas(taxas_dos_dias, operacao.quantidade, OperacaoCDB_RDB.objects.get(id=operacao_id).porcentagem())
                # Guardar ultima data de calculo
                ultima_data_calculada_cdb_rdb = item.data
            for investimento in cdb_rdb.values():
                patrimonio_cdb_rdb += investimento.quantidade.quantize(Decimal('.01'), ROUND_DOWN)
            patrimonio['CDB/RDB'] = patrimonio_cdb_rdb
            patrimonio['patrimonio_total'] += patrimonio['CDB/RDB'] 
#             fim_cdb_rdb = datetime.datetime.now()
#             total_cdb_rdb += fim_cdb_rdb - inicio_cdb_rdb

            # CRI/CRA
#             inicio_cri_cra = datetime.datetime.now()
            patrimonio_cri_cra = 0
            for certificado in cri_cra.keys():
                patrimonio_cri_cra += cri_cra[certificado] * calcular_valor_um_cri_cra_na_data(certificado, item.data)
            patrimonio['CRI/CRA'] = patrimonio_cri_cra
            patrimonio['patrimonio_total'] += patrimonio['CRI/CRA'] 
#             fim_cri_cra = datetime.datetime.now()
#             total_cri_cra += fim_cri_cra - inicio_cri_cra

            # Debênture
#             inicio_debentures = datetime.datetime.now()
            patrimonio_debentures = 0
            for debenture in debentures.keys():
                historico_fundo = HistoricoValorDebenture.objects.filter(debenture=debenture, data__lte=item.data).order_by('-data')[0]
                patrimonio_debentures += debentures[debenture] * historico_fundo.valor_total()
            patrimonio['Debêntures'] = patrimonio_debentures
            patrimonio['patrimonio_total'] += patrimonio['Debêntures'] 
#             fim_debentures = datetime.datetime.now()
#             total_debentures += fim_debentures - inicio_debentures

            # Fundo de investimento
#             inicio_fundo_investimento = datetime.datetime.now()
            patrimonio_fundo_investimento = 0
            for fundo in fundos_investimento.keys():
                historico_fundo = HistoricoValorCotas.objects.filter(fundo_investimento=fundo, data__lte=item.data).order_by('-data')
                ultima_operacao_fundo = OperacaoFundoInvestimento.objects.filter(data__lte=item.data, fundo_investimento=fundo).order_by('-data')[0]
                if historico_fundo and historico_fundo[0].data > ultima_operacao_fundo.data:
                    patrimonio_fundo_investimento += fundos_investimento[fundo] * historico_fundo[0].valor_cota
                else:
                    patrimonio_fundo_investimento += fundos_investimento[fundo] * ultima_operacao_fundo.valor_cota()
            patrimonio['Fundo de Inv.'] = patrimonio_fundo_investimento
            patrimonio['patrimonio_total'] += patrimonio['Fundo de Inv.'] 
#             fim_fundo_investimento = datetime.datetime.now()
#             total_fundo_investimento += fim_fundo_investimento - inicio_fundo_investimento
            
            
#             print 'Ações (B&H)          ', total_acoes_bh
#             print 'Ações (Trading)      ', total_acoes_t
#             print 'Prov. Ações          ', total_prov_acoes_bh
#             print 'TD                   ', total_td
#             print 'FII                  ', total_fii
#             print 'Prov. FII            ', total_prov_fii
#             print 'LC                   ', total_lc
#             print 'CDB/RDB              ', total_cdb_rdb
#             print 'CRI/CRA              ', total_cri_cra
#             print 'Debêntures           ', total_debentures
#             print 'Fundo Inv.           ', total_fundo_investimento
            
            # Preparar estatísticas
            for data_estatistica in datas_estatisticas:
                if item.data == data_estatistica.data: 
                    if len(estatisticas) > 0 and estatisticas[len(estatisticas)-1][0] == data_estatistica.descricao:
                        estatisticas[len(estatisticas)-1] = [data_estatistica.descricao, float(patrimonio['patrimonio_total'])]
                    else:
                        estatisticas += [[data_estatistica.descricao, float(patrimonio['patrimonio_total'])]]
                 
            # Preparar data
            data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
            # Verifica se altera ultima posicao do grafico ou adiciona novo registro
            if len(graf_patrimonio) > 0 and graf_patrimonio[len(graf_patrimonio)-1][0] == data_formatada:
                graf_patrimonio[len(graf_patrimonio)-1][1] = float(patrimonio['patrimonio_total'])
            else:
                graf_patrimonio += [[data_formatada, float(patrimonio['patrimonio_total'])]]
            
    # Adicionar ultimo valor ao dicionario de patrimonio anual
    if len(patrimonio_anual) > 0:
        diferenca = patrimonio['patrimonio_total'] - patrimonio_anual[len(patrimonio_anual) - 1][1]['patrimonio_total']
    else:
        diferenca = patrimonio['patrimonio_total']
    patrimonio_anual += [[str(ano_corrente).replace('.', ''), patrimonio, diferenca]]
    
    # Terminar estatísticas
    for index, estatistica in enumerate(estatisticas):
        estatisticas[index] = [estatistica[0], float(patrimonio['patrimonio_total']) - estatistica[1]]
    
#     print 'Ações (B&H):      ', total_acoes_bh
#     print 'Ações (Trading):  ', total_acoes_t
#     print 'Prov. ações:      ', total_prov_acoes_bh
#     print 'FII:              ', total_fii 
#     print 'Prov. FII:        ', total_prov_fii 
#     print 'TD:               ', total_td 
#     print 'LC:               ', total_lc 
#     print 'CDB/RDB:          ', total_cdb_rdb
#     print 'CRI/CRA:          ', total_cri_cra
#     print 'Debêntures:       ', total_debentures
#     print 'Fundo Inv.:       ', total_fundo_investimento
    
    return TemplateResponse(request, 'detalhamento_investimentos.html', {'graf_patrimonio': graf_patrimonio, 'patrimonio_anual': patrimonio_anual,
                                            'estatisticas': estatisticas})

def sobre(request):
    return TemplateResponse(request, 'sobre.html', {})