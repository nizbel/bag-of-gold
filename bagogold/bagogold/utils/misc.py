# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import UsoProventosOperacaoAcao
from bagogold.bagogold.models.fii import UsoProventosOperacaoFII
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import HistoricoIPCA, OperacaoTitulo
from decimal import Decimal
from difflib import SequenceMatcher
from urllib2 import Request, urlopen, URLError, HTTPError
import datetime
import math
import random
import re
import time


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
               
def buscar_valores_diarios_selic(data_inicial=datetime.date.today() - datetime.timedelta(days=30), data_final=datetime.date.today()):
    """
    Retorna os valores da taxa SELIC pelo site do Banco Central
    Parâmetros: Data inicial
                Data final
    Retorno: Lista com tuplas (data, fator diário)
    """
    if data_final < data_inicial:
        raise ValueError('Data final deve ser igual ou posterior a data inicial')
    # Verifica se o intervalo entre as datas inicial e final é menor do que 10 anos
    if data_final.year - data_inicial.year > 10:
        raise ValueError('Intervalo deve ser inferior a 10 anos')
    elif data_final.year - data_inicial.year == 10:
        if data_final.month > data_inicial.month:
            raise ValueError('Intervalo deve ser inferior a 10 anos')
        elif data_final.month == data_inicial.month:
            if data_final.day > data_inicial.day:
                raise ValueError('Intervalo deve ser inferior a 10 anos')
    
    # from bagogold.bagogold.utils.misc import buscar_valores_diarios_selic
    # http://www3.bcb.gov.br/selic/consulta/taxaSelic.do?method=listarTaxaDiaria&dataInicial=11/11/2016&dataFinal=16/11/2016&tipoApresentacao=arquivo
    td_url = 'http://www3.bcb.gov.br/selic/consulta/taxaSelic.do?method=listarTaxaDiaria&dataInicial=%s&dataFinal=%s&tipoApresentacao=arquivo' % (data_inicial.strftime('%d/%m/%Y'),
                                                                                                                                                  data_final.strftime('%d/%m/%Y'))
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
        data = response.read()
#         print data
        lista_datas_valores = list()
        # data vem como um arquivo txt separado por linhas com \n e delimitado por ;
        linhas = data.split('\n')
        # ler a partir da terceira linha
        for linha in linhas[2:]:
            dados_linha = linha.split(';')
            if len(dados_linha) > 2:
                try:
                    data = datetime.datetime.strptime(dados_linha[0], '%d/%m/%Y').date()
                except:
                    continue
                fator_diario = Decimal(dados_linha[2].replace(',', '.'))
                if fator_diario.is_zero():
                    continue
                lista_datas_valores.append((data, fator_diario))
        return lista_datas_valores
     
def calcular_rendimentos_ate_data(investidor, data, tipo_investimentos='BCDEFILRT'):
    """
    Calcula os rendimentos de operações até a data especificada, para os tipos de investimento definidos
    Parâmetros: Investidor
                Data final (inclusive)
                Tipo de investimento (seguindo o padrão
    B = Buy and Hold; C = CDB/RDB; D = Tesouro Direto; E = Debêntures; F = FII; I = Fundo de investimento; L = Letra de Crédito; R = CRI/CRA; T = Trading;
    Retorno: Valores de rendimentos para cada tipo de investimento {Tipo: Valor}
    """
    from bagogold.bagogold.models.cdb_rdb import OperacaoCDB_RDB
    from bagogold.bagogold.utils.acoes import calcular_poupanca_prov_acao_ate_dia
    from bagogold.bagogold.utils.cdb_rdb import calcular_valor_cdb_rdb_ate_dia, calcular_valor_venda_cdb_rdb
    from bagogold.bagogold.utils.fii import calcular_poupanca_prov_fii_ate_dia
    from bagogold.bagogold.utils.lc import calcular_valor_lc_ate_dia, calcular_valor_venda_lc
    from bagogold.bagogold.utils.td import calcular_valor_td_ate_dia
    from bagogold.cri_cra.models.cri_cra import OperacaoCRI_CRA
    from bagogold.cri_cra.utils.utils import calcular_valor_cri_cra_ate_dia
    
    rendimentos = {}
    # Ações (Buy and Hold)
    if 'B' in tipo_investimentos:
        rendimentos['B'] = calcular_poupanca_prov_acao_ate_dia(investidor, data) + sum(UsoProventosOperacaoAcao.objects.filter(operacao__investidor=investidor, operacao__data__lte=data).values_list('qtd_utilizada', flat=True))
            
    # CDB/RDB
    if 'C' in tipo_investimentos:
        rendimentos['C'] = sum(calcular_valor_cdb_rdb_ate_dia(investidor, data).values()) \
            - sum([operacao.quantidade for operacao in OperacaoCDB_RDB.objects.filter(investidor=investidor, data__lte=data, tipo_operacao='C')]) \
            + sum([calcular_valor_venda_cdb_rdb(operacao) for operacao in OperacaoCDB_RDB.objects.filter(investidor=investidor, data__lte=data, tipo_operacao='V')])
    
    # Tesouro Direto
    if 'D' in tipo_investimentos:
        rendimentos['D'] = sum(calcular_valor_td_ate_dia(investidor, data).values()) \
            - sum([(operacao.quantidade * operacao.preco_unitario) for operacao in OperacaoTitulo.objects.filter(investidor=investidor, data__lte=data, tipo_operacao='C')]) \
            + sum([(operacao.quantidade * operacao.preco_unitario) for operacao in OperacaoTitulo.objects.filter(investidor=investidor, data__lte=data, tipo_operacao='V')])
    
    # FII
    if 'F' in tipo_investimentos:
        rendimentos['F'] = calcular_poupanca_prov_fii_ate_dia(investidor, data) + sum(UsoProventosOperacaoFII.objects.filter(operacao__investidor=investidor, operacao__data__lte=data).values_list('qtd_utilizada', flat=True))
        
    # Letras de Crédito
    if 'L' in tipo_investimentos:
        rendimentos['L'] = sum(calcular_valor_lc_ate_dia(investidor, data).values()) \
            - sum([operacao.quantidade for operacao in OperacaoLetraCredito.objects.filter(investidor=investidor, data__lte=data, tipo_operacao='C')]) \
            + sum([calcular_valor_venda_lc(operacao) for operacao in OperacaoLetraCredito.objects.filter(investidor=investidor, data__lte=data, tipo_operacao='V')])
    
    # CRI/CRA
    if 'R' in tipo_investimentos:
        rendimentos['R'] = sum(calcular_valor_cri_cra_ate_dia(investidor, data).values()) \
            - sum([(operacao.quantidade * operacao.preco_unitario) for operacao in OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, data__lte=data, tipo_operacao='C')]) \
            + sum([(operacao.quantidade * operacao.preco_unitario) for operacao in OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, data__lte=data, tipo_operacao='V')])
    
    return rendimentos

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

def calcular_domingo_pascoa_no_ano(ano):
    """
    Calcula o domingo de páscoa para o ano especificado. Usado para achar as datas dos feriados eclesiásticos
    Parâmetros: Ano
    Retorno: Dia do domingo de páscoa no ano
    """
    numero_dourado = (ano % 19)
    # Verificar na tabela
    """
    1  14 de abril
    2   3 de abril
    3  23 de março
    4  11 de abril
    5  31 de março
    6  18 de abril
    7   8 de abril
    8  28 de março
    9  16 de abril
    10  5 de abril
    11 25 de março
    12 13 de abril
    13  2 de abril
    14 22 de março
    15 10 de abril
    16 30 de março
    17 17 de abril
    18  7 de abril
    19 27 de março
    """
    data_encontrada = ['14/4', '3/4', '23/3', '11/4', '31/3', '18/4', '8/4', '28/3', '16/4', '5/4', '25/3', '13/4', '2/4', '22/3', '10/4', '30/3', '17/4', '7/4', '27/3'][numero_dourado]
    data_encontrada = datetime.date(ano, int(data_encontrada.split('/')[1]), int(data_encontrada.split('/')[0]))
    # Verifica os próximos 7 dias a fim de encontrar o próximo domingo
    semana_generator = [data_encontrada + datetime.timedelta(days=x) for x in xrange(7)]
    for dia in semana_generator:
        if dia.weekday() == 6:
            return dia
    
def verificar_feriado_bovespa(data):
    """
    Verifica se o dia informado é feriado na Bovespa
    Parâmetros: Data
    Retorno: É feriado?
    """
    dia_mes = (data.day, data.month)
    # Calcular feriados dependentes da páscoa
    domingo_pascoa = calcular_domingo_pascoa_no_ano(data.year)
    carnaval = domingo_pascoa - datetime.timedelta(days=47)
    sexta_santa = domingo_pascoa - datetime.timedelta(days=2)
    corpus_christi = domingo_pascoa + datetime.timedelta(days=60)
    lista_feriados = ((1, 1), # Confraternização Universal
                      (carnaval.day, carnaval.month), # Carnaval
                      (sexta_santa.day, sexta_santa.month), # Sexta-feira santa
                      (corpus_christi.day, corpus_christi.month), # Corpus Christi
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


def formatar_zeros_a_direita_apos_2_casas_decimais(valor):
    """
    Formata um valor removendo zeros a direita após as 2 casas decimais mais significativas
    Parâmetros: Valor (inteiro ou não)
    Retorno: Número formatado com os zeros a direita, após 2 casas decimais, removidos
    """
    if valor == 0:
        return '0.00'
    str_valor_formatado = str(valor)
    if '.' in str_valor_formatado:
        # Formatar número com casas decimais
        parte_inteira = str_valor_formatado.split('.')[0]
        parte_decimal = str_valor_formatado.split('.')[1]
        if len(parte_decimal) < 2:
            parte_decimal = '{:<02}'.format(parte_decimal)
        elif len(parte_decimal) > 2:
            parte_decimal = parte_decimal[:2] + parte_decimal[2:].rstrip('0')
            
        str_valor_formatado = '%s.%s' % (parte_inteira, parte_decimal)
    else:
        # Formatar número inteiro
        str_valor_formatado += '.00'
    
    return str_valor_formatado
    
def ultimo_dia_util():
    dia = datetime.date.today() - datetime.timedelta(days=1)
    while dia.weekday() > 4 or verificar_feriado_bovespa(dia):
        dia = dia - datetime.timedelta(days=1)
    return dia

def verifica_se_dia_util(data):
    """
    Verifica se data passa é dia útil
    Parâmetros: Data
    Retorno:    Se é ou não dia útil
    """
    if data.weekday() > 4 or verificar_feriado_bovespa(data):
        return False
    return True

def buscar_data_aleatoria(data_inicial, data_final):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """
    stime = time.mktime(data_inicial.timetuple())
    etime = time.mktime(data_final.timetuple())

    ptime = stime + random.random() * (etime - stime)

    return datetime.date.fromtimestamp(ptime)

def buscar_dia_util_aleatorio(data_inicial, data_final):
    data_aleatoria = buscar_data_aleatoria(data_inicial, data_final)
    while data_aleatoria.weekday() > 4 or verificar_feriado_bovespa(data_aleatoria):
        data_aleatoria = buscar_data_aleatoria(data_inicial, data_final)
    return data_aleatoria

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()