# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from itertools import chain
from operator import attrgetter

from bagogold.bagogold.models.investidores import Investidor
from bagogold.criptomoeda.models import OperacaoCriptomoeda, \
    TransferenciaCriptomoeda, Criptomoeda
from bagogold.criptomoeda.utils import calcular_qtd_moedas_ate_dia


class Command(BaseCommand):
    help = 'Verificar histórico de cripto para pegar preços médios'

    def handle(self, *args, **options):
        investidor = Investidor.objects.get(user__username='nizbel')
        
        cripto_qtd = calcular_qtd_moedas_ate_dia(investidor, datetime.date(2017, 12, 31))
        cripto_qtd = {Criptomoeda.objects.get(id=k).ticker: cripto_qtd[k] for k in cripto_qtd.keys()}
        
        # Adicionar btc cash
        cripto_qtd['BCH'] += Decimal('0.096622723')
#         print cripto_qtd
        
        # Usado para criar objetos vazios
        class Object(object):
            pass
    
        operacoes_compra = OperacaoCriptomoeda.objects.filter(data__lte=datetime.date(2017, 12, 31), investidor=investidor, tipo_operacao='C').order_by('operacaocriptomoedamoeda')
        operacoes_venda = OperacaoCriptomoeda.objects.filter(data__lte=datetime.date(2017, 12, 31), investidor=investidor, tipo_operacao='V').order_by('-operacaocriptomoedamoeda')
        
        transferencias = TransferenciaCriptomoeda.objects.filter(data__lte=datetime.date(2017, 12, 31), investidor=investidor)
        
        lista = sorted(chain(operacoes_compra, operacoes_venda, transferencias), key=attrgetter('data'))
        
        cripto = {}
        
        for item in lista:
            if isinstance(item, OperacaoCriptomoeda):
                if item.criptomoeda.ticker not in cripto.keys():
                    cripto[item.criptomoeda.ticker] = Object()
                    cripto[item.criptomoeda.ticker].preco_medio = 0
                    cripto[item.criptomoeda.ticker].qtd = 0
                    
                    if item.criptomoeda.ticker == 'BCH':
                        # Adicionar btc cash
                        cripto[item.criptomoeda.ticker].qtd += Decimal('0.096622723')
                    
                # Verifica se há taxa cadastrada
                item.taxa = item.taxa()
                
                if item.tipo_operacao == 'C':
                    if item.taxa:
                        # Taxas externas à quantidade comprada
                        if item.taxa.moeda == item.criptomoeda:
                            item.preco_total = (item.quantidade + item.taxa.valor) * item.preco_unitario
                        elif item.taxa.moeda_utilizada() == item.moeda_utilizada():
                            item.preco_total = item.quantidade * item.preco_unitario + item.taxa.valor
                        else:
                            raise ValueError('Moeda utilizada na taxa é inválida')
                    else:
                        item.preco_total = item.quantidade * item.preco_unitario
                    # Movimentações em real contam como dinheiro investido
                    if item.em_real():
                        cripto[item.criptomoeda.ticker].preco_medio = (cripto[item.criptomoeda.ticker].preco_medio * cripto[item.criptomoeda.ticker].qtd \
                                                                               + item.preco_total) / (item.quantidade + cripto[item.criptomoeda.ticker].qtd)
                    else:
                        cripto[item.operacaocriptomoedamoeda.criptomoeda.ticker].qtd -= item.preco_total
                        cripto[item.criptomoeda.ticker].preco_medio = (cripto[item.criptomoeda.ticker].preco_medio * cripto[item.criptomoeda.ticker].qtd \
                                                                               + (item.preco_total * cripto[item.operacaocriptomoedamoeda.criptomoeda.ticker].preco_medio)) \
                                                                                  / (item.quantidade + cripto[item.criptomoeda.ticker].qtd)
                    
                    cripto[item.criptomoeda.ticker].qtd += item.quantidade
                else:
                    # Taxa entra como negativa na conta do valor total da operação
                    if item.taxa:
                        # Taxas são inclusas na quantidade vendida
                        if item.taxa.moeda == item.criptomoeda:
                            item.preco_total = (item.quantidade - item.taxa.valor) * item.preco_unitario
                        elif item.taxa.moeda_utilizada() == item.moeda_utilizada():
                            item.preco_total = item.quantidade * item.preco_unitario - item.taxa.valor
                        else:
                            raise ValueError('Moeda utilizada na taxa é inválida')
                    else:
                        item.preco_total = item.quantidade * item.preco_unitario
                    
                    # Alterar quantidade de moeda utilizada na operação
                    if not item.em_real():
                        cripto[item.operacaocriptomoedamoeda.criptomoeda.ticker].preco_medio = (cripto[item.criptomoeda.ticker].preco_medio * item.quantidade \
                                                                               + (cripto[item.operacaocriptomoedamoeda.criptomoeda.ticker].preco_medio \
                                                                                  * cripto[item.operacaocriptomoedamoeda.criptomoeda.ticker].qtd)) \
                                                                                  / (item.preco_total + cripto[item.operacaocriptomoedamoeda.criptomoeda.ticker].qtd)
                        cripto[item.operacaocriptomoedamoeda.criptomoeda.ticker].qtd += item.preco_total
                        
                    cripto[item.criptomoeda.ticker].qtd -= item.quantidade
            
            elif isinstance(item, TransferenciaCriptomoeda):
                if item.moeda and item.moeda.ticker not in cripto.keys():
                    cripto[item.moeda.ticker] = Object()
                    cripto[item.moeda.ticker].preco_medio = 0
                    cripto[item.moeda.ticker].qtd = 0
                    
                if item.moeda:
                    cripto[item.moeda.ticker].preco_medio = cripto[item.moeda.ticker].preco_medio * cripto[item.moeda.ticker].qtd \
                        / (cripto[item.moeda.ticker].qtd - item.taxa)
                    cripto[item.moeda.ticker].qtd -= item.taxa
                
        # Remover moedas com quantidade vazia
        cripto = {k: cripto[k] for k in cripto.keys() if cripto[k].qtd > 0}
        
        teste = [u'%s: %s\n%s: %s a %s cada\n%s\n' % (key, cripto_qtd[key], key, value.qtd, value.preco_medio,
                                                    value.qtd * value.preco_medio) for key, value in cripto.items()]
        for _ in teste:
            print _