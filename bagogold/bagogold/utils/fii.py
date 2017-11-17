# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII, \
    ValorDiarioFII, HistoricoFII, EventoAgrupamentoFII, EventoDesdobramentoFII, \
    EventoFII, EventoIncorporacaoFII, FII
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
    operacoes = OperacaoFII.objects.filter(investidor=investidor,data__lte=dia).order_by('data')
    
    # Remover valores repetidos
    fiis = list(set(operacoes.values_list('fii', flat=True)))

    proventos = ProventoFII.objects.filter(data_ex__lte=dia, fii__in=fiis).annotate(data=F('data_ex')).order_by('data_ex')
#     for provento in proventos:
#         provento.data = provento.data_ex
     
    lista_conjunta = sorted(chain(proventos, operacoes),
                            key=attrgetter('data'))
    
    total_proventos = Decimal(0)
    
    # Guarda as cotas correntes para o calculo do patrimonio
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

def calcular_poupanca_prov_fii_ate_dia_por_divisao(dia, divisao):
    """
    Calcula a quantidade de proventos provisionada até dia determinado para uma divisão para FII
    Parâmetros: Dia da posição de proventos
                Divisão escolhida
    Retorno: Quantidade provisionada no dia
    """
    operacoes_divisao = DivisaoOperacaoFII.objects.filter(divisao=divisao, operacao__data__lte=dia).values_list('operacao__id', flat=True)
    
    operacoes = OperacaoFII.objects.filter(id__in=operacoes_divisao).order_by('data')

    proventos = ProventoFII.objects.filter(data_ex__lte=dia).order_by('data_ex')
    for provento in proventos:
        provento.data = provento.data_ex
     
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

def calcular_qtd_fiis_ate_dia(investidor, dia):
    """ 
    Calcula a quantidade de FIIs até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de FIIs {ticker: qtd}
    """
    if not all([verificar_se_existe_evento_para_fii(fii, dia) for fii in FII.objects.filter(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
                                                                                            .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True))]):
        qtd_fii = dict(OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).annotate(ticker=F('fii__ticker')).values('ticker') \
            .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                                When(tipo_operacao='V', then=F('quantidade')*-1),
                                output_field=DecimalField()))).values_list('ticker', 'total').exclude(total=0))
    
    else:
        qtd_fii = {}
        for fii in FII.objects.filter(id__in=OperacaoFII.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True) \
                                                                                            .order_by('fii__id').distinct('fii__id').values_list('fii', flat=True)):
            qtd_fii_na_data = calcular_qtd_fiis_ate_dia_por_ticker(investidor, dia, fii.ticker)
            if qtd_fii_na_data > 0:
                qtd_fii[fii.ticker] = qtd_fii_na_data
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
    if not verificar_se_existe_evento_para_fii(FII.objects.get(ticker=ticker), dia):
        qtd_fii = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True) \
            .aggregate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                                      When(tipo_operacao='V', then=F('quantidade')*-1),
                                      output_field=DecimalField())))['total'] or 0
    else:
        qtd_fii = 0
        
        operacoes = OperacaoFII.objects.filter(fii__ticker=ticker, data__lte=dia, investidor=investidor).exclude(data__isnull=True) \
            .annotate(qtd_final=(Case(When(tipo_operacao='C', then=F('quantidade')),
                                      When(tipo_operacao='V', then=F('quantidade')*-1),
                                      output_field=DecimalField()))).annotate(tipo=Value(u'Operação', output_field=CharField()))
                                      
                                      
        # Verificar agrupamentos e desdobramentos
        agrupamentos = EventoAgrupamentoFII.objects.filter(fii__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))

        desdobramentos = EventoDesdobramentoFII.objects.filter(fii__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
        
        incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__ticker=ticker, data__lte=dia) | Q(novo_fii__ticker=ticker, data__lte=dia)).exclude(id=ignorar_incorporacao_id) \
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
    if not all([verificar_se_existe_evento_para_fii(fii, dia) for fii in FII.objects.filter(id__in=DivisaoOperacaoFII.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id) \
                                                                                            .order_by('operacao__fii__id').distinct('operacao__fii__id').values_list('operacao__fii', flat=True))]):
        qtd_fii = dict(DivisaoOperacaoFII.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).annotate(ticker=F('operacao__fii__ticker')) \
            .values('ticker').annotate(qtd=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                                When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                                output_field=DecimalField()))).values_list('ticker', 'qtd').exclude(qtd=0))
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
    Retorno: Quantidade de FIIs para o ticker determinado
    """
    if not verificar_se_existe_evento_para_fii(FII.objects.get(ticker=ticker), dia):
        qtd_fii = DivisaoOperacaoFII.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id, operacao__fii__ticker=ticker) \
                       .aggregate(qtd=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                                When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                                output_field=DecimalField())))['qtd'] or 0
    else:
        qtd_fii = 0
        
        operacoes = DivisaoOperacaoFII.objects.filter(operacao__fii__ticker=ticker, operacao__data__lte=dia, divisao__id=divisao_id) \
            .annotate(qtd_final=(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                                      When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                                      output_field=DecimalField()))).annotate(data=F('operacao__data')).annotate(tipo=Value(u'Operação', output_field=CharField()))
                                      
                                      
        # Verificar agrupamentos e desdobramentos
        agrupamentos = EventoAgrupamentoFII.objects.filter(fii__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Agrupamento', output_field=CharField()))

        desdobramentos = EventoDesdobramentoFII.objects.filter(fii__ticker=ticker, data__lte=dia).annotate(tipo=Value(u'Desdobramento', output_field=CharField()))
        
        incorporacoes = EventoIncorporacaoFII.objects.filter(Q(fii__ticker=ticker, data__lte=dia) | Q(novo_fii__ticker=ticker, data__lte=dia)).exclude(id=ignorar_incorporacao_id) \
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
    # Verificar se há evento ou se outro FII foi incorporado a este
    return any([classe.objects.filter(fii=fii, data__lte=data_limite).exists() for classe in EventoFII.__subclasses__()]) \
        or EventoIncorporacaoFII.objects.filter(novo_fii=fii, data__lte=data_limite).exists()
