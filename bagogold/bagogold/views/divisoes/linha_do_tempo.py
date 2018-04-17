# -*- coding: utf-8 -*-
import datetime
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.expressions import F, Case, When, Value
from django.template.loader import render_to_string
from itertools import chain
import json
from operator import attrgetter

from django.db.models.fields import CharField
from django.http import HttpResponse
from django.template.response import TemplateResponse

from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoCDB_RDB, \
    TransferenciaEntreDivisoes, DivisaoOperacaoLCI_LCA, DivisaoOperacaoLetraCambio
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia_por_divisao
from bagogold.lc.utils import calcular_valor_lc_ate_dia_por_divisao
from bagogold.lci_lca.utils import calcular_valor_lci_lca_ate_dia_por_divisao


@login_required
@adiciona_titulo_descricao('Linha do tempo de divisão', 'Mostra as transferências e a utilização do dinheiro de uma divisão, ordenadas por data')
def linha_do_tempo(request, divisao_id):
    
    divisao = Divisao.objects.get(id=divisao_id)
    if divisao.investidor != request.user.investidor:
        raise PermissionDenied
    
    if request.is_ajax():
        if request.GET.get('investimento') == 'A':
            eventos = linha_do_tempo_lc(divisao)
        if request.GET.get('investimento') == 'C':
            eventos = linha_do_tempo_cdb_rdb(divisao)
        if request.GET.get('investimento') == 'L':
            eventos = linha_do_tempo_lci_lca(divisao)
            
        return HttpResponse(json.dumps({'sucesso': True, 'linha': render_to_string('divisoes/utils/linha_do_tempo.html', {'eventos': eventos})}), 
                                        content_type = "application/json")  

    # Preparar tipos de investimentos
    investimentos = {'A': u'Letra de Câmbio', 'C': u'CDB/RDB', 'L': u'LCI/LCA'}
        
    return TemplateResponse(request, 'divisoes/linha_do_tempo.html', {'divisao': divisao, 'investimentos': investimentos})


def linha_do_tempo_cdb_rdb(divisao):
    class Object(object):
        pass
    
    operacoes_divisao = DivisaoOperacaoCDB_RDB.objects.filter(divisao=divisao).annotate(data=F('operacao__data')) \
        .annotate(titulo=Case(When(operacao__tipo_operacao='C', then=Value(u'Operação de compra', CharField())),
                              When(operacao__tipo_operacao='V', then=Value(u'Operação de venda', CharField())), output_field=CharField()))
    for operacao_divisao in operacoes_divisao:
        operacao_divisao.operacao.quantidade = operacao_divisao.quantidade
        operacao_divisao.texto = [operacao_divisao.operacao]
    
    # Transferências
    transf_cedente = TransferenciaEntreDivisoes.objects.filter(divisao_cedente=divisao, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB)
    for transferencia in transf_cedente:
        transferencia.titulo = u'Transferência de recursos da divisão'
        transferencia.texto = [transferencia]
        
    transf_recebedora = TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=divisao, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB)
    for transferencia in transf_recebedora:
        transferencia.titulo = u'Transferência de recursos para a divisão'
        transferencia.texto = [transferencia]
        
    eventos = sorted(chain(transf_recebedora, transf_cedente, operacoes_divisao),
                            key=attrgetter('data'))

    for indice, evento in enumerate(eventos):
        # Verifica se há próximo evento
        while indice + 1 < len(eventos) and eventos[indice + 1].data == evento.data:
            evento_repetido = eventos.pop(indice + 1)
            evento.titulo = u'Múltiplos eventos'
            evento.texto.extend(evento_repetido.texto)
            
    # Adicionar data atual para garantir que sempre haja pelo menos 1 evento
    if len(eventos) == 0 or eventos[-1].data < datetime.date.today():
        evento = Object()
        evento.titulo = u'Data atual'
        evento.texto = [u'Situação na data atual']
        evento.data = datetime.date.today()
        eventos.append(evento)        
    
    for evento in eventos:
        evento.saldo = divisao.saldo_cdb_rdb(evento.data)
        evento.investido = sum(calcular_valor_cdb_rdb_ate_dia_por_divisao(evento.data, divisao.id).values())
        
    return eventos

def linha_do_tempo_lc(divisao):
    class Object(object):
        pass
    
    operacoes_divisao = DivisaoOperacaoLetraCambio.objects.filter(divisao=divisao).annotate(data=F('operacao__data')) \
        .annotate(titulo=Case(When(operacao__tipo_operacao='C', then=Value(u'Operação de compra', CharField())),
                              When(operacao__tipo_operacao='V', then=Value(u'Operação de venda', CharField())), output_field=CharField()))
    for operacao_divisao in operacoes_divisao:
        operacao_divisao.operacao.quantidade = operacao_divisao.quantidade
        operacao_divisao.texto = [operacao_divisao.operacao]
    
    # Transferências
    transf_cedente = TransferenciaEntreDivisoes.objects.filter(divisao_cedente=divisao, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LC)
    for transferencia in transf_cedente:
        transferencia.titulo = u'Transferência de recursos da divisão'
        transferencia.texto = [transferencia]
        
    transf_recebedora = TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=divisao, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LC)
    for transferencia in transf_recebedora:
        transferencia.titulo = u'Transferência de recursos para a divisão'
        transferencia.texto = [transferencia]
        
    eventos = sorted(chain(transf_recebedora, transf_cedente, operacoes_divisao),
                            key=attrgetter('data'))

    for indice, evento in enumerate(eventos):
        # Verifica se há próximo evento
        while indice + 1 < len(eventos) and eventos[indice + 1].data == evento.data:
            evento_repetido = eventos.pop(indice + 1)
            evento.titulo = u'Múltiplos eventos'
            evento.texto.extend(evento_repetido.texto)
            
    # Adicionar data atual para garantir que sempre haja pelo menos 1 evento
    if len(eventos) == 0 or eventos[-1].data < datetime.date.today():
        evento = Object()
        evento.titulo = u'Data atual'
        evento.texto = [u'Situação na data atual']
        evento.data = datetime.date.today()
        eventos.append(evento)        
            
    for evento in eventos:
        evento.saldo = divisao.saldo_lc(evento.data)
        evento.investido = sum(calcular_valor_lc_ate_dia_por_divisao(evento.data, divisao.id).values())
        
    return eventos

def linha_do_tempo_lci_lca(divisao):
    class Object(object):
        pass
    
    operacoes_divisao = DivisaoOperacaoLCI_LCA.objects.filter(divisao=divisao).annotate(data=F('operacao__data')) \
        .annotate(titulo=Case(When(operacao__tipo_operacao='C', then=Value(u'Operação de compra', CharField())),
                              When(operacao__tipo_operacao='V', then=Value(u'Operação de venda', CharField())), output_field=CharField()))
    for operacao_divisao in operacoes_divisao:
        operacao_divisao.operacao.quantidade = operacao_divisao.quantidade
        operacao_divisao.texto = [operacao_divisao.operacao]
    
    # Transferências
    transf_cedente = TransferenciaEntreDivisoes.objects.filter(divisao_cedente=divisao, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LCI_LCA)
    for transferencia in transf_cedente:
        transferencia.titulo = u'Transferência de recursos da divisão'
        transferencia.texto = [transferencia]
        
    transf_recebedora = TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=divisao, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LCI_LCA)
    for transferencia in transf_recebedora:
        transferencia.titulo = u'Transferência de recursos para a divisão'
        transferencia.texto = [transferencia]
        
    eventos = sorted(chain(transf_recebedora, transf_cedente, operacoes_divisao),
                            key=attrgetter('data'))

    for indice, evento in enumerate(eventos):
        # Verifica se há próximo evento
        while indice + 1 < len(eventos) and eventos[indice + 1].data == evento.data:
            evento_repetido = eventos.pop(indice + 1)
            evento.titulo = u'Múltiplos eventos'
            evento.texto.extend(evento_repetido.texto)
            
    # Adicionar data atual para garantir que sempre haja pelo menos 1 evento
    if len(eventos) == 0 or eventos[-1].data < datetime.date.today():
        evento = Object()
        evento.titulo = u'Data atual'
        evento.texto = [u'Situação na data atual']
        evento.data = datetime.date.today()
        eventos.append(evento)        
            
    for evento in eventos:
        evento.saldo = divisao.saldo_lci_lca(evento.data)
        evento.investido = sum(calcular_valor_lci_lca_ate_dia_por_divisao(evento.data, divisao.id).values())
        
    return eventos