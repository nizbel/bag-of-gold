# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao, Provento
from bagogold.bagogold.models.cdb_rdb import OperacaoCDB_RDB
from bagogold.bagogold.models.fii import OperacaoFII
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo
from decimal import Decimal
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import datetime

# TODO melhorar isso
def calcular_preco_medio_ir(request, ano):
    class Object(object):
        pass
    operacoes_ano = OperacaoAcao.objects.filter(data__lte='%s-12-31' % (ano), destinacao='B').order_by('data')
    proventos_ano = Provento.objects.exclude(data_ex__isnull=True).filter(data_ex__range=[operacoes_ano[0].data, '%s-12-31' % (ano)]).order_by('data_ex')
    for provento in proventos_ano:
        provento.data = provento.data_ex
    
    lista_eventos = sorted(chain(operacoes_ano, proventos_ano), key=attrgetter('data'))
    
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
                    print evento.acao.ticker, acoes[evento.acao.ticker].quantidade, evento.valor_unitario, total_recebido, 'pagos em', evento.data_pagamento
                    if evento.data_pagamento <= datetime.date(ano,12,31):
                        if evento.tipo_provento == 'J':
                            total_recebido = total_recebido * Decimal(0.85)
                            acoes[evento.acao.ticker].jscp += total_recebido
                        else:
                            acoes[evento.acao.ticker].dividendos += total_recebido
                    else:
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

    for acao in sorted(acoes.keys()):
        if acoes[acao].quantidade > 0:
            print acao, '->', acoes[acao].quantidade, 'a', (acoes[acao].preco_medio/Decimal(acoes[acao].quantidade)), 'Div.:', acoes[acao].dividendos, 'JSCP:', acoes[acao].jscp, 'Ano seguinte:', \
                acoes[acao].credito_prox_ano
            print acao, '->', acoes[acao].quantidade, 'a', Decimal(format(acoes[acao].preco_medio/Decimal(acoes[acao].quantidade), '.2f')), 'Div.:', Decimal(format(acoes[acao].dividendos, '.2f')), \
                                                                   'JSCP:', Decimal(format(acoes[acao].jscp, '.2f')), 'Ano seguinte:', acoes[acao].credito_prox_ano
            
    fiis = {}
    for operacao in OperacaoFII.objects.filter(data__lte='%s-12-31' % (ano)).order_by('data'):
        if operacao.fii.ticker not in fiis:
            fiis[operacao.fii.ticker] = Object()
            fiis[operacao.fii.ticker].quantidade = 0
            fiis[operacao.fii.ticker].preco_medio = Decimal(0)
            
        if operacao.tipo_operacao == 'C':
            fiis[operacao.fii.ticker].quantidade += operacao.quantidade
            fiis[operacao.fii.ticker].preco_medio += (operacao.quantidade * operacao.preco_unitario + \
                operacao.emolumentos + operacao.corretagem)
            
        elif operacao.tipo_operacao == 'V':
            fiis[operacao.fii.ticker].quantidade -= operacao.quantidade
            fiis[operacao.fii.ticker].preco_medio -= (operacao.quantidade * operacao.preco_unitario - \
                operacao.emolumentos - operacao.corretagem)
    
    for fii in fiis.keys():
        if fiis[fii].quantidade > 0:
            print fii, '->', fiis[fii].quantidade, 'a', (fiis[fii].preco_medio/Decimal(fiis[fii].quantidade))
            
    return render_to_response('imposto_renda/imposto_renda.html', {}, context_instance=RequestContext(request))

def listar_anos(request):
    investidor = request.user.investidor
    
    primeira_operacao_acoes = OperacaoAcao.objects.filter(investidor=investidor).order_by('data')[0]
    primeira_operacao_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor).order_by('data')[0]
    primeira_operacao_fii = OperacaoFII.objects.filter(investidor=investidor).order_by('data')[0]
    primeira_operacao_fundo_investimento = OperacaoFundoInvestimento.objects.filter(investidor=investidor).order_by('data')[0]
    primeira_operacao_lc = OperacaoLetraCredito.objects.filter(investidor=investidor).order_by('data')[0]
    primeira_operacao_td = OperacaoTitulo.objects.filter(investidor=investidor).order_by('data')[0]
    
    primeiro_ano = min(primeira_operacao_acoes.data, primeira_operacao_cdb_rdb.data, primeira_operacao_fii.data, primeira_operacao_fundo_investimento.data, \
                       primeira_operacao_lc.data, primeira_operacao_td.data).year
    
    anos = range(primeiro_ano, datetime.date.today().year + 1)
    
    return render_to_response('imposto_renda/listar_anos.html', {'anos': anos}, context_instance=RequestContext(request))