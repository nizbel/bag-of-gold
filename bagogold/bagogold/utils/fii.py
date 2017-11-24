# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII, \
    CheckpointDivisaoFII
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII, \
    ValorDiarioFII, HistoricoFII, EventoAgrupamentoFII, EventoDesdobramentoFII, \
    EventoFII, EventoIncorporacaoFII, FII, CheckpointFII, CheckpointProventosFII
from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When, Value
from django.db.models.fields import DecimalField, CharField
from django.db.models.query_utils import Q
from itertools import chain
from operator import attrgetter
import datetime

def calcular_poupanca_prov_fii_ate_dia(investidor, dia=datetime.date.today()):
    """
    Calcula a quantidade de proventos provisionada até dia determinado para FII
    Parâmetros: Investidor
                Dia da posição de proventos
    Retorno: Quantidade provisionada no dia
    """
    fiis = dict(CheckpointFII.objects.filter(investidor=investidor, ano=dia.year-1).values_list('fii', 'quantidade'))
    operacoes = OperacaoFII.objects.filter(investidor=investidor, data__range=[dia.replace(month=1).replace(day=1), dia]).order_by('data')
    
    # Remover valores repetidos
    fiis_proventos = list(set(fiis.keys() + list(operacoes.values_list('fii', flat=True))))
    
    proventos = ProventoFII.objects.filter(data_pagamento__range=[dia.replace(month=1).replace(day=1), dia], fii__in=fiis_proventos).annotate(data=F('data_ex')).order_by('data_ex')
     
    # Verificar agrupamentos e desdobramentos
    agrupamentos = EventoAgrupamentoFII.objects.filter(fii__in=fiis_proventos, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))

    desdobramentos = EventoDesdobramentoFII.objects.filter(fii__in=fiis_proventos, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
    
    incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__in=fiis_proventos, data__range=[dia.replace(month=1).replace(day=1), dia]) | Q(novo_fii__in=fiis_proventos, data__lte=dia)) \
        .annotate(tipo=Value(u'Incorporação', output_field=CharField())) 
    
    lista_conjunta = sorted(chain(proventos, agrupamentos, desdobramentos, incorporacoes, operacoes),
                            key=attrgetter('data'))
    
    # Preparar total de proventos até o final do ano anterior
    if CheckpointProventosFII.objects.filter(investidor=investidor, ano=dia.year-1).exists():
        total_proventos = CheckpointProventosFII.objects.get(investidor=investidor, ano=dia.year-1).valor
    else:
        total_proventos = Decimal(0)
    
    # Calculos de patrimonio e gasto total
    for item_lista in lista_conjunta:      
        if item_lista.fii.ticker not in fiis.keys():
            fiis[item_lista.fii.ticker] = 0
            
        # Verifica se é uma compra/venda
        if isinstance(item_lista, OperacaoFII):   
            # Verificar se se trata de compra ou venda
            if item_lista.tipo_operacao == 'C':
                if item_lista.utilizou_proventos():
                    total_proventos -= item_lista.qtd_proventos_utilizada()
                fiis[item_lista.fii.ticker] += item_lista.quantidade
                
            elif item_lista.tipo_operacao == 'V':
                fiis[item_lista.fii.ticker] -= item_lista.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item_lista, ProventoFII):
            if fiis[item_lista.fii.ticker] > 0:
                total_recebido = fiis[item_lista.fii.ticker] * item_lista.valor_unitario
                total_proventos += total_recebido

        # Eventos
        else:
            if item_lista.tipo == 'Agrupamento':
                fiis[item_lista.fii.ticker] = item_lista.qtd_apos(fiis[item_lista.fii.ticker])
            elif item_lista.tipo == 'Desdobramento':
                fiis[item_lista.fii.ticker] = item_lista.qtd_apos(fiis[item_lista.fii.ticker])
            elif item_lista.tipo == 'Incorporação':
                fiis[item_lista.fii.ticker] = 0
                if item_lista.novo_fii.ticker not in fiis.keys():
                    fiis[item_lista.novo_fii.ticker] = 0
                fiis[item_lista.novo_fii.ticker] += calcular_qtd_fiis_ate_dia_por_ticker(investidor, item_lista.data, item_lista.fii.ticker, item_lista.id)
           
    return total_proventos.quantize(Decimal('0.01'))

def calcular_poupanca_prov_fii_ate_dia_por_divisao(dia, divisao):
    """
    Calcula a quantidade de proventos provisionada até dia determinado para uma divisão para FII
    Parâmetros: Dia da posição de proventos
                Divisão escolhida
    Retorno: Quantidade provisionada no dia
    """
    operacoes_divisao = DivisaoOperacaoFII.objects.filter(divisao=divisao, operacao__data__lte=dia).values_list('operacao__id', flat=True)
    
    operacoes = OperacaoFII.objects.filter(id__in=operacoes_divisao).order_by('data')

    proventos = ProventoFII.objects.filter(data_ex__lte=dia).annotate(data=F('data_ex')).order_by('data_ex')
     
    lista_conjunta = sorted(chain(operacoes, proventos),
                            key=attrgetter('data'))
    
    total_proventos = Decimal(0)
    
    # Guarda as ações correntes para o calculo do patrimonio
    fiis = {}
    # Calculos de patrimonio e gasto total
    for item_lista in lista_conjunta:      
        if item_lista.fii.ticker not in fiis.keys():
            fiis[item_lista.fii.ticker] = 0
            
        # Verifica se é uma compra/venda
        if isinstance(item_lista, OperacaoFII):   
            # Verificar se se trata de compra ou venda
            if item_lista.tipo_operacao == 'C':
                if item_lista.utilizou_proventos():
                    total_proventos -= item_lista.qtd_proventos_utilizada()
                fiis[item_lista.fii.ticker] += item_lista.quantidade
                
            elif item_lista.tipo_operacao == 'V':
                fiis[item_lista.fii.ticker] -= item_lista.quantidade
        
        # Verifica se é recebimento de proventos
        elif isinstance(item_lista, ProventoFII):
            if item_lista.data_pagamento <= datetime.date.today() and fiis[item_lista.fii.ticker] > 0:
                total_recebido = fiis[item_lista.fii.ticker] * item_lista.valor_unitario
                total_proventos += total_recebido
                    
    return total_proventos.quantize(Decimal('0.01'))

def calcular_qtd_fiis_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de FIIs até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de FIIs {ticker: qtd}
    """
    if not any([verificar_se_existe_evento_para_fii_periodo(fii, dia.replace(month=1).replace(day=1), dia) for fii in \
                FII.objects.filter(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia) \
                                   .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True))]):
        posicao_anterior = dict(CheckpointFII.objects.filter(investidor=investidor, ano=dia.year-1, quantidade__gt=0).values_list('fii__ticker', 'quantidade'))
        novas_operacoes = dict(OperacaoFII.objects.filter(investidor=investidor, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(ticker=F('fii__ticker')).values('ticker') \
            .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                                When(tipo_operacao='V', then=F('quantidade')*-1),
                                output_field=DecimalField()))).values_list('ticker', 'total').exclude(total=0))
        
        qtd_fii = { k: posicao_anterior.get(k, 0) + novas_operacoes.get(k, 0) for k in set(posicao_anterior) | set(novas_operacoes) \
                   if posicao_anterior.get(k, 0) + novas_operacoes.get(k, 0) != 0}
    
    else:
        qtd_fii = {}
#         for fii in FII.objects.filter(Q(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia) \
#                                       .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)) \
#                                       | Q(id__in=EventoIncorporacaoFII.objects.filter(fii__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia) \
#                                       .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)) \
#                                           .order_by('novo_fii__id').distinct('novo_fii__id').values_list('novo_fii', flat=True))):
        fiis_operacoes = list(OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).order_by('fii__id').distinct('fii__id').values_list('fii__ticker', flat=True))
        fiis_incorporados = list(EventoIncorporacaoFII.objects.filter(fii__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia) \
                                    .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)) \
                                        .order_by('novo_fii__id').distinct('novo_fii__id').values_list('novo_fii__ticker', flat=True))
        for ticker in list(set(fiis_operacoes + fiis_incorporados)):
            qtd_fii_na_data = calcular_qtd_fiis_ate_dia_por_ticker(investidor, dia, ticker)
            if qtd_fii_na_data > 0:
                qtd_fii[ticker] = qtd_fii_na_data
    return qtd_fii

def calcular_qtd_fiis_ate_dia_por_ticker(investidor, dia, ticker, ignorar_incorporacao_id=None):
    """ 
    Calcula a quantidade de FIIs até dia determinado para um ticker determinado
    Parâmetros: Investidor
                Ticker do FII
                Dia final
                Id da incorporação a ser ignorada
    Retorno: Quantidade de FIIs para o ticker determinado
    """
    if not verificar_se_existe_evento_para_fii_periodo(FII.objects.get(ticker=ticker), dia.replace(month=1).replace(day=1), dia):
        if CheckpointFII.objects.filter(investidor=investidor, ano=dia.year-1, fii__ticker=ticker, quantidade__gt=0).exists():
            qtd_fii = CheckpointFII.objects.get(investidor=investidor, ano=dia.year-1, fii__ticker=ticker, quantidade__gt=0).quantidade
        else:
            qtd_fii = 0
        qtd_fii += (OperacaoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia], investidor=investidor).exclude(data__isnull=True) \
            .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                                      When(tipo_operacao='V', then=F('quantidade')*-1),
                                      output_field=DecimalField())))['total'] or 0)
    else:
        if CheckpointFII.objects.filter(investidor=investidor, ano=dia.year-1, fii__ticker=ticker).exists():
            qtd_fii = CheckpointFII.objects.get(investidor=investidor, ano=dia.year-1, fii__ticker=ticker).quantidade
        else:
            qtd_fii = 0
        operacoes = OperacaoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia], investidor=investidor).exclude(data__isnull=True) \
            .annotate(qtd_final=(Case(When(tipo_operacao='C', then=F('quantidade')),
                                      When(tipo_operacao='V', then=F('quantidade')*-1),
                                      output_field=DecimalField()))).annotate(tipo=Value(u'Operação', output_field=CharField()))
                                      
                                      
        # Verificar agrupamentos e desdobramentos
        agrupamentos = EventoAgrupamentoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))

        desdobramentos = EventoDesdobramentoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
        
        incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]) | Q(novo_fii__ticker=ticker, data__lte=dia)).exclude(id=ignorar_incorporacao_id) \
            .annotate(tipo=Value(u'Incorporação', output_field=CharField()))
        
        lista_conjunta = sorted(chain(agrupamentos, desdobramentos, incorporacoes, operacoes), key=attrgetter('data'))
        
        for elemento in lista_conjunta:
            if elemento.tipo == 'Operação':
                qtd_fii += elemento.qtd_final
            elif elemento.tipo == 'Agrupamento':
                qtd_fii = elemento.qtd_apos(qtd_fii)
            elif elemento.tipo == 'Desdobramento':
                qtd_fii = elemento.qtd_apos(qtd_fii)
            elif elemento.tipo == 'Incorporação':
                if elemento.fii.ticker == ticker:
                    qtd_fii = 0
                elif elemento.novo_fii.ticker == ticker:
                    qtd_fii += calcular_qtd_fiis_ate_dia_por_ticker(investidor, elemento.data, elemento.fii.ticker, elemento.id)
        
    return qtd_fii

def calcular_qtd_fiis_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de FIIs até dia determinado
    Parâmetros: Dia final
                Id da divisão
    Retorno: Quantidade de FIIs {ticker: qtd}
    """
    if not any([verificar_se_existe_evento_para_fii(fii, dia) for fii in FII.objects.filter(id__in=DivisaoOperacaoFII.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id) \
                                                                                            .order_by('operacao__fii__id').distinct('operacao__fii__id').values_list('operacao__fii', flat=True))]):
        
        posicao_anterior = dict(CheckpointDivisaoFII.objects.filter(divisao__id=divisao_id, ano=dia.year-1, quantidade__gt=0).values_list('fii__ticker', 'quantidade'))
        novas_operacoes = dict(DivisaoOperacaoFII.objects.filter(operacao__data__range=[dia.replace(month=1).replace(day=1), dia], divisao__id=divisao_id).annotate(ticker=F('operacao__fii__ticker')) \
            .values('ticker').annotate(qtd=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                                When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                                output_field=DecimalField()))).values_list('ticker', 'qtd').exclude(qtd=0))
        qtd_fii = { k: posicao_anterior.get(k, 0) + novas_operacoes.get(k, 0) for k in set(posicao_anterior) | set(novas_operacoes) \
                   if posicao_anterior.get(k, 0) + novas_operacoes.get(k, 0) != 0}

    else:
        qtd_fii = {}
        for fii in FII.objects.filter(id__in=DivisaoOperacaoFII.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id) \
                                                                                            .order_by('operacao__fii__id').distinct('operacao__fii__id').values_list('operacao__fii', flat=True)):
            qtd_fii_na_data = calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(dia, divisao_id, fii.ticker)
            if qtd_fii_na_data > 0:
                qtd_fii[fii.ticker] = qtd_fii_na_data
    
    return qtd_fii

def calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(dia, divisao_id, ticker, ignorar_incorporacao_id=None):
    """ 
    Calcula a quantidade de FIIs até dia determinado para um ticker determinado
    Parâmetros: Dia final
                Id da divisão
                Ticker do FII
                Id da incorporação a ser ignorada
    Retorno: Quantidade de cotas para o ticker determinado
    """
    if not verificar_se_existe_evento_para_fii_periodo(FII.objects.get(ticker=ticker), dia.replace(month=1).replace(day=1), dia):
        if CheckpointDivisaoFII.objects.filter(divisao__id=divisao_id, ano=dia.year-1, fii__ticker=ticker, quantidade__gt=0).exists():
            qtd_fii = CheckpointFII.objects.get(divisao__id=divisao_id, ano=dia.year-1, fii__ticker=ticker, quantidade__gt=0).quantidade
        else:
            qtd_fii = 0
        qtd_fii += DivisaoOperacaoFII.objects.filter(operacao__data__range=[dia.replace(month=1).replace(day=1), dia], divisao__id=divisao_id, operacao__fii__ticker=ticker) \
                       .aggregate(qtd=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                                When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                                output_field=DecimalField())))['qtd'] or 0
    else:
        if CheckpointDivisaoFII.objects.filter(divisao__id=divisao_id, ano=dia.year-1, fii__ticker=ticker, quantidade__gt=0).exists():
            qtd_fii = CheckpointFII.objects.get(divisao__id=divisao_id, ano=dia.year-1, fii__ticker=ticker, quantidade__gt=0).quantidade
        else:
            qtd_fii = 0
        
        operacoes = DivisaoOperacaoFII.objects.filter(operacao__fii__ticker=ticker, operacao__data__range=[dia.replace(month=1).replace(day=1), dia], divisao__id=divisao_id) \
            .annotate(qtd_final=(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                                      When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                                      output_field=DecimalField()))).annotate(data=F('operacao__data')).annotate(tipo=Value(u'Operação', output_field=CharField()))
                                      
                                      
        # Verificar agrupamentos e desdobramentos
        agrupamentos = EventoAgrupamentoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))

        desdobramentos = EventoDesdobramentoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
        
        incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]) | Q(novo_fii__ticker=ticker, data__lte=dia)).exclude(id=ignorar_incorporacao_id) \
            .annotate(tipo=Value(u'Incorporação', output_field=CharField()))
        
        lista_conjunta = sorted(chain(agrupamentos, desdobramentos, incorporacoes, operacoes), key=attrgetter('data'))
        
        for elemento in lista_conjunta:
            if elemento.tipo == 'Operação':
                qtd_fii += elemento.qtd_final
            elif elemento.tipo == 'Agrupamento':
                qtd_fii = elemento.qtd_apos(qtd_fii)
            elif elemento.tipo == 'Desdobramento':
                qtd_fii = elemento.qtd_apos(qtd_fii)
            elif elemento.tipo == 'Incorporação':
                if elemento.fii.ticker == ticker:
                    qtd_fii = 0
                elif elemento.novo_fii.ticker == ticker:
                    qtd_fii += calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(elemento.data, divisao_id, elemento.fii.ticker, elemento.id)
        
    return qtd_fii

def calcular_preco_medio_fiis_ate_dia(investidor, dia=datetime.date.today()):
    """
    Calcula o preço médio dos FIIs do investidor em dia determinado
    Parâmetros: Investidor
                Dia
    Retorno: Preços médios {ticker: preco_medio}
    """
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    if not any([verificar_se_existe_evento_para_fii_periodo(fii, dia.replace(month=1).replace(day=1), dia) for fii in \
                FII.objects.filter(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia) \
                                   .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True))]):
        posicao_anterior = CheckpointFII.objects.filter(investidor=investidor, ano=dia.year-1, quantidade__gt=0)
    
        novas_operacoes = OperacaoFII.objects.filter(investidor=investidor, data__range=[dia.replace(month=1).replace(day=1), dia])
            
        lista_fiis = list(set(list(posicao_anterior.order_by('fii_id').distinct('fii_id').values_list('fii', flat=True)) + \
            list(novas_operacoes.order_by('fii_id').distinct('fii_id').values_list('fii', flat=True))))
        amortizacoes = ProventoFII.objects.filter(fii__in=lista_fiis, data_ex__range=[dia.replace(month=1).replace(day=1), dia], tipo_provento='A').annotate(data=F('data_ex')).order_by('data')
        
        novas_operacoes = novas_operacoes.annotate(custo_total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')*F('preco_unitario') + F('corretagem') + F('emolumentos')), 
                                                                        output_field=DecimalField()))).order_by('data')
        
        preco_medio_fii = {}
        for posicao in posicao_anterior:
            preco_medio_fii[posicao.fii.ticker] = Object()
            preco_medio_fii[posicao.fii.ticker].quantidade = posicao.quantidade
            preco_medio_fii[posicao.fii.ticker].preco_medio = posicao.preco_medio
        
        lista_conjunta = sorted(chain(amortizacoes, novas_operacoes), key=attrgetter('data'))
        
        # Iterar por operações e amortizações
        for elemento in lista_conjunta:
            if elemento.fii.ticker not in preco_medio_fii.keys():
                preco_medio_fii[elemento.fii.ticker] = Object()
                preco_medio_fii[elemento.fii.ticker].quantidade = 0
                preco_medio_fii[elemento.fii.ticker].preco_medio = 0
            # Verifica se é uma compra/venda
            if isinstance(elemento, OperacaoFII):   
                # Verificar se se trata de compra ou venda
                if elemento.tipo_operacao == 'C':
                    preco_medio_fii[elemento.fii.ticker].preco_medio = (preco_medio_fii[elemento.fii.ticker].quantidade * preco_medio_fii[elemento.fii.ticker].preco_medio + elemento.custo_total) \
                        / (preco_medio_fii[elemento.fii.ticker].quantidade + elemento.quantidade)
                    preco_medio_fii[elemento.fii.ticker].quantidade += elemento.quantidade
                    
                elif elemento.tipo_operacao == 'V':
                    preco_medio_fii[elemento.fii.ticker].quantidade -= elemento.quantidade
                    if preco_medio_fii[elemento.fii.ticker].quantidade == 0:
                        preco_medio_fii[elemento.fii.ticker].preco_medio = 0
            
            # Verifica se é recebimento de proventos
            elif isinstance(elemento, ProventoFII):
                if preco_medio_fii[elemento.fii.ticker].quantidade > 0:
                    preco_medio_fii[elemento.fii.ticker].preco_medio -= elemento.valor_unitario
                    
        # Preparar dict
        preco_medio_fii = {ticker: info_qtd_custo.preco_medio for ticker, info_qtd_custo in preco_medio_fii.items() if info_qtd_custo.quantidade > 0}
            
    else:
        preco_medio_fii = {}
#         for fii in FII.objects.filter(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
#                                                                                             .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)):
        for fii in FII.objects.filter(Q(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia) \
                                      .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)) \
                                      | Q(id__in=EventoIncorporacaoFII.objects.filter(fii__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia) \
                                      .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)) \
                                          .order_by('novo_fii__id').distinct('novo_fii__id').values_list('novo_fii', flat=True))):
#             print fii
            preco_medio_na_data = calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, dia, fii.ticker)
            if preco_medio_na_data > 0:
                preco_medio_fii[fii.ticker] = preco_medio_na_data
    
    return preco_medio_fii

def calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, dia, ticker, ignorar_incorporacao_id=None):
    """ 
    Calcula o preço médio de um FII em dia determinado
    Parâmetros: Investidor
                Ticker do FII
                Dia final
                Id da incorporação a ser ignorada
    Retorno: Preço médio do FII
    """
    if CheckpointFII.objects.filter(investidor=investidor, ano=dia.year-1, fii__ticker=ticker, quantidade__gt=0).exists():
        info_fii = CheckpointFII.objects.get(investidor=investidor, ano=dia.year-1, fii__ticker=ticker, quantidade__gt=0)
        qtd_fii = info_fii.quantidade
        preco_medio_fii = info_fii.preco_medio
    else:
        qtd_fii = 0
        preco_medio_fii = 0
    
    operacoes = OperacaoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia], investidor=investidor) \
        .annotate(custo_total=(Case(When(tipo_operacao='C', then=F('quantidade')*F('preco_unitario') + F('corretagem') + F('emolumentos')), output_field=DecimalField()))) \
        .annotate(tipo=Value(u'Operação', output_field=CharField()))
             
    amortizacoes = ProventoFII.objects.filter(fii__ticker=ticker, data_ex__range=[dia.replace(month=1).replace(day=1), dia], tipo_provento='A').annotate(data=F('data_ex')) \
        .annotate(tipo=Value(u'Amortização', output_field=CharField())).order_by('data')
                         
    # Verificar agrupamentos e desdobramentos
    agrupamentos = EventoAgrupamentoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))

    desdobramentos = EventoDesdobramentoFII.objects.filter(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
    
    incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__ticker=ticker, data__range=[dia.replace(month=1).replace(day=1), dia]) | Q(novo_fii__ticker=ticker, data__lte=dia)).exclude(id=ignorar_incorporacao_id) \
        .annotate(tipo=Value(u'Incorporação', output_field=CharField()))
    
    lista_conjunta = sorted(chain(amortizacoes, agrupamentos, desdobramentos, incorporacoes, operacoes), key=attrgetter('data'))
    
    for elemento in lista_conjunta:
        if elemento.tipo == 'Operação':
            if elemento.tipo_operacao == 'C':
                preco_medio_fii = (qtd_fii * preco_medio_fii + elemento.custo_total) / (qtd_fii + elemento.quantidade)
                qtd_fii += elemento.quantidade
                
            elif elemento.tipo_operacao == 'V':
                qtd_fii -= elemento.quantidade
                if qtd_fii == 0:
                    preco_medio_fii = 0
        elif elemento.tipo == 'Amortização':
            if qtd_fii > 0:
                preco_medio_fii -= elemento.valor_unitario
        elif elemento.tipo == 'Agrupamento':
            preco_medio_fii = elemento.preco_medio_apos(preco_medio_fii, qtd_fii)
            qtd_fii = elemento.qtd_apos(qtd_fii)
        elif elemento.tipo == 'Desdobramento':
            preco_medio_fii = elemento.preco_medio_apos(preco_medio_fii, qtd_fii)
            qtd_fii = elemento.qtd_apos(qtd_fii)
        elif elemento.tipo == 'Incorporação':
            if elemento.fii.ticker == ticker:
                qtd_fii = 0
                preco_medio_fii = 0
            elif elemento.novo_fii.ticker == ticker:
                qtd_incorporada = calcular_qtd_fiis_ate_dia_por_ticker(investidor, elemento.data, elemento.fii.ticker, elemento.id)
                if qtd_incorporada + qtd_fii > 0:
                    preco_medio_fii = (calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, elemento.data, elemento.fii.ticker, elemento.id) * qtd_incorporada + \
                                        qtd_fii * preco_medio_fii) / (qtd_incorporada + qtd_fii)
                    qtd_fii += qtd_incorporada
        
    return preco_medio_fii

def calcular_rendimento_proventos_fii_12_meses(fii):
    """ 
    Calcula o rendimento percentual dos proventos nos últimos 12 meses para um FII
    Parâmetros: FII
    Retorno: Rendimento percentual
    """
    total_proventos = Decimal(0)
    data_1_ano_atras = datetime.date.today() - datetime.timedelta(days=365)
    # Calcular media de proventos dos ultimos 6 recebimentos
    proventos = ProventoFII.objects.filter(fii=fii, data_ex__gt=data_1_ano_atras).order_by('data_ex')
    if len(proventos) == 0:
        return Decimal(0)
    for provento in proventos:
        total_proventos += provento.valor_unitario
        
    # Pegar valor atual dos FIIs
    preenchido = False
    try:
        valor_diario_mais_recente = ValorDiarioFII.objects.filter(fii=fii).order_by('-data_hora')
        if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
            valor_atual = valor_diario_mais_recente[0].preco_unitario
            percentual_retorno = (total_proventos/valor_atual) * Decimal(100)
            preenchido = True
    except:
        preenchido = False
    if (not preenchido):
        # Pegar último dia util com negociação da ação para calculo do patrimonio
        try:
            valor_atual = HistoricoFII.objects.filter(fii=fii).order_by('-data')[0].preco_unitario
            # Percentual do retorno sobre o valor do fundo
            percentual_retorno = (total_proventos/valor_atual) * Decimal(100)
        except:
            valor_atual = Decimal(0)
            # Percentual do retorno sobre o valor do fundo
            percentual_retorno = Decimal(0)
    
    return percentual_retorno

def calcular_variacao_percentual_fii_por_periodo(fii, periodo_inicio, periodo_fim):
    """
    Calcula a variação percentual de um FII em determinado período
    Parâmetros: FII
                Data inicial do período
                Data final do período
    Retorno: Variação percentual
    """
    try:
        valor_inicial = HistoricoFII.objects.filter(fii=fii, data__lte=periodo_inicio).order_by('-data')[0].preco_unitario
        valor_final = HistoricoFII.objects.filter(fii=fii, data__lte=periodo_fim).order_by('-data')[0].preco_unitario
    except:
        return 0
    
    return (valor_final - valor_inicial) / valor_final * 100

def calcular_valor_fii_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula o valor das cotas do investidor até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Valor das cotas {ticker: valor_da_data}
    """
    
    qtd_fii = calcular_qtd_fiis_ate_dia(investidor, dia)
    
    for ticker in qtd_fii.keys():
        if ValorDiarioFII.objects.filter(fii__ticker=ticker, data_hora__day=dia.day, data_hora__month=dia.month).exists():
            qtd_fii[ticker] = ValorDiarioFII.objects.filter(fii__ticker=ticker, data_hora__day=dia.day, data_hora__month=dia.month).order_by('-data_hora')[0].preco_unitario * qtd_fii[ticker]
        else:
            qtd_fii[ticker] = HistoricoFII.objects.filter(fii__ticker=ticker, data__lte=dia).order_by('-data')[0].preco_unitario * qtd_fii[ticker]
        
    return qtd_fii

def verificar_se_existe_evento_para_fii(fii, data_limite=datetime.date.today()):
    """
    Verifica se existe evento para fii até data (data inclusive)
    Parâmetros: FII
                Data
    Retorno: True caso exista, senão False
    """
    # Verificar se há evento ou se outro FII foi incorporado a este
    return any([classe.objects.filter(fii=fii, data__lte=data_limite).exists() for classe in EventoFII.__subclasses__()]) \
        or EventoIncorporacaoFII.objects.filter(novo_fii=fii, data__lte=data_limite).exists()
        
def verificar_se_existe_evento_para_fii_periodo(fii, data_inicio, data_fim):
    """
    Verifica se existe evento para fii no período (datas inclusive)
    Parâmetros: FII
                Data de início
                Data de fim
    Retorno: True caso exista, senão False
    """
    # Verificar se há evento ou se outro FII foi incorporado a este
    return any([classe.objects.filter(fii=fii, data__range=[data_inicio, data_fim]).exists() for classe in EventoFII.__subclasses__()]) \
        or EventoIncorporacaoFII.objects.filter(novo_fii=fii, data__range=[data_inicio, data_fim]).exists()
