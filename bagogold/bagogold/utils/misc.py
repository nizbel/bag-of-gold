# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao
from bagogold.bagogold.models.fii import OperacaoFII
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import HistoricoIPCA, OperacaoTitulo
from decimal import Decimal
from itertools import chain
from operator import attrgetter
from urllib2 import Request, urlopen, URLError, HTTPError
import datetime
import math
import re


def calcular_iof_regressivo(dias):
    return Decimal(max((100 - (dias * 3 + math.ceil((float(dias)/3)))), 0)/100)

def buscar_historico_ipca():
    td_url = 'http://www.portalbrasil.net/ipca.htm'
    req = Request(td_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
#         print 'Host: %s' % (req.get_host())
        data = response.read()
#         print data
        string_importante = (data[data.find('simplificada'):
                                 data.find('FONTES')])
#         print string_importante
        linhas = re.findall('<tr.*?>.*?</tr>', string_importante, re.MULTILINE|re.DOTALL|re.IGNORECASE)
        for linha in linhas[1:]:
            linha = re.sub('<.*?>', '', linha, flags=re.MULTILINE|re.DOTALL|re.IGNORECASE)
            linha = linha.replace(' ', '').replace('&nbsp;', '')
            campos = re.findall('([\S]*)', linha, re.MULTILINE|re.DOTALL|re.IGNORECASE)
            campos = filter(bool, campos)
#             print campos
            for mes in range(1,13):
                try:
#                     print 'Ano:', campos[0], 'Mes:', mes, 'Valor:', Decimal(campos[mes].replace(',', '.'))
                    historico_ipca = HistoricoIPCA(ano=int(campos[0]), mes=mes, valor=Decimal(campos[mes].replace(',', '.')))
                    historico_ipca.save()
                except:
                    print 'Não foi possível converter', campos[mes]
                    
def trazer_primeiro_registro(queryset):
    """
    Traz o primeiro registro de um queryset
    Parâmetros: Queryset
    Retorno: Primeiro registro ou nulo
    """
    resultado = list(queryset[:1])
    if resultado:
        return resultado[0]
    return None

def verificar_feriado_bovespa(data):
    """
    Verifica se o dia informado é feriado na Bovespa
    Parâmetros: Data
    Retorno: É feriado?
    """
    dia_mes = (data.day, data.month)
    lista_feriados = ((1, 1), # Confraternização Universal
                      (21, 4), # Tiradentes
                      (1, 5), # Dia do trabalho
                      (7, 9), # Independência do Brasil
                      (12, 10), # Nossa Senhora Aparecida
                      (2, 11), # Finados
                      (15, 11), # Proclamação da República
                      (25, 12), # Natal
                      (31, 12), # Ano novo
                      )
    return (dia_mes in lista_feriados)

def qtd_dias_uteis_no_periodo(data_inicial, data_final):
    """
    Calcula a quantidade de dias úteis entre as datas enviadas, incluindo a primeira e excluindo a segunda
    Parâmetros: Data inicial (inclusiva)
                Data final (exclusiva)
    Retorno: Número de dias entre as datas
    """
    # Se data final menor que inicial, retornar erro
    if data_final < data_inicial:
        raise ValueError('Data final deve ser igual ou maior que data inicial')
    daygenerator = (data_inicial + datetime.timedelta(days=x) for x in xrange((data_final - data_inicial).days))
    return sum(1 for day in daygenerator if day.weekday() < 5 and not verificar_feriado_bovespa(day))

def buscar_ultimas_operacoes(investidor, quantidade_operacoes):
    from bagogold.bagogold.models.cdb_rdb import OperacaoCDB_RDB
    """
    Busca as últimas operações feitas pelo investidor, ordenadas por data decrescente
    Parâmetros: Investidor
                Quantidade de operações a ser retornada
    Retorno: Lista com as operações ordenadas por data
    """
    # Juntar todas as operações em uma lista
    operacoes_fii = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    operacoes_td = OperacaoTitulo.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    operacoes_acoes = OperacaoAcao.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    operacoes_lc = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  
    operacoes_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  
    operacoes_fundo_investimento = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    lista_operacoes = sorted(chain(operacoes_fii, operacoes_td, operacoes_acoes, operacoes_lc, operacoes_cdb_rdb, operacoes_fundo_investimento),
                            key=attrgetter('data'), reverse=True)
    
    ultimas_operacoes = lista_operacoes[:min(quantidade_operacoes, len(lista_operacoes))]
    
    return ultimas_operacoes