# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao, Provento
from bagogold.bagogold.models.cdb_rdb import OperacaoCDB_RDB
from bagogold.bagogold.models.fii import OperacaoFII, ProventoFII
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento
from bagogold.bagogold.models.lc import OperacaoLetraCredito, LetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo, Titulo, HistoricoTitulo
from bagogold.bagogold.utils.lc import calcular_valor_lc_ate_dia
from bagogold.bagogold.utils.misc import trazer_primeiro_registro
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia_por_titulo
from collections import OrderedDict
from decimal import Decimal, ROUND_FLOOR
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
    
    ############################################################
    ### Ações ##################################################
    ############################################################
    
    operacoes_ano = OperacaoAcao.objects.filter(data__lte='%s-12-31' % (ano), investidor=investidor).order_by('data')
    proventos_ano = Provento.objects.exclude(data_ex__isnull=True).filter(data_ex__range=['%s-1-1' % (ano), '%s-12-31' % (ano)]).order_by('data_ex')
    for provento in proventos_ano:
        provento.data = provento.data_ex
    
    lista_eventos = sorted(chain(operacoes_ano, proventos_ano), key=attrgetter('data'))
    
    # Variáveis para cálculo de ganhos em renda variável por mes
    total_mes = OrderedDict()
    ganho_abaixo_vinte_mil = OrderedDict()
    total_abaixo_vinte_mil = Decimal(0)
    ganho_acima_vinte_mil = OrderedDict()
    lucro_venda = OrderedDict()
    lucro_venda_dt = OrderedDict()
    
    # Inicializar variáveis
    for mes_atual in range(1, 13):
        total_mes[mes_atual] = Decimal(0)
        ganho_abaixo_vinte_mil[mes_atual] = Decimal(0)
        ganho_acima_vinte_mil[mes_atual] = (Decimal(0), Decimal(0))
        lucro_venda[mes_atual] = Decimal(0)
        lucro_venda_dt[mes_atual] = Decimal(0)
    
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
                # Apurar ganhos de renda variável
                if evento.data.year == ano:
                    mes_atual = evento.data.month
                    total_mes[mes_atual] += evento.preco_unitario * evento.quantidade
                    if evento.destinacao == 'B':
                        total_venda = (evento.quantidade * evento.preco_unitario - evento.corretagem - evento.emolumentos)
                        lucro_venda[mes_atual] += total_venda - (acoes[evento.acao.ticker].preco_medio / acoes[evento.acao.ticker].quantidade) * evento.quantidade
                    elif evento.destinacao == 'T':
                        # Pegar compras para ver lucro
                        for evento_compra in evento.venda.get_queryset().order_by('compra__preco_unitario'):
                            gasto_total_compra = (Decimal(evento_compra.quantidade) / evento_compra.compra.quantidade) * \
                                (evento_compra.compra.quantidade * evento_compra.compra.preco_unitario + evento_compra.compra.emolumentos + evento_compra.compra.corretagem)
                            total_venda = (Decimal(evento_compra.quantidade) / evento.quantidade) * \
                                (evento.quantidade * evento.preco_unitario - evento.corretagem - evento.emolumentos)
                            print 'lucro da venda:', total_venda, '-', gasto_total_compra, (total_venda - gasto_total_compra)
                            if evento_compra.day_trade:
                                lucro_venda_dt[mes_atual] += total_venda - gasto_total_compra
                            else:
                                lucro_venda[mes_atual] += total_venda - gasto_total_compra
                                
                # Alterar dados da ação atual
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
#                             print acoes[evento.acao.ticker].dividendos
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

    # Pegar ganhos líquidos por ações até 20.000 reais no mês
    for mes in range(1, 13):
        print mes
        if total_mes[mes] < 20000 and lucro_venda[mes] > 0:
#             print 'mes', mes, lucro_venda
            ganho_abaixo_vinte_mil[mes] = lucro_venda[mes]
            total_abaixo_vinte_mil += lucro_venda[mes]
        elif total_mes > 20000 or lucro_venda < 0 or lucro_venda_dt != 0:
#             print 'mes', mes, lucro_venda, lucro_venda_dt
            ganho_acima_vinte_mil[mes] = (lucro_venda[mes], lucro_venda_dt[mes])
    
    total_dividendos = Decimal(0)
    total_jscp = Decimal(0)
    for acao in sorted(acoes.keys()):
        total_dividendos += acoes[acao].dividendos
        total_jscp += acoes[acao].jscp
        if acoes[acao].quantidade > 0:
            acoes[acao].preco_medio = (acoes[acao].preco_medio/Decimal(acoes[acao].quantidade)).quantize(Decimal('0.0001'))
#             print acao, '->', acoes[acao].quantidade, 'a', acoes[acao].preco_medio, 'Div.:', acoes[acao].dividendos, 'JSCP:', acoes[acao].jscp, 'Ano seguinte:', \
#                 acoes[acao].credito_prox_ano
            
    ############################################################
    ### Letras de Crédito ######################################
    ############################################################
    
    cdb_rdb = {}
     
#     for letra_credito_id, valor in calcular_valor_lc_ate_dia(investidor, datetime.date(ano, 12, 31)).items():
#         lc = LetraCredito.objects.get(id=letra_credito_id, investidor=investidor)
#         letras_credito[lc.nome] = valor
    for operacao in OperacaoCDB_RDB.objects.filter(data__lte='%s-12-31' % (ano), investidor=investidor).order_by('data'):
        if operacao.investimento.nome not in cdb_rdb:
            cdb_rdb[operacao.investimento.nome] = Decimal(0)
        if operacao.tipo_operacao == 'C':
            cdb_rdb[operacao.investimento.nome] += operacao.quantidade
        elif operacao.tipo_operacao == 'V':
            cdb_rdb[operacao.investimento.nome] -= operacao.quantidade
            
            
    ############################################################
    ### Fundo de investimento imobiliário ######################
    ############################################################
    
    fiis = {}
    operacoes_fii_ano = OperacaoFII.objects.filter(data__lte='%s-12-31' % (ano), investidor=investidor).order_by('data')
    proventos_fii_ano = ProventoFII.objects.exclude(data_ex__isnull=True).filter(data_pagamento__range=['%s-1-1' % (ano), '%s-12-31' % (ano)], data_ex__range=['%s-1-1' % (ano), '%s-12-31' % (ano)]).order_by('data_ex')
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
            fiis[fii].preco_medio = (fiis[fii].preco_medio/Decimal(fiis[fii].quantidade)).quantize(Decimal('0.0001'))
#             print fii, '->', fiis[fii].quantidade, 'a', fiis[fii].preco_medio
            
            
    ############################################################
    ### Letras de Crédito ######################################
    ############################################################
    
    letras_credito = {}
     
#     for letra_credito_id, valor in calcular_valor_lc_ate_dia(investidor, datetime.date(ano, 12, 31)).items():
#         lc = LetraCredito.objects.get(id=letra_credito_id, investidor=investidor)
#         letras_credito[lc.nome] = valor
    for operacao in OperacaoLetraCredito.objects.filter(data__lte='%s-12-31' % (ano), investidor=investidor).order_by('data'):
        if operacao.letra_credito.nome not in letras_credito:
            letras_credito[operacao.letra_credito.nome] = Decimal(0)
        if operacao.tipo_operacao == 'C':
            letras_credito[operacao.letra_credito.nome] += operacao.quantidade
        elif operacao.tipo_operacao == 'V':
            letras_credito[operacao.letra_credito.nome] -= operacao.quantidade
    
            
    ############################################################
    ### Tesouro Direto #########################################
    ############################################################
    
    # Para IR devem ser acumulados os valores de compra das operações
    operacoes_td = OperacaoTitulo.objects.filter(data__lte='%s-12-31' % (ano), investidor=investidor).order_by('data')
    
    # Lista para guardar as operações de compra remanescentes
    operacoes_td_lista = list(operacoes_td.filter(tipo_operacao='C'))
    
    for operacao_venda in operacoes_td.filter(tipo_operacao='V'):
        for operacao_compra in [operacao_lista for operacao_lista in operacoes_td_lista if operacao_lista.titulo==operacao_venda.titulo]:
            if operacao_venda.quantidade == operacao_compra.quantidade:
                operacoes_td_lista.remove(operacao_compra)
                break
            elif operacao_venda.quantidade > operacao_compra.quantidade:
                operacao_venda.quantidade -= operacao_compra.quantidade
                operacoes_td_lista.remove(operacao_compra)
            elif operacao_venda.quantidade < operacao_compra.quantidade:
                operacao_compra.quantidade -= operacao_venda.quantidade
                break
    
    total_acumulado_td = Decimal(0)
    
    for operacao in operacoes_td_lista:
        total_acumulado_td += (operacao.preco_unitario * operacao.quantidade).quantize(Decimal('0.01'), ROUND_FLOOR)
    
    # Preparar dados
    dados = {}
    dados['total_dividendos'] = total_dividendos
    dados['total_jscp'] = total_jscp
    dados['total_rendimentos_fii'] = total_rendimentos_fii
    dados['total_abaixo_vinte_mil'] = total_abaixo_vinte_mil
    dados['total_acumulado_td'] = total_acumulado_td
    
    # Editar ano para string
    ano = str(ano).replace('.', '')
    
    return render_to_response('imposto_renda/detalhar_imposto_ano.html', {'ano': ano, 'acoes': acoes, 'cdb_rdb': cdb_rdb, 'fiis': fiis, 'ganho_abaixo_vinte_mil': ganho_abaixo_vinte_mil,
                                                                          'ganho_acima_vinte_mil': ganho_acima_vinte_mil, 'letras_credito': letras_credito,'dados': dados}, context_instance=RequestContext(request))

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