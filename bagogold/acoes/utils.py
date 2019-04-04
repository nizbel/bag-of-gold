# -*- coding: utf-8 -*-
import calendar
import datetime
from decimal import Decimal
from itertools import chain
from operator import attrgetter
import re
from urllib2 import Request, urlopen, HTTPError, URLError

from django.db.models import Sum, Case, When, IntegerField, F
from django.db.models.expressions import Value
from django.db.models.fields import DecimalField, CharField
from django.db.models.query_utils import Q
import mechanize

from bagogold.acoes.models import EventoAlteracaoAcao, EventoBonusAcao, \
    EventoAcao, CheckpointAcao, ProventoAcao, EventoAgrupamentoAcao, \
    EventoDesdobramentoAcao, EventoBonusAcaoRecebida
from bagogold.acoes.models import UsoProventosOperacaoAcao, \
    OperacaoAcao, AcaoProvento, ProventoAcao
from bagogold.bagogold.models.divisoes import DivisaoOperacaoAcao
from bagogold.bagogold.models.empresa import Empresa


def calcular_operacoes_sem_proventos_por_mes(investidor, operacoes, data_inicio=None, data_fim=None):
    """ 
    Calcula a quantidade investida em compras de ações sem usar proventos por mes
    
    Parâmetros: Investidor
                Queryset de operações ordenadas por data
                Data de início do período
                Data de fim do período
    Retorno: Lista de tuplas (data, quantidade)
    """
    lista_ids_operacoes = list(UsoProventosOperacaoAcao.objects.filter(operacao__investidor=investidor).values_list('operacao', flat=True).distinct())

    # Filtrar período
    if data_inicio:
        operacoes = operacoes.filter(data__gte=data_inicio)
    if data_fim:
        operacoes = operacoes.filter(data__lte=data_fim)
    
    anos_meses = list()
    for operacao in operacoes:
        ano_mes = (operacao.data.month, operacao.data.year)
        if ano_mes not in anos_meses:
            anos_meses.append(ano_mes)

    graf_gasto_op_sem_prov_mes = list()    
    for mes, ano in anos_meses:
        operacoes_mes = operacoes.filter(data__month=mes, data__year=ano)
        total_mes = 0
        for operacao in operacoes_mes:                      
            if operacao.id not in lista_ids_operacoes:  
#                 print 'Sem uso de proventos'
                total_mes += (operacao.quantidade * operacao.preco_unitario + \
                operacao.emolumentos + operacao.corretagem)
            else:
                qtd_usada = operacao.qtd_proventos_utilizada()
#                 print 'Com uso de proventos: %s' % (qtd_usada)
                total_mes += (operacao.quantidade * operacao.preco_unitario + \
                operacao.emolumentos + operacao.corretagem) - qtd_usada
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 18).timetuple()) * 1000)
        graf_gasto_op_sem_prov_mes += [[data_formatada, float(total_mes)]]
        
    return graf_gasto_op_sem_prov_mes

def calcular_uso_proventos_por_mes(investidor, data_inicio=None, data_fim=None):
    """ 
    Calcula a quantidade de uso de proventos em operações por mes
    
    Parâmetros: Investidor
                Data de início do período
                Data de fim do período
    Retorno: Lista de tuplas (data, quantidade)
    """
    lista_ids_operacoes = list(UsoProventosOperacaoAcao.objects.filter(operacao__investidor=investidor).values_list('operacao', flat=True).distinct())
    
    # Guarda as operações que tiveram uso de proventos
    operacoes = OperacaoAcao.objects.filter(id__in=lista_ids_operacoes)
    
    # Filtrar período
    if data_inicio:
        operacoes = operacoes.filter(data__gte=data_inicio)
    if data_fim:
        operacoes = operacoes.filter(data__lte=data_fim)
    
    anos_meses = list()
    for operacao in operacoes:
        ano_mes = (operacao.data.month, operacao.data.year)
        if ano_mes not in anos_meses:
            anos_meses.append(ano_mes)
    
    graf_uso_proventos_mes = list()
    for mes, ano in anos_meses:
        operacoes_mes = operacoes.filter(data__month=mes, data__year=ano)
        total_mes = 0
        for operacao in operacoes_mes:                      
            total_mes += operacao.qtd_proventos_utilizada()
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 12).timetuple()) * 1000)
        graf_uso_proventos_mes += [[data_formatada, float(total_mes)]]
        
    return graf_uso_proventos_mes

def calcular_media_uso_proventos_6_meses(investidor, data_inicio=None, data_fim=None):
    """ 
    Calcula a média de uso de proventos em operações nos últimos 6 meses
    
    Parâmetros: Investidor
    Retorno: Lista de tuplas (data, quantidade)
    """
    ultimos_6_meses = list()
    lista_ids_operacoes = list()
    usos_proventos = UsoProventosOperacaoAcao.objects.filter(operacao__investidor=investidor)
    for uso_proventos in usos_proventos:
        lista_ids_operacoes.append(uso_proventos.operacao.id)
    
    # Guarda as operações que tiveram uso de proventos
    operacoes = OperacaoAcao.objects.filter(id__in=lista_ids_operacoes)
    
    anos_meses = list()
    for operacao in operacoes:
        ano_mes = (operacao.data.month, operacao.data.year)
        if ano_mes not in anos_meses:
            anos_meses.append(ano_mes)
    
    graf_uso_proventos_mes = list()
    for mes, ano in anos_meses:
        operacoes_mes = operacoes.filter(data__month=mes, data__year=ano)
        total_mes = 0
        for operacao in operacoes_mes:                      
            total_mes += usos_proventos.get(operacao__id=operacao.id).qtd_utilizada
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 15).timetuple()) * 1000)
        # Adicionar a lista de valores e calcular a media
        ultimos_6_meses.append(total_mes)
        if len(ultimos_6_meses) > 6:
            ultimos_6_meses.pop(0)
        media_6_meses = 0
        for valor in ultimos_6_meses:
            media_6_meses += valor
        graf_uso_proventos_mes += [[data_formatada, float(media_6_meses/6)]]
        
    return graf_uso_proventos_mes
    
def calcular_provento_por_mes(investidor, proventos, operacoes, data_inicio=None, data_fim=None):
    """ 
    Calcula a quantidade de proventos em dinheiro recebido por mes
    
    Parâmetros: Investidor
                Queryset de proventos ordenados por data
                Queryset de operações ordenadas por data
                Data de início do período
                Data de fim do período
    Retorno: Lista de tuplas (data, quantidade)
    """
    # Filtrar período
    if data_inicio:
        operacoes = operacoes.filter(data__gte=data_inicio)
        proventos = proventos.filter(data_ex__gte=data_inicio)
    if data_fim:
        operacoes = operacoes.filter(data__lte=data_fim)
        proventos = proventos.filter(data_ex__lte=data_fim)
        
    anos_meses = list()
    for provento in proventos:
        ano_mes = (provento.data_ex.month, provento.data_ex.year)
        if ano_mes not in anos_meses:
            anos_meses.append(ano_mes)
    
    # Adicionar mes atual caso não tenha sido adicionado
    if (datetime.date.today().month, datetime.date.today().year) not in anos_meses:
        anos_meses.append((datetime.date.today().month, datetime.date.today().year))

    graf_proventos_mes = list()    
    for mes, ano in anos_meses:
#         print '%s %s' % (mes, ano)
        proventos_mes = proventos.filter(data_ex__month=mes, data_ex__year=ano)
        total_mes_div = 0
        total_mes_jscp = 0
        for provento in proventos_mes:                        
#             qtd_acoes = operacoes.filter(acao=provento.acao, data__lt=provento.data_ex).aggregate(qtd_acoes=Sum(
#                         Case(When(tipo_operacao='C', then=F('quantidade')), When(tipo_operacao='V', then=(F('quantidade')*-1)),
#                               output_field=IntegerField())))['qtd_acoes']
            qtd_acoes = calcular_qtd_acoes_ate_dia_por_ticker(investidor, provento.acao.ticker, provento.data_ex - datetime.timedelta(days=1))
            # TODO adicionar frações de proventos em ações
            if provento.tipo_provento == 'D':
                total_mes_div += qtd_acoes * provento.valor_unitario
            elif provento.tipo_provento == 'J':
                total_mes_jscp += qtd_acoes * provento.valor_unitario * Decimal(0.85)
        data_formatada = str(calendar.timegm(datetime.date(ano, mes, 12).timetuple()) * 1000)
        graf_proventos_mes += [[data_formatada, float(total_mes_div), float(total_mes_jscp)]]
        
    return graf_proventos_mes

def calcular_media_proventos_6_meses(investidor, proventos, operacoes, data_inicio=None, data_fim=None):
    """ 
    Calcula a média de proventos recebida nos últimos 6 meses
    
    Parâmetros: Investidor
                Queryset de proventos ordenados por data
                Queryset de operações ordenadas por data
                Data de início do período
                Data de fim do período
    Retorno: Lista de tuplas (data, quantidade)
    """
    # Filtrar período
    if data_inicio:
        # Data de início levada para 6 meses atrás para verificar a média
        data_inicio = (data_inicio - datetime.timedelta(days=30 * 6)).replace(day=1)
        operacoes = operacoes.filter(data__gte=data_inicio)
        proventos = proventos.filter(data_ex__gte=data_inicio)
    if data_fim:
        operacoes = operacoes.filter(data__lte=data_fim)
        proventos = proventos.filter(data_ex__lte=data_fim)
        
    # Verifica se há proventos a serem calculados
    if not proventos:
        return list()
    
    ultimos_6_meses = list()
    meses_anos = list()
    # Primeiro valor de mes_ano é o primeiro mês em que foi recebido algum provento
    mes_ano = (proventos[0].data_ex.month, proventos[0].data_ex.year)
    meses_anos.append(mes_ano)
    while mes_ano[0] != datetime.date.today().month or mes_ano[1] != datetime.date.today().year:
        mes_ano = (mes_ano[0] + 1, mes_ano[1])
        if mes_ano[0] > 12:
            mes_ano = (1, mes_ano[1] + 1)
        meses_anos.append(mes_ano)

    graf_proventos_mes = list()    
    for mes, ano in meses_anos:
#         print '%s %s' % (mes, ano)
        proventos_mes = proventos.filter(data_ex__month=mes, data_ex__year=ano)
        total_mes = 0
        for provento in proventos_mes:                        
#             qtd_acoes = operacoes.filter(acao=provento.acao, data__lt=provento.data_ex).aggregate(qtd_acoes=Sum(
#                         Case(When(tipo_operacao='C', then=F('quantidade')), When(tipo_operacao='V', then=(F('quantidade')*-1)),
#                               output_field=IntegerField())))['qtd_acoes']
            qtd_acoes = calcular_qtd_acoes_ate_dia_por_ticker(investidor, provento.acao.ticker, provento.data_ex - datetime.timedelta(days=1))
            if provento.tipo_provento == 'D':
                total_mes += qtd_acoes * provento.valor_unitario
            elif provento.tipo_provento == 'J':
                total_mes += qtd_acoes * provento.valor_unitario * Decimal(0.85)
#         print total_mes
        # Adicionar a lista de valores e calcular a media
        ultimos_6_meses.append(total_mes)
        if len(ultimos_6_meses) > 6:
            ultimos_6_meses.pop(0)
        
        # Verifica se filtro de data está valendo
        if not data_inicio or (ano - data_inicio.year) * 12 + mes - data_inicio.month >= 6:
            # Somar valores guardados
            media_6_meses = sum(ultimos_6_meses)
            
            data_formatada = str(calendar.timegm(datetime.date(ano, mes, 18).timetuple()) * 1000)
    
            graf_proventos_mes += [[data_formatada, float(media_6_meses/6)]]
        
    return graf_proventos_mes

def calcular_lucro_trade_ate_data(investidor, data):
    """
    Calcula o lucro acumulado em trades até a data especificada
    
    Parâmetros: Investidor
                Data
    Retorno: Lucro/Prejuízo
    """
    trades = OperacaoAcao.objects.exclude(data__isnull=True).filter(investidor=investidor, tipo_operacao='V', destinacao='T', data__lt=data).order_by('data')
    lucro_acumulado = 0
    
    for operacao in trades:
        venda_com_taxas = operacao.quantidade * operacao.preco_unitario - operacao.emolumentos - operacao.corretagem
        
        # Calcular lucro bruto da operação de venda
        # Pegar operações de compra
        # TODO PREPARAR CASO DE MUITAS COMPRAS PARA MUITAS VENDAS
        qtd_compra = 0
        gasto_total_compras = 0
        for operacao_compra in operacao.venda.get_queryset().order_by('compra__preco_unitario'):
            qtd_compra += min(operacao_compra.compra.quantidade, operacao.quantidade)
            # TODO NAO PREVÊ MUITAS COMPRAS PARA MUITAS VENDAS
            gasto_total_compras += (qtd_compra * operacao_compra.compra.preco_unitario + operacao_compra.compra.emolumentos + \
                                    operacao_compra.compra.corretagem)
        
        lucro_bruto_venda = (operacao.quantidade * operacao.preco_unitario - operacao.corretagem - operacao.emolumentos) - \
            gasto_total_compras
        lucro_acumulado += lucro_bruto_venda
        
    return lucro_acumulado

def calcular_qtd_acoes_ate_dia(investidor, dia=None):
    """ 
    Calcula a quantidade de ações até dia determinado
    
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de ações {ticker: qtd}
    """
    # TODO implementar
    return

#     # Preparar data
#     if data == None:
#         data = datetime.date.today()
#         
#     if destinacao not in ['', 'B', 'T']:
#         raise ValueError
#     # Buscar proventos em ações
#     acoes_operadas = OperacaoAcao.objects.filter(investidor=investidor, data__lte=data).values_list('acao', flat=True) if destinacao == '' \
#             else OperacaoAcao.objects.filter(investidor=investidor, data__lte=data, destinacao=destinacao).values_list('acao', flat=True)
#     
#     # Remover ações repetidas
#     acoes_operadas = list(set(acoes_operadas))
#     
#     proventos_em_acoes = list(set(AcaoProvento.objects.filter(provento__acao__in=acoes_operadas, provento__data_pagamento__lte=data) \
#                                   .values_list('acao_recebida', flat=True)))
#     
#     # Adicionar ações recebidas pelo investidor
#     acoes_investidor = list(set(acoes_operadas + proventos_em_acoes))
#     
#     return acoes_investidor



def calcular_qtd_acoes_ate_dia_por_ticker(investidor, ticker, dia, destinacao=OperacaoAcao.DESTINACAO_BH, ignorar_alteracao_id=None, verificar_evento=True):
    """ 
    Calcula a quantidade de ações até dia determinado
    
    Parâmetros: Investidor
                Ticker da ação
                Dia final
                Levar trades em consideração
                ID de alteração a ser ignorada
                Verificar se houve evento para ação no período?
    Retorno: Quantidade de ações
    """
#     if considerar_trade:
#         operacoes = OperacaoAcao.objects.filter(investidor=investidor, acao__ticker=ticker, data__lte=dia).exclude(data__isnull=True).order_by('data')
#     else:
#         operacoes = OperacaoAcao.objects.filter(investidor=investidor, destinacao='B', acao__ticker=ticker, data__lte=dia).exclude(data__isnull=True).order_by('data')
#     # Pega os proventos em ações recebidos por outras ações
#     proventos_em_acoes = AcaoProvento.objects.filter(provento__oficial_bovespa=True, acao_recebida__ticker=ticker, provento__data_ex__lte=dia).exclude(provento__data_ex__isnull=True) \
#         .annotate(acao_ticker=F('provento__acao__ticker')).annotate(data=F('provento__data_ex')).order_by('data').select_related('provento')
# #     for provento in proventos_em_acoes:
# #         provento.data = provento.provento.data_ex
#     
#     lista_conjunta = sorted(chain(proventos_em_acoes, operacoes), key=attrgetter('data'))
#     
#     qtd_acoes = 0
#     
#     for item in lista_conjunta:
#         if isinstance(item, OperacaoAcao): 
#             # Verificar se se trata de compra ou venda
#             if item.tipo_operacao == 'C':
#                 qtd_acoes += item.quantidade
#                 
#             elif item.tipo_operacao == 'V':
#                 qtd_acoes -= item.quantidade
#         
#         elif isinstance(item, AcaoProvento): 
#             if item.acao_ticker == ticker:
#                 qtd_acoes += int(item.provento.valor_unitario * qtd_acoes / 100)
#             else:
#                 qtd_acoes += int(item.provento.valor_unitario * calcular_qtd_acoes_ate_dia_por_ticker(investidor, item.acao_ticker, item.data, considerar_trade, ignorar_alteracao_id) / 100)
    
    if verificar_evento and not verificar_se_existe_evento_para_acao_periodo(ticker, dia.replace(month=1).replace(day=1), dia):
        if destinacao == 0:
            if CheckpointAcao.objects.filter(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, quantidade__gt=0).exists():
                qtd_acoes = CheckpointAcao.objects.filter(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, quantidade__gt=0).aggregate(qtd_final=Sum('quantidade'))['quantidade']
            else:
                qtd_acoes = 0
            qtd_acoes += (OperacaoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia], investidor=investidor).exclude(data__isnull=True) \
                .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                                          When(tipo_operacao='V', then=F('quantidade')*-1),
                                          output_field=DecimalField())))['total'] or 0)
            
        else:
            if CheckpointAcao.objects.filter(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, quantidade__gt=0, destinacao=destinacao).exists():
                qtd_acoes = CheckpointAcao.objects.get(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, quantidade__gt=0, destinacao=destinacao).quantidade
            else:
                qtd_acoes = 0
            qtd_acoes += (OperacaoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia], investidor=investidor, destinacao=destinacao)
                          .exclude(data__isnull=True).aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                                          When(tipo_operacao='V', then=F('quantidade')*-1),
                                          output_field=DecimalField())))['total'] or 0)
            
    else:
        if destinacao == 0:
            if CheckpointAcao.objects.filter(investidor=investidor, ano=dia.year-1, acao__ticker=ticker).exists():
                qtd_acoes = CheckpointAcao.objects.filter(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, quantidade__gt=0).aggregate(qtd_final=Sum('quantidade'))['quantidade']
            else:
                qtd_acoes = 0
            operacoes = OperacaoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia], investidor=investidor).exclude(data__isnull=True) \
                .annotate(qtd_final=(Case(When(tipo_operacao='C', then=F('quantidade')),
                                          When(tipo_operacao='V', then=F('quantidade')*-1),
                                          output_field=DecimalField()))).annotate(tipo=Value(u'Operação', output_field=CharField())).select_related('acao')
        else:
            if CheckpointAcao.objects.filter(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, destinacao=destinacao).exists():
                qtd_acoes = CheckpointAcao.objects.get(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, destinacao=destinacao).quantidade
            else:
                qtd_acoes = 0
            operacoes = OperacaoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia], investidor=investidor, destinacao=destinacao) \
                .exclude(data__isnull=True).annotate(qtd_final=(Case(When(tipo_operacao='C', then=F('quantidade')),
                                          When(tipo_operacao='V', then=F('quantidade')*-1),
                                          output_field=DecimalField()))).annotate(tipo=Value(u'Operação', output_field=CharField())).select_related('acao')
                                      
                                      
        # Verificar agrupamentos e desdobramentos
        agrupamentos = EventoAgrupamentoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]) \
            .annotate(tipo=Value(u'Agrupamento', output_field=CharField())).select_related('acao')

        desdobramentos = EventoDesdobramentoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]) \
            .annotate(tipo=Value(u'Desdobramento', output_field=CharField())) \
            .select_related('acao')
            
        bonificacoes = EventoBonusAcao.objects.filter(Q(acao__ticker=ticker, eventobonusacaorecebida__isnull=True, data__range=[dia.replace(month=1).replace(day=1), dia]) \
                                                        | Q(eventobonusacaorecebida__acao_recebida__ticker=ticker, data__lte=dia)) \
            .annotate(tipo=Value(u'Bonificação', output_field=CharField())).select_related('acao', 'eventobonusacaorecebida__acao_recebida')
            
        
        alteracoes = EventoAlteracaoAcao.objects.filter(Q(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]) | Q(nova_acao__ticker=ticker, data__lte=dia)) \
            .exclude(id=ignorar_alteracao_id).annotate(tipo=Value(u'Alteração', output_field=CharField())).select_related('acao', 'nova_acao')
        
        lista_conjunta = sorted(chain(agrupamentos, desdobramentos, bonificacoes, alteracoes, operacoes), key=attrgetter('data'))
        
        for elemento in lista_conjunta:
            if elemento.tipo == 'Operação':
                qtd_acoes += elemento.qtd_final
            elif elemento.tipo == 'Agrupamento':
                qtd_acoes = elemento.qtd_apos(qtd_acoes)
            elif elemento.tipo == 'Desdobramento':
                qtd_acoes = elemento.qtd_apos(qtd_acoes)
            elif elemento.tipo == 'Bonificação':
                if elemento.acao.ticker == ticker and elemento.acao_recebida.ticker == ticker:
                    qtd_acoes += elemento.qtd_bonus(qtd_acoes)
                elif elemento.acao_recebida.ticker == ticker:
                    qtd_acoes += elemento.qtd_bonus(calcular_qtd_acoes_ate_dia_por_ticker(investidor, elemento.acao.ticker, elemento.data, destinacao))
            elif elemento.tipo == 'Alteração':
                if elemento.acao.ticker == ticker:
                    qtd_acoes = 0
                elif elemento.nova_acao.ticker == ticker:
                    qtd_acoes += calcular_qtd_acoes_ate_dia_por_ticker(investidor, elemento.acao.ticker, elemento.data, destinacao,
                                                                       ignorar_alteracao_id=elemento.id)
    
    
    return qtd_acoes

def calcular_qtd_acoes_ate_dia_por_divisao(dia, divisao_id, destinacao='B'):
    """ 
    Calcula a quantidade de ações até dia determinado por divisão
    
    Parâmetros: Dia final
                ID da divisão
                Destinação das operações
    Retorno: Quantidade de ações {ticker: qtd}
    """
    operacoes = DivisaoOperacaoAcao.objects.filter(operacao__destinacao=destinacao, operacao__data__lte=dia, divisao__id=divisao_id).annotate(acao_ticker=F('operacao__acao__ticker')) \
        .annotate(tipo_operacao=F('operacao__tipo_operacao')).annotate(data=F('operacao__data')).order_by('data')
    if len(operacoes) == 0:
        return {}
#     operacoes = OperacaoAcao.objects.filter(destinacao=destinacao, id__in=operacoes_divisao_id).exclude(data__isnull=True).annotate(acao_ticker=F('acao__ticker')).order_by('data')
    # Pega os proventos em ações recebidos por outras ações
    proventos_em_acoes = AcaoProvento.objects.filter(provento__acao__ticker__in=list(set(operacoes.values_list('acao_ticker', flat=True))), provento__data_ex__lte=dia).exclude(provento__data_ex__isnull=True) \
        .annotate(provento_acao_ticker=F('provento__acao__ticker')).annotate(acao_ticker=F('acao_recebida__ticker')).annotate(data=F('provento__data_ex')) \
        .annotate(valor_unitario=F('provento__valor_unitario')).order_by('data')
    
    lista_conjunta = sorted(chain(operacoes, proventos_em_acoes), key=attrgetter('data'))
    
    qtd_acoes = {}
    
    for item in lista_conjunta:
        if item.acao_ticker not in qtd_acoes:
            qtd_acoes[item.acao_ticker] = 0
                
        if isinstance(item, DivisaoOperacaoAcao): 
            # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
#             item.quantidade = DivisaoOperacaoAcao.objects.get(divisao__id=divisao_id, operacao=item).quantidade
            
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                qtd_acoes[item.acao_ticker] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                qtd_acoes[item.acao_ticker] -= item.quantidade
        
        elif isinstance(item, AcaoProvento): 
            if item.provento_acao_ticker not in qtd_acoes:
                qtd_acoes[item.provento_acao_ticker] = 0
            
            if item.provento_acao_ticker == item.acao_ticker:
                qtd_acoes[item.acao_ticker] += int(item.valor_unitario * qtd_acoes[item.acao_ticker] / 100)
            else:
                qtd_acoes[item.acao_ticker] += int(item.valor_unitario * qtd_acoes[item.provento_acao_ticker] / 100)
    
    for key, item in qtd_acoes.items():
        if qtd_acoes[key] == 0:
            del qtd_acoes[key]
    
    return qtd_acoes

def calcular_qtd_acoes_ate_dia_por_ticker_por_divisao(dia, divisao_id, ticker, ignorar_alteracao_id=None):
    """ 
    Calcula a quantidade de ações até dia determinado para um ticker determinado
    
    Parâmetros: Dia final
                Id da divisão
                Ticker da ação
                Id da alteração a ser ignorada
    Retorno: Quantidade de ações para o ticker determinado
    """
    # TODO implementar
    return

def calcular_poupanca_prov_acao_ate_dia(investidor, dia, destinacao=OperacaoAcao.DESTINACAO_BH):
    """
    Calcula a quantidade de proventos provisionada até dia determinado para ações
    
    Parâmetros: Investidor
                Dia da posição de proventos
                Destinação (B&H ou Trade)
    Retorno: Quantidade provisionada no dia
    """
    operacoes = OperacaoAcao.objects.filter(investidor=investidor, destinacao=destinacao, data__lte=dia).annotate(acao_ticker=F('acao__ticker')).order_by('data') \
        .prefetch_related('usoproventosoperacaoacao_set')
    
    # Remover valores repetidos
#     acoes = list(set(operacoes.values_list('acao', flat=True)))

    proventos = ProventoAcao.objects.filter(acao__in=list(set(operacoes.values_list('acao', flat=True))), data_pagamento__lte=dia).annotate(acao_ticker=F('acao__ticker')) \
        .annotate(data=F('data_ex')).order_by('data').prefetch_related('acaoprovento_set')
     
    lista_conjunta = sorted(chain(proventos, operacoes),
                            key=attrgetter('data'))
    
    total_proventos = Decimal(0)
    
    # Guarda as ações correntes para o calculo do patrimonio
    acoes = {}
    # Calculos de patrimonio e gasto total
    for item_lista in lista_conjunta:      
#         print acoes, total_proventos
        if item_lista.acao_ticker not in acoes.keys():
            acoes[item_lista.acao_ticker] = 0
            
        # Verifica se é uma compra/venda
        if isinstance(item_lista, OperacaoAcao):   
            # Verificar se se trata de compra ou venda
            if item_lista.tipo_operacao == 'C':
                if item_lista.utilizou_proventos():
                    total_proventos -= item_lista.qtd_proventos_utilizada()
                acoes[item_lista.acao_ticker] += item_lista.quantidade
                
            elif item_lista.tipo_operacao == 'V':
                acoes[item_lista.acao_ticker] -= item_lista.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item_lista, ProventoAcao):
            if acoes[item_lista.acao_ticker] > 0:
                if item_lista.tipo_provento in ['D', 'J']:
                    total_recebido = acoes[item_lista.acao_ticker] * item_lista.valor_unitario
                    if item_lista.tipo_provento == 'J':
                        total_recebido = total_recebido * Decimal(0.85)
                    total_proventos += total_recebido
                    
                elif item_lista.tipo_provento == 'A':
                    provento_acao = item_lista.acaoprovento_set.all()[0]
                    if provento_acao.acao_recebida.ticker not in acoes.keys():
                        acoes[provento_acao.acao_recebida.ticker] = 0
                    acoes_recebidas = int((acoes[item_lista.acao_ticker] * item_lista.valor_unitario ) / 100 )
                    item_lista.total_gasto = acoes_recebidas
                    acoes[provento_acao.acao_recebida.ticker] += acoes_recebidas
                    if provento_acao.valor_calculo_frac > 0:
                        if provento_acao.data_pagamento_frac <= datetime.date.today():
                            total_proventos += (((acoes[item_lista.acao_ticker] * item_lista.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
    
    return total_proventos.quantize(Decimal('0.01'))

def calcular_poupanca_prov_acao_ate_dia_por_divisao(dia, divisao, destinacao=OperacaoAcao.DESTINACAO_BH):
    """
    Calcula a quantidade de proventos provisionada até dia determinado para uma divisão para ações
    
    Parâmetros: Dia da posição de proventos, divisão escolhida, destinação ('B' ou 'T')
    Retorno: Quantidade provisionada no dia
    """
    operacoes = DivisaoOperacaoAcao.objects.filter(divisao=divisao, operacao__destinacao=destinacao, operacao__data__lte=dia).annotate(acao_ticker=F('operacao__acao__ticker')) \
        .select_related('operacao').annotate(data=F('operacao__data')).order_by('data')

    if len(operacoes) == 0:
        return 0
    
#     operacoes = OperacaoAcao.objects.filter(id__in=operacoes_divisao).annotate(acao_ticker=F('acao__ticker')).order_by('data')

    # Remover valores repetidos
#     acoes = list(set(operacoes.values_list('acao', flat=True)))
    
    proventos = ProventoAcao.objects.filter(acao__ticker__in=list(set(operacoes.values_list('acao_ticker', flat=True))), data_pagamento__lte=dia) \
        .annotate(data=F('data_ex')).annotate(acao_ticker=F('acao__ticker')).order_by('data')
     
    lista_conjunta = sorted(chain(proventos, operacoes),
                            key=attrgetter('data'))
    
    total_proventos = Decimal(0)
    
    # Guarda as ações correntes para o calculo do patrimonio
    acoes = {}
    # Calculos de patrimonio e gasto total
    for item_lista in lista_conjunta:          
#         print acoes, total_proventos 
        if item_lista.acao_ticker not in acoes.keys():
            acoes[item_lista.acao_ticker] = 0
            
        # Verifica se é uma compra/venda
        if isinstance(item_lista, DivisaoOperacaoAcao):  
            # Verificar se se trata de compra ou venda
            if item_lista.operacao.tipo_operacao == 'C':
                if item_lista.operacao.utilizou_proventos():
                    total_proventos -= item_lista.operacao.qtd_proventos_utilizada() * item_lista.percentual_divisao()
                acoes[item_lista.acao_ticker] += item_lista.quantidade
                
            elif item_lista.operacao.tipo_operacao == 'V':
                acoes[item_lista.acao_ticker] -= item_lista.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item_lista, ProventoAcao):
            if acoes[item_lista.acao_ticker] > 0:
                if item_lista.tipo_provento in ['D', 'J']:
                    total_recebido = acoes[item_lista.acao_ticker] * item_lista.valor_unitario
                    if item_lista.tipo_provento == 'J':
                        total_recebido = total_recebido * Decimal(0.85)
                    total_proventos += total_recebido
                    
                elif item_lista.tipo_provento == 'A':
                    provento_acao = item_lista.acaoprovento_set.all()[0]
                    if provento_acao.acao_recebida.ticker not in acoes.keys():
                        acoes[provento_acao.acao_recebida.ticker] = 0
                    acoes_recebidas = int((acoes[item_lista.acao_ticker] * item_lista.valor_unitario ) / 100 )
                    item_lista.total_gasto = acoes_recebidas
                    acoes[provento_acao.acao_recebida.ticker] += acoes_recebidas
                    if provento_acao.valor_calculo_frac > 0:
                        if provento_acao.data_pagamento_frac <= datetime.date.today():
                            total_proventos += (((acoes[item_lista.acao_ticker] * item_lista.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
    
    return total_proventos.quantize(Decimal('0.01'))

def calcular_preco_medio_acoes_ate_dia(investidor, dia=None):
    """
    Calcula o preço médio das ações do investidor em dia determinado
    
    Parâmetros: Investidor
                Dia
    Retorno: Preços médios {ticker: preco_medio}
    """
    # TODO implementar
    return {}

def calcular_preco_medio_acoes_ate_dia_por_ticker(investidor, ticker, dia, destinacao=OperacaoAcao.DESTINACAO_BH, ignorar_alteracao_id=None):
    """ 
    Calcula o preço médio de uma ação do investidor em dia determinado
    
    Parâmetros: Investidor
                Ticker da ação
                Dia final
                Id da incorporação a ser ignorada
    Retorno: Preço médio da ação
    """
    if CheckpointAcao.objects.filter(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, quantidade__gt=0, destinacao=destinacao).exists():
        info_acao = CheckpointAcao.objects.get(investidor=investidor, ano=dia.year-1, acao__ticker=ticker, quantidade__gt=0, destinacao=destinacao)
        qtd_acao = info_acao.quantidade
        preco_medio_acao = info_acao.preco_medio
    else:
        qtd_acao = 0
        preco_medio_acao = 0
    
    operacoes = OperacaoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia], investidor=investidor, destinacao=destinacao) \
        .annotate(custo_total=(Case(When(tipo_operacao='C', then=F('quantidade')*F('preco_unitario') + F('corretagem') + F('emolumentos')), output_field=DecimalField()))) \
        .annotate(tipo=Value(u'Operação', output_field=CharField()))
             
    # Verificar agrupamentos e desdobramentos
    agrupamentos = EventoAgrupamentoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))

    desdobramentos = EventoDesdobramentoAcao.objects.filter(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
    
    alteracoes = EventoAlteracaoAcao.objects.filter(Q(acao__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]) | Q(nova_acao__ticker=ticker, data__lte=dia)) \
        .exclude(id=ignorar_alteracao_id).annotate(tipo=Value(u'Alteração', output_field=CharField()))
    
    # TODO adicionar bonus
    
    lista_conjunta = sorted(chain(agrupamentos, desdobramentos, alteracoes, operacoes), key=attrgetter('data'))
    
    for elemento in lista_conjunta:
        if elemento.tipo == 'Operação':
            if elemento.tipo_operacao == 'C':
                preco_medio_acao = (qtd_acao * preco_medio_acao + elemento.custo_total) / (qtd_acao + elemento.quantidade)
                qtd_acao += elemento.quantidade
                
            elif elemento.tipo_operacao == 'V':
                qtd_acao -= elemento.quantidade
                if qtd_acao == 0:
                    preco_medio_acao = 0
        elif elemento.tipo == 'Amortização':
            if qtd_acao > 0:
                preco_medio_acao -= elemento.valor_unitario
        elif elemento.tipo == 'Agrupamento':
            preco_medio_acao = elemento.preco_medio_apos(preco_medio_acao, qtd_acao)
            qtd_acao = elemento.qtd_apos(qtd_acao)
        elif elemento.tipo == 'Desdobramento':
            preco_medio_acao = elemento.preco_medio_apos(preco_medio_acao, qtd_acao)
            qtd_acao = elemento.qtd_apos(qtd_acao)
        elif elemento.tipo == 'Alteração':
            if elemento.acao.ticker == ticker:
                qtd_acao = 0
                preco_medio_acao = 0
            elif elemento.nova_acao.ticker == ticker:
                qtd_incorporada = calcular_qtd_acoes_ate_dia_por_ticker(investidor, elemento.acao.ticker, elemento.data, destinacao, elemento.id)
                if qtd_incorporada + qtd_acao > 0:
                    preco_medio_acao = (calcular_preco_medio_acoes_ate_dia_por_ticker(investidor, elemento.acao.ticker, elemento.data, destinacao, elemento.id) * qtd_incorporada + \
                                        qtd_acao * preco_medio_acao) / (qtd_incorporada + qtd_acao)
                    qtd_acao += qtd_incorporada
        
    return preco_medio_acao

def calcular_preco_medio_acoes_ate_dia_por_divisao(divisao, dia=None):
    """
    Calcula o preço médio das ações da divisão em dia determinado
    
    Parâmetros: Divisão
                Dia
    Retorno: Preços médios {ticker: preco_medio}
    """
    # TODO implementar
    return {}

def calcular_preco_medio_acoes_ate_dia_por_ticker_por_divisao(divisao, dia, ticker, ignorar_alteracao_id=None):
    """ 
    Calcula o preço médio de uma ação da divisão em dia determinado
    
    Parâmetros: Divisão
                Ticker da ação
                Dia final
                Id da alteração a ser ignorada
    Retorno: Preço médio da ação
    """
    # TODO implementar
    return 0

def verificar_tipo_acao(ticker):
    categoria = int(re.search('\d+', ticker).group(0))
    if categoria == 3:
        return u'ON'
    elif categoria == 4:
        return u'PN'
    elif categoria == 5:
        return u'PNA'
    elif categoria == 6:
        return u'PNB'
    elif categoria == 7:
        return u'PNC'
    elif categoria == 8:
        return u'PND'
    elif categoria == 11:
        return u'UNT'
    raise ValueError('Tipo de ação inválido')

def preencher_codigos_cvm():
    """Preenche códigos bvmf para as empresas a partir das urls na listagem de empresas"""
    acao_url = 'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/BuscaEmpresaListada.aspx?idioma=pt-br'
    req = Request(acao_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        data = response.read()
        if 'Sistema indisponivel' in data:
            return preencher_codigos_cvm()
        inicio = data.find('<div class="inline-list-letra">')
        fim = data.find('</div>', inicio)
        string_importante = (data[inicio:fim])
        letras = re.findall('<a.*?>(.*?)<\/a>', string_importante, flags=re.DOTALL)
#         print letras
        # Buscar empresas
        empresas = Empresa.objects.all()
        for letra in letras:
            letra_url = 'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/BuscaEmpresaListada.aspx?Letra=%s&idioma=pt-br' % letra
            req = Request(letra_url)
            conectou = False
            while not conectou:
                try:
                    response = urlopen(req)
                except HTTPError as e:
                    print 'The server couldn\'t fulfill the request.'
                    print 'Error code: ', e.code
                except URLError as e:
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
                else:
                    data = response.read()
                    if 'Sistema indisponivel' not in data:
                        conectou = True
            inicio = data.find('<tbody>')
            fim = data.find('</tbody>', inicio)
            string_importante = (data[inicio:fim])
            urls = re.findall('<a.*?codigoCvm=(.*?)\">(.*?)<\/a>', string_importante, flags=re.DOTALL)
            for codigo, nome in urls:
                if nome in empresas.values_list('nome_pregao', flat=True):
                    empresa = empresas.filter(nome_pregao=nome).order_by('-id')[0]
                    empresa.codigo_cvm = codigo
                    empresa.save()
#                     print 'Salvou empresa', empresa

def buscar_ticker_acoes(empresa_url, tentativa):
    """
    Busca tickers não cadastrados para empresas
    """
    req = Request(empresa_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        data = response.read()
        if 'Sistema indisponivel' in data:
            if tentativa < 3:
                return buscar_ticker_acoes(empresa_url, tentativa+1)
            else:
                return
        tickers = re.findall("var\s+?symbols\s*?=\s*?'([\w|]+)'", data, flags=re.DOTALL|re.MULTILINE|re.IGNORECASE)
        if len(tickers) > 0:
            return tickers[0].split('|')
        else:
            return ''
        
def verificar_se_existe_evento_para_acao(acao_ticker, data_limite=None):
    """
    Verifica se existe evento para ação até data (data inclusive)
    
    Parâmetros: Ticker da ação
                Data
    Retorno: True caso exista, senão False
    """
    # Preparar data
    if data_limite == None:
        data_limite = datetime.date.today()
        
    # Verificar se há evento, se outra ação foi alterada para esta ou se esta ação foi recebida como bonus por outra
    return any([classe.objects.filter(acao__ticker=acao_ticker, data__lte=data_limite).exists() for classe in EventoAcao.__subclasses__()]) \
        or EventoAlteracaoAcao.objects.filter(nova_acao__ticker=acao_ticker, data__lte=data_limite).exists() \
        or EventoBonusAcaoRecebida.objects.filter(acao_recebida__ticker=acao_ticker, bonus__data__lte=data_limite).exists()
        
def verificar_se_existe_evento_para_acao_periodo(acao_ticker, data_inicio, data_fim):
    """
    Verifica se existe evento para ação no período (datas inclusive)
    
    Parâmetros: Ticker da ação
                Data de início
                Data de fim
    Retorno: True caso exista, senão False
    """
    # Verificar se há evento, se outra ação foi alterada para esta ou se esta ação foi recebida como bonus por outra
#     return any([classe.objects.filter(fii__ticker=fii_ticker, data__range=[data_inicio, data_fim]).exists() for classe in EventoFII.__subclasses__()]) \
#         or EventoIncorporacaoFII.objects.filter(novo_fii__ticker=fii_ticker, data__range=[data_inicio, data_fim]).exists()
    for classe in EventoAcao.__subclasses__():
        if classe.objects.filter(acao__ticker=acao_ticker, data__range=[data_inicio, data_fim]).exists():
            return True
    if EventoAlteracaoAcao.objects.filter(nova_acao__ticker=acao_ticker, data__range=[data_inicio, data_fim]).exists():
        return True
    return EventoBonusAcaoRecebida.objects.filter(acao_recebida__ticker=acao_ticker, bonus__data__range=[data_inicio, data_fim]).exists()
        
def verificar_se_existe_evento_para_acoes_periodo(acao_tickers, data_inicio, data_fim):
    """
    Verifica se existe evento para ações no período (datas inclusive)
    
    Parâmetros: Lista de tickers de ações
                Data de início
                Data de fim
    Retorno: True caso exista, senão False
    """
    # Verificar se há evento, se outra ação foi alterada para esta ou se esta ação foi recebida como bonus por outra
#     return any([classe.objects.filter(fii__ticker__in=fii_tickers, data__range=[data_inicio, data_fim]).exists() for classe in EventoFII.__subclasses__()]) \
#         or EventoIncorporacaoFII.objects.filter(novo_fii__ticker__in=fii_tickers, data__range=[data_inicio, data_fim]).exists()
    for classe in EventoAcao.__subclasses__():
        if classe.objects.filter(acao__ticker__in=acao_tickers, data__range=[data_inicio, data_fim]).exists():
            return True
    if EventoAlteracaoAcao.objects.filter(nova_acao__ticker__in=acao_tickers, data__range=[data_inicio, data_fim]).exists():
        return True
    return EventoBonusAcaoRecebida.objects.filter(acao_recebida__ticker__in=acao_tickers, bonus__data__range=[data_inicio, data_fim]).exists()

def listar_acoes_com_evento_periodo(acao_tickers, data_inicio, data_fim):
    """
    Lista os tickers de ações que possuem algum evento no período informado
    
    Parâmetros: Lista de tickers de ações
                Data de início
                Data de fim
    Retorno: Lista com os tickers de ações
    """
    lista_tickers = list()
    for classe in EventoAcao.__subclasses__():
        lista_tickers.extend(classe.objects.filter(acao__ticker__in=acao_tickers, data__range=[data_inicio, data_fim]) \
                             .values_list('acao__ticker', flat=True))
    # Adicionar recebimentos por alteração
    lista_tickers.extend(EventoAlteracaoAcao.objects.filter(nova_acao__ticker__in=acao_tickers, data__range=[data_inicio, data_fim]) \
                         .values_list('nova_acao__ticker', flat=True))
    
    # Adicionar recebimentos por bônus
    lista_tickers.extend(EventoBonusAcaoRecebida.objects.filter(acao_recebida__ticker__in=acao_tickers, bonus__data__range=[data_inicio, data_fim]) \
                         .values_list('acao_recebida__ticker', flat=True))
    
    return list(set(lista_tickers))
