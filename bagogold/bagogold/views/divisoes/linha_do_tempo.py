# -*- coding: utf-8 -*-
import datetime
from itertools import chain
import json
from operator import attrgetter

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.expressions import F, Case, When, Value
from django.db.models.fields import CharField
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template.response import TemplateResponse

from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoCDB_RDB, \
    TransferenciaEntreDivisoes, DivisaoOperacaoLCI_LCA, DivisaoOperacaoLetraCambio, \
    DivisaoOperacaoCriptomoeda, DivisaoTransferenciaCriptomoeda, \
    DivisaoForkCriptomoeda, DivisaoOperacaoTD
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia_por_divisao
from bagogold.criptomoeda.utils import calcular_valor_moedas_ate_dia_por_divisao
from bagogold.lc.utils import calcular_valor_lc_ate_dia_por_divisao
from bagogold.lci_lca.utils import calcular_valor_lci_lca_ate_dia_por_divisao
from bagogold.tesouro_direto.utils import calcular_valor_titulos_ate_dia_por_divisao


@login_required
@adiciona_titulo_descricao('Linha do tempo de divisão', 'Mostra as transferências e a utilização do dinheiro de uma divisão, ordenadas por data')
def linha_do_tempo(request, divisao_id):
    
    divisao = Divisao.objects.get(id=divisao_id)
    if divisao.investidor != request.user.investidor:
        raise PermissionDenied
    
    if request.is_ajax():
        if 'evento' not in request.GET:
            if request.GET.get('investimento') == Divisao.INVESTIMENTO_LETRAS_CAMBIO_CODIGO:
                eventos = linha_do_tempo_lc(divisao)
            elif request.GET.get('investimento') == Divisao.INVESTIMENTO_CDB_RDB_CODIGO:
                eventos = linha_do_tempo_cdb_rdb(divisao)
            elif request.GET.get('investimento') == Divisao.INVESTIMENTO_LCI_LCA_CODIGO:
                eventos = linha_do_tempo_lci_lca(divisao)
            elif request.GET.get('investimento') == Divisao.INVESTIMENTO_CRIPTOMOEDAS_CODIGO:
                eventos = linha_do_tempo_criptomoedas(divisao)
            elif request.GET.get('investimento') == Divisao.INVESTIMENTO_TESOURO_DIRETO_CODIGO:
                eventos = linha_do_tempo_tesouro_direto(divisao)
                
            return HttpResponse(json.dumps({'sucesso': True, 'linha': render_to_string('divisoes/utils/linha_do_tempo.html', {'eventos': eventos})}), 
                                            content_type = "application/json")
        
        else:
            data_evento = datetime.datetime.strptime(request.GET.get('evento'), '%d/%m/%Y').date()
            
            if request.GET.get('investimento') == Divisao.INVESTIMENTO_LETRAS_CAMBIO_CODIGO:
                saldo = divisao.saldo_lc(data_evento)
                investido = sum(calcular_valor_lc_ate_dia_por_divisao(data_evento, divisao.id).values())
            
            elif request.GET.get('investimento') == Divisao.INVESTIMENTO_CDB_RDB_CODIGO:
                saldo = divisao.saldo_cdb_rdb(data_evento)
                investido = sum(calcular_valor_cdb_rdb_ate_dia_por_divisao(data_evento, divisao.id).values())
            
            elif request.GET.get('investimento') == Divisao.INVESTIMENTO_LCI_LCA_CODIGO:
                saldo = divisao.saldo_lci_lca(data_evento)
                investido = sum(calcular_valor_lci_lca_ate_dia_por_divisao(data_evento, divisao.id).values())
            
            elif request.GET.get('investimento') == Divisao.INVESTIMENTO_CRIPTOMOEDAS_CODIGO:
                saldo = divisao.saldo_criptomoeda(data_evento)
                investido = sum(calcular_valor_moedas_ate_dia_por_divisao(divisao.id, data_evento).values())
            
            elif request.GET.get('investimento') == Divisao.INVESTIMENTO_TESOURO_DIRETO_CODIGO:
                saldo = divisao.saldo_td(data_evento)
                investido = sum(calcular_valor_titulos_ate_dia_por_divisao(data_evento, divisao.id).values())
                
            return HttpResponse(json.dumps({'saldo': str(saldo), 'investido': str(investido), 'data': request.GET.get('evento').replace('/', ''),
                                            'saldo_negativo': (saldo < 0)}), 
                                        content_type = "application/json")
              

    # Preparar tipos de investimentos
    investimentos = Divisao.INVESTIMENTOS_DISPONIVEIS_TIMELINE
        
    return TemplateResponse(request, 'divisoes/linha_do_tempo.html', {'divisao': divisao, 'investimentos': investimentos})


def linha_do_tempo_cdb_rdb(divisao):
    """
    Carrega dados da linha do tempo para CDB/RDB
    
    Parâmetros: Divisão
    Retorno: Eventos no formato para linha do tempo
    """
    class Object(object):
        pass
    
    operacoes_divisao = DivisaoOperacaoCDB_RDB.objects.filter(divisao=divisao).annotate(data=F('operacao__data')) \
        .annotate(titulo=Case(When(operacao__tipo_operacao='C', then=Value(u'Operação de compra', CharField())),
                              When(operacao__tipo_operacao='V', then=Value(u'Operação de venda', CharField())), output_field=CharField())) \
        .select_related('operacao__cdb_rdb')
    for operacao_divisao in operacoes_divisao:
        operacao_divisao.operacao.quantidade = operacao_divisao.quantidade
        operacao_divisao.texto = [operacao_divisao.operacao]
    
    # Transferências
    transf_cedente = TransferenciaEntreDivisoes.objects.filter(divisao_cedente=divisao, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB) \
        .select_related('divisao_cedente', 'divisao_recebedora')
    for transferencia in transf_cedente:
        transferencia.titulo = u'Transferência de recursos da divisão'
        transferencia.texto = [transferencia]
        
    transf_recebedora = TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=divisao, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB) \
        .select_related('divisao_cedente', 'divisao_recebedora')
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
    
#     for evento in eventos:
#         evento.saldo = divisao.saldo_cdb_rdb(evento.data)
#         evento.investido = sum(calcular_valor_cdb_rdb_ate_dia_por_divisao(evento.data, divisao.id).values())
        
    return eventos
    
def linha_do_tempo_criptomoedas(divisao):
    class Object(object):
        pass
    
    # Operações, transferências e forks de criptomoedas
    operacoes_divisao = DivisaoOperacaoCriptomoeda.objects.filter(divisao=divisao).annotate(data=F('operacao__data')) \
        .annotate(titulo=Case(When(operacao__tipo_operacao='C', then=Value(u'Operação de compra', CharField())),
                              When(operacao__tipo_operacao='V', then=Value(u'Operação de venda', CharField())), output_field=CharField()))
    for operacao_divisao in operacoes_divisao:
        operacao_divisao.operacao.quantidade = operacao_divisao.quantidade
        operacao_divisao.texto = [operacao_divisao.operacao]
    
    transferencias_divisao = DivisaoTransferenciaCriptomoeda.objects.filter(divisao=divisao).annotate(data=F('transferencia__data')) \
        .annotate(titulo=Value(u'Transferência de criptomoedas', output_field=CharField()))
    for transferencia_divisao in transferencias_divisao:
        transferencia_divisao.transferencia.quantidade = transferencia_divisao.quantidade
        transferencia_divisao.texto = [transferencia_divisao.transferencia]
        
    forks_divisao = DivisaoForkCriptomoeda.objects.filter(divisao=divisao).annotate(data=F('fork__data')) \
        .annotate(titulo=Value(u'Fork', output_field=CharField()))
    for fork_divisao in forks_divisao:
        fork_divisao.fork.quantidade = fork_divisao.quantidade
        fork_divisao.texto = [fork_divisao.fork]
    
    # Transferências de saldo
    transf_cedente = TransferenciaEntreDivisoes.objects.filter(divisao_cedente=divisao, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRIPTOMOEDA)
    for transferencia in transf_cedente:
        transferencia.titulo = u'Transferência de recursos da divisão'
        transferencia.texto = [transferencia]
        
    transf_recebedora = TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=divisao, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRIPTOMOEDA)
    for transferencia in transf_recebedora:
        transferencia.titulo = u'Transferência de recursos para a divisão'
        transferencia.texto = [transferencia]
        
    eventos = sorted(chain(transf_recebedora, transf_cedente, transferencias_divisao, forks_divisao, operacoes_divisao),
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
            
#     for evento in eventos:
#         evento.saldo = divisao.saldo_criptomoeda(evento.data)
#         evento.investido = sum(calcular_valor_moedas_ate_dia_por_divisao(divisao.id, evento.data).values())
        
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
            
#     for evento in eventos:
#         evento.saldo = divisao.saldo_lc(evento.data)
#         evento.investido = sum(calcular_valor_lc_ate_dia_por_divisao(evento.data, divisao.id).values())
        
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
            
#     for evento in eventos:
#         evento.saldo = divisao.saldo_lci_lca(evento.data)
#         evento.investido = sum(calcular_valor_lci_lca_ate_dia_por_divisao(evento.data, divisao.id).values())
        
    return eventos

def linha_do_tempo_tesouro_direto(divisao):
    """
    Carrega dados da linha do tempo para Tesouro Direto
    
    Parâmetros: Divisão
    Retorno: Eventos no formato para linha do tempo
    """
    class Object(object):
        pass
    
    operacoes_divisao = DivisaoOperacaoTD.objects.filter(divisao=divisao).annotate(data=F('operacao__data')) \
        .annotate(titulo=Case(When(operacao__tipo_operacao='C', then=Value(u'Operação de compra', CharField())),
                              When(operacao__tipo_operacao='V', then=Value(u'Operação de venda', CharField())), output_field=CharField()))
    for operacao_divisao in operacoes_divisao:
        operacao_divisao.operacao.quantidade = operacao_divisao.quantidade
        operacao_divisao.texto = [operacao_divisao.operacao]
    
    # Transferências
    transf_cedente = TransferenciaEntreDivisoes.objects.filter(divisao_cedente=divisao, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TESOURO_DIRETO)
    for transferencia in transf_cedente:
        transferencia.titulo = u'Transferência de recursos da divisão'
        transferencia.texto = [transferencia]
        
    transf_recebedora = TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=divisao, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TESOURO_DIRETO)
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
            
#     for evento in eventos:
#         evento.saldo = divisao.saldo_td(evento.data)
#         evento.investido = sum(calcular_valor_tesouro_direto_ate_dia_por_divisao(evento.data, divisao.id).values())
        
    return eventos