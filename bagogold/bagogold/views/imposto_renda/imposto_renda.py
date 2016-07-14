# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao, Provento
from bagogold.bagogold.models.cdb_rdb import OperacaoCDB_RDB
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.bagogold.utils.misc import trazer_primeiro_registro
from collections import OrderedDict
from decimal import Decimal
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from itertools import chain
from operator import attrgetter
import datetime

# TODO melhorar isso
def detalhar_imposto_renda(request, ano):
    ano = int(ano)
    investidor = request.user.investidor
    
    class Object(object):
        pass
    operacoes_ano = OperacaoAcao.objects.filter(data__lte='%s-12-31' % (ano), investidor=investidor).order_by('data')
    proventos_ano = Provento.objects.exclude(data_ex__isnull=True).filter(data_ex__range=['%s-1-1' % (ano), '%s-12-31' % (ano)]).order_by('data_ex')
    for provento in proventos_ano:
        provento.data = provento.data_ex
    
    lista_eventos = sorted(chain(operacoes_ano, proventos_ano), key=attrgetter('data'))
    
    ganho_abaixo_vinte_mil = OrderedDict()
    total_abaixo_vinte_mil = Decimal(0)
    ganho_acima_vinte_mil = OrderedDict()
    # Pegar ganhos líquidos por ações até 20.000 reais no mês
    for mes in range(1, 13):
        print mes
        total_mes = Decimal(0)
        lucro_venda = Decimal(0)
        lucro_venda_dt = Decimal(0)
        operacoes_mes = operacoes_ano.filter(data__year=ano, data__month=mes, tipo_operacao='V')
        for operacao in operacoes_mes:
            total_mes += operacao.preco_unitario * operacao.quantidade
            if operacao.destinacao == 'B':
                print 'buy and hold', total_mes
            elif operacao.destinacao == 'T':
                # Pegar compras para ver lucro
                for operacao_compra in operacao.venda.get_queryset().order_by('compra__preco_unitario'):
                    gasto_total_compra = (Decimal(operacao_compra.quantidade) / operacao_compra.compra.quantidade) * \
                        (operacao_compra.compra.quantidade * operacao_compra.compra.preco_unitario + operacao_compra.compra.emolumentos + operacao_compra.compra.corretagem)
                    total_venda = (Decimal(operacao_compra.quantidade) / operacao.quantidade) * \
                        (operacao.quantidade * operacao.preco_unitario - operacao.corretagem - operacao.emolumentos)
                    print 'lucro da venda:', total_venda, '-', gasto_total_compra, (total_venda - gasto_total_compra)
                    if operacao_compra.day_trade:
                        lucro_venda_dt += total_venda - gasto_total_compra
                    else:
                        lucro_venda += total_venda - gasto_total_compra
        if total_mes < 20000 and lucro_venda > 0:
#             print 'mes', mes, lucro_venda
            ganho_abaixo_vinte_mil[mes] = lucro_venda
            total_abaixo_vinte_mil += lucro_venda
        elif total_mes > 20000 or lucro_venda < 0 or lucro_venda_dt != 0:
#             print 'mes', mes, lucro_venda, lucro_venda_dt
            ganho_acima_vinte_mil[mes] = (lucro_venda, lucro_venda_dt)
    
    acoes = {}
    for evento in lista_eventos:
        if evento.acao.ticker not in acoes:
            acoes[evento.acao.ticker] = Object()
            acoes[evento.acao.ticker].quantidade = 0
            acoes[evento.acao.ticker].preco_medio = Decimal(0)
            acoes[evento.acao.ticker].jscp = Decimal(0)
            acoes[evento.acao.ticker].dividendos = Decimal(0)
            acoes[evento.acao.ticker].credito_prox_ano = Decimal(0)
            
        
        # Verificar se é operação
        if isinstance(evento, OperacaoAcao):  
            if evento.tipo_operacao == 'C':
                acoes[evento.acao.ticker].quantidade += evento.quantidade
                acoes[evento.acao.ticker].preco_medio += (evento.quantidade * evento.preco_unitario + \
                    evento.emolumentos + evento.corretagem)
                
            elif evento.tipo_operacao == 'V':
                acoes[evento.acao.ticker].quantidade -= evento.quantidade
                acoes[evento.acao.ticker].preco_medio -= (evento.quantidade * evento.preco_unitario - \
                    evento.emolumentos - evento.corretagem)
        
        # Verificar se é provento
        elif isinstance(evento, Provento):  
            if evento.tipo_provento in ['D', 'J']:
                if evento.data_pagamento >= datetime.date(ano,1,1):
                    total_recebido = acoes[evento.acao.ticker].quantidade * evento.valor_unitario
#                     print evento.acao.ticker, acoes[evento.acao.ticker].quantidade, evento.valor_unitario, total_recebido, 'pagos em', evento.data_pagamento
                    if evento.data_pagamento <= datetime.date(ano,12,31):
                        if evento.tipo_provento == 'J':
                            total_recebido = total_recebido * Decimal(0.85)
                            acoes[evento.acao.ticker].jscp += total_recebido
                        else:
                            acoes[evento.acao.ticker].dividendos += total_recebido
                            print acoes[evento.acao.ticker].dividendos
                    else:
                        if evento.tipo_provento == 'J':
                            total_recebido = total_recebido * Decimal(0.85)
                        acoes[evento.acao.ticker].credito_prox_ano += total_recebido
                    
                
            elif evento.tipo_provento == 'A':
                provento_acao = evento.acaoprovento_set.all()[0]
                if provento_acao.acao_recebida.ticker not in acoes:
                    acoes[provento_acao.acao_recebida.ticker] = Object()
                    acoes[provento_acao.acao_recebida.ticker].quantidade = 0
                    acoes[provento_acao.acao_recebida.ticker].preco_medio = Decimal(0)
                    acoes[provento_acao.acao_recebida.ticker].jscp = Decimal(0)
                    acoes[provento_acao.acao_recebida.ticker].dividendos = Decimal(0)
                    acoes[provento_acao.acao_recebida.ticker].credito_prox_ano = Decimal(0)
                acoes_recebidas = int((acoes[evento.acao.ticker].quantidade * evento.valor_unitario ) / 100 )
                valor_unitario_acoes_recebidas = Decimal(0)
                acoes[provento_acao.acao_recebida.ticker].preco_medio += (acoes_recebidas * valor_unitario_acoes_recebidas)
                acoes[provento_acao.acao_recebida.ticker].quantidade += acoes_recebidas
#                 if provento_acao.valor_calculo_frac > 0:
#                     if provento_acao.data_pagamento_frac <= datetime.date.today():
#                                 print u'recebido fracionado %s, %s ações de %s a %s' % (total_recebido, acoes[evento.acao.ticker], evento.acao.ticker, evento.valor_unitario)
#                         total_gasto += (((acoes[evento.acao.ticker] * evento.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac
#                         total_proventos += (((acoes[evento.acao.ticker] * evento.valor_unitario ) / 100 ) % 1) * provento_acao.valor_calculo_frac

    total_dividendos = Decimal(0)
    total_jscp = Decimal(0)
    for acao in sorted(acoes.keys()):
        total_dividendos += acoes[acao].dividendos
        total_jscp += acoes[acao].jscp
        if acoes[acao].quantidade > 0:
            acoes[acao].preco_medio = (acoes[acao].preco_medio/Decimal(acoes[acao].quantidade))
#             print acao, '->', acoes[acao].quantidade, 'a', acoes[acao].preco_medio, 'Div.:', acoes[acao].dividendos, 'JSCP:', acoes[acao].jscp, 'Ano seguinte:', \
#                 acoes[acao].credito_prox_ano
            
    fiis = {}
    operacoes_fii_ano = OperacaoFII.objects.filter(data__lte='%s-12-31' % (ano), investidor=investidor).order_by('data')
    proventos_fii_ano = ProventoFII.objects.exclude(data_ex__isnull=True).filter(data_ex__range=['%s-1-1' % (ano), '%s-12-31' % (ano)]).order_by('data_ex')
    for provento in proventos_fii_ano:
        provento.data = provento.data_ex
    
    lista_eventos_fii = sorted(chain(operacoes_fii_ano, proventos_fii_ano), key=attrgetter('data'))
    
    # Verificar se é operação
    for evento in lista_eventos_fii:
        if evento.fii.ticker not in fiis:
            fiis[evento.fii.ticker] = Object()
            fiis[evento.fii.ticker].quantidade = 0
            fiis[evento.fii.ticker].preco_medio = Decimal(0)
            fiis[evento.fii.ticker].rendimentos = Decimal(0)
            
        if isinstance(evento, OperacaoFII):
            if evento.tipo_operacao == 'C':
                fiis[evento.fii.ticker].quantidade += evento.quantidade
                fiis[evento.fii.ticker].preco_medio += (evento.quantidade * evento.preco_unitario + \
                    evento.emolumentos + evento.corretagem)
                
            elif evento.tipo_operacao == 'V':
                fiis[evento.fii.ticker].quantidade -= evento.quantidade
                fiis[evento.fii.ticker].preco_medio -= (evento.quantidade * evento.preco_unitario - \
                    evento.emolumentos - evento.corretagem)
                
        # Verificar se é provento
        elif isinstance(evento, ProventoFII):  
            if evento.data_pagamento >= datetime.date(ano,1,1):
                total_recebido = fiis[evento.fii.ticker].quantidade * evento.valor_unitario
#                 print evento.fii.ticker, fiis[evento.fii.ticker].quantidade, evento.valor_unitario, total_recebido, 'pagos em', evento.data_pagamento
                if evento.data_pagamento <= datetime.date(ano,12,31):
                    fiis[evento.fii.ticker].rendimentos += total_recebido
                    print fiis[evento.fii.ticker].rendimentos
                else:
                    fiis[evento.fii.ticker].credito_prox_ano += total_recebido
                        
    total_rendimentos_fii = Decimal(0)
    for fii in fiis.keys():
        total_rendimentos_fii += fiis[fii].rendimentos
        if fiis[fii].quantidade > 0:
            fiis[fii].preco_medio = (fiis[fii].preco_medio/Decimal(fiis[fii].quantidade))
#             print fii, '->', fiis[fii].quantidade, 'a', fiis[fii].preco_medio
            
    # Preparar dados
    dados = {}
    dados['total_dividendos'] = total_dividendos
    dados['total_jscp'] = total_jscp
    dados['total_rendimentos_fii'] = total_rendimentos_fii
    dados['total_abaixo_vinte_mil'] = total_abaixo_vinte_mil
    
    # Editar ano para string
    ano = str(ano).replace('.', '')
    
    return render_to_response('imposto_renda/detalhar_imposto_ano.html', {'ano': ano, 'acoes': acoes, 'fiis': fiis, 'ganho_abaixo_vinte_mil': ganho_abaixo_vinte_mil,
                                                                          'ganho_acima_vinte_mil': ganho_acima_vinte_mil, 'dados': dados}, context_instance=RequestContext(request))

def listar_anos(request):
    class Object(object):
        pass
    investidor = request.user.investidor
    
    lista_primeiras_operacoes = list()
    lista_primeiras_operacoes.append(trazer_primeiro_registro(OperacaoAcao.objects.filter(investidor=investidor).order_by('data')))
    lista_primeiras_operacoes.append(trazer_primeiro_registro(OperacaoCDB_RDB.objects.filter(investidor=investidor).order_by('data')))
    lista_primeiras_operacoes.append(trazer_primeiro_registro(OperacaoFII.objects.filter(investidor=investidor).order_by('data')))
    lista_primeiras_operacoes.append(trazer_primeiro_registro(OperacaoFundoInvestimento.objects.filter(investidor=investidor).order_by('data')))
    lista_primeiras_operacoes.append(trazer_primeiro_registro(OperacaoLetraCredito.objects.filter(investidor=investidor).order_by('data')))
    lista_primeiras_operacoes.append(trazer_primeiro_registro(OperacaoTitulo.objects.filter(investidor=investidor).order_by('data')))
    
    # Remover nulos
    lista_primeiras_operacoes = [operacao for operacao in lista_primeiras_operacoes if operacao != None]
    
    primeiro_ano = min([operacao.data for operacao in lista_primeiras_operacoes]).year
    
    impostos_renda = list()
    
    for ano in range(primeiro_ano, datetime.date.today().year + 1):
        imposto_renda = Object()
        imposto_renda.ano = str(ano).replace('.', '')
        imposto_renda.valor_a_pagar = Decimal(0)
        impostos_renda.append(imposto_renda)
    
    return render_to_response('imposto_renda/listar_anos.html', {'impostos_renda': impostos_renda}, context_instance=RequestContext(request))