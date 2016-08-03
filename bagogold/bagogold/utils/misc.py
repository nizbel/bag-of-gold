# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import HistoricoIPCA
from decimal import Decimal
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
            print campos
            for mes in range(1,13):
                try:
                    print 'Ano:', campos[0], 'Mes:', mes, 'Valor:', Decimal(campos[mes].replace(',', '.'))
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