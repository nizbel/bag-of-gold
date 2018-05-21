# -*- coding: utf-8 -*-
from StringIO import StringIO
import calendar
import datetime
from decimal import Decimal
from django.db.models.query_utils import Q
from ftplib import FTP
import re
from urllib2 import Request, urlopen
import zipfile

from django.db import transaction
from django.db.models.aggregates import Count
import pyexcel

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI, \
    HistoricoIPCA, HistoricoTaxaSelic, IPCAProjetado
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo
import pyexcel.ext.xls


def calcular_valor_atualizado_com_taxa_di(taxa_do_dia, valor_atual, operacao_taxa):
    """
    Calcula o valor atualizado de uma operação vinculada ao DI, a partir da taxa DI do dia
    
    Parâmetros: Taxa DI do dia
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa DI
    """
    return ((pow((Decimal(1) + taxa_do_dia/100), Decimal(1)/Decimal(252)) - Decimal(1)) * operacao_taxa/100 + Decimal(1)) * valor_atual

def calcular_valor_atualizado_com_taxa_prefixado(valor_atual, operacao_taxa, qtd_dias=1):
    """
    Calcula o valor atualizado de uma operação em renda fixa prefixada, a partir da quantidade de dias do período
    
    Parâmetros: Valor atual da operação
                Taxa da operação
                Quantidade de dias
    Retorno: Valor atualizado com a taxa de um dia prefixado
    """
    return pow((Decimal(1) + operacao_taxa/100), Decimal(qtd_dias)/Decimal(252)) * valor_atual

def calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, valor_atual, operacao_taxa):
    """
    Calcula o valor atualizado de uma operação vinculada ao DI, a partir das taxa DI dos dias
    
    Parâmetros: Taxas DI dos dias {taxa(Decimal): quantidade_de_dias}
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa DI
    """
    taxa_acumulada = 1
    for taxa_do_dia in taxas_dos_dias.keys():
        taxa_acumulada *= pow(((pow((Decimal(1) + taxa_do_dia/100), Decimal(1)/Decimal(252)) - Decimal(1)) * operacao_taxa/100 + Decimal(1)), taxas_dos_dias[taxa_do_dia])
    return taxa_acumulada * valor_atual

def calcular_valor_atualizado_com_taxas_di_e_juros(taxas_dos_dias, valor_atual, operacao_taxa, juros):
    """
    Calcula o valor atualizado de uma operação vinculada ao DI, a partir das taxa DI dos dias
    
    Parâmetros: Taxas DI dos dias {taxa(Decimal): quantidade_de_dias}
                Valor atual da operação
                Taxa da operação
                Juros (percentual ao ano)
    Retorno: Valor atualizado com a taxa DI
    """
    taxa_acumulada = 1
    juros = Decimal(juros)
    for taxa_do_dia in taxas_dos_dias.keys():
        taxa_acumulada *= pow((((pow((Decimal(1) + taxa_do_dia/100), Decimal(1)/Decimal(252)) - Decimal(1)) * operacao_taxa/100 + Decimal(1)) * \
                               pow((Decimal(1) + juros/100), Decimal(1)/Decimal(252))), taxas_dos_dias[taxa_do_dia])
    return taxa_acumulada * valor_atual

def calcular_valor_atualizado_com_taxa_selic(taxa_do_dia, valor_atual):
    """
    Calcula o valor atualizado de uma operação vinculada ao Selic, a partir da taxa Selic do dia
    
    Parâmetros: Taxa Selic do dia
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa Selic
    """
    return taxa_do_dia * valor_atual

def calcular_valor_atualizado_com_taxas_selic(taxas_dos_dias, valor_atual):
    """
    Calcula o valor atualizado de uma operação vinculada ao Selic, a partir das taxa Selic dos dias
    
    Parâmetros: Taxas Selic dos dias {taxa(Decimal): quantidade_de_dias}
                Valor atual da operação
                Taxa da operação
    Retorno: Valor atualizado com a taxa Selic
    """
    taxa_acumulada = 1
    for taxa_do_dia in taxas_dos_dias.keys():
        taxa_acumulada *= pow(taxa_do_dia, taxas_dos_dias[taxa_do_dia])
    return taxa_acumulada * valor_atual

def calcular_valor_acumulado_ipca(data_base, data_final=datetime.date.today()):
    """
    Calcula o valor acumulado do IPCA desde a data base, até uma data final
    
    Parâmetros: Data base
                Data final
    Retorno: Taxa total acumulada
    """
    # COTACAO = 1000 / (1 + TAXA)**(DIAS_UTEIS/252)
    # Se data base for dia 16 em diante, pegar mes/ano
    if data_base.day >= 16:
        ipca_inicial = HistoricoIPCA.objects.filter(data_inicio__lte=data_base).order_by('-data_inicio')[0]
        if data_base.day > 16:
            # Cálculo de dias úteis proporcional
            pass
        else:
            ipca_periodo = ipca_inicial.valor
    
    # Se data base for dia 15 ou anterior, pegar mes anterior como base
    else:
        ano = data_base.year
        mes = data_base.month - 1
        if mes == 0:
            mes = 12
            ano = ano - 1
        ipca_inicial = HistoricoIPCA.objects.get(mes=mes, ano=ano)
        ipca_periodo = ipca_inicial.valor
    
    # Preparar último registro de IPCA
    ipca_final = HistoricoIPCA.objects.filter(data_inicio__lte=data_final).order_by('-data_inicio')[0]
    # Adicionar ao cálculo todos os meses cujo dia 15 do mês posterior for menor ou igual a data final
    for mes_historico in HistoricoIPCA.objects.filter(Q(data_inicio__gt=ipca_inicial.data_inicio, data_inicio__year=data_base.year) | \
                                                      Q(data_inicio__year__gt=data_base.year, data_inicio__lt=ipca_final.data_inicio)) \
                                                      .order_by('data_inicio'):
        # IPCA não-projetado
        if not hasattr(mes_historico, 'ipcaprojetado'):
            ipca_periodo = (1 + ipca_periodo) * (1 + mes_historico.valor) - 1
#             print (1 + ipca_periodo) * 1000
        # IPCA projetado
        else:
            qtd_dias_uteis_passados = qtd_dias_uteis_no_periodo(mes_historico.data_inicio, mes_historico.data_fim + datetime.timedelta(days=1))
            ultimo_dia_util = calendar.monthrange(mes_historico.data_inicio.year, mes_historico.data_inicio.month)[1]
            ultima_data_periodo_ipca = (ipca_final.data_inicio.replace(day=ultimo_dia_util) + datetime.timedelta(days=1)) \
                .replace(day=15)
            qtd_dias_uteis_total = qtd_dias_uteis_no_periodo(mes_historico.data_inicio.replace(day=16), ultima_data_periodo_ipca + datetime.timedelta(days=1))
            ipca_periodo = (1 + ipca_periodo) * ((1 + mes_historico.valor)**(Decimal(qtd_dias_uteis_passados)/qtd_dias_uteis_total)) - 1
    # Caso a última data seja diferente de 15, pegar último mês e calcular a proporção de dias úteis
    if data_final.day == 15:
        if not hasattr(ipca_final, 'ipcaprojetado'):
            ipca_periodo = (1 + ipca_periodo) * (1 + ipca_final.valor) - 1
        else:
            qtd_dias_uteis_passados = qtd_dias_uteis_no_periodo(ipca_final.data_inicio, ipca_final.data_fim + datetime.timedelta(days=1))
            ultimo_dia_util = calendar.monthrange(ipca_final.data_inicio.year, ipca_final.data_inicio.month)[1]
            ultima_data_periodo_ipca = (ipca_final.data_inicio.replace(day=ultimo_dia_util) + datetime.timedelta(days=1)) \
                .replace(day=15)
            qtd_dias_uteis_total = qtd_dias_uteis_no_periodo(ipca_final.data_inicio.replace(day=16), ultima_data_periodo_ipca + datetime.timedelta(days=1))
            ipca_periodo = (1 + ipca_periodo) * ((1 + ipca_final.valor)**(Decimal(qtd_dias_uteis_passados)/qtd_dias_uteis_total)) - 1
    else:
        qtd_dias_uteis_passados = qtd_dias_uteis_no_periodo(ipca_final.data_inicio, data_final + datetime.timedelta(days=1))
        ultimo_dia_util = calendar.monthrange(ipca_final.data_inicio.year, ipca_final.data_inicio.month)[1]
        ultima_data_periodo_ipca = (ipca_final.data_inicio.replace(day=ultimo_dia_util) + datetime.timedelta(days=1)) \
            .replace(day=15)
        qtd_dias_uteis_total = qtd_dias_uteis_no_periodo(ipca_final.data_inicio.replace(day=16), ultima_data_periodo_ipca + datetime.timedelta(days=1))
        ipca_periodo = (1 + ipca_periodo) * ((1 + ipca_final.valor)**(Decimal(qtd_dias_uteis_passados)/qtd_dias_uteis_total)) - 1
    
#     print (1 + ipca_periodo) * 1000
    return ipca_periodo
    
def calcular_valor_acumulado_selic(data_base, data_final=datetime.date.today()):
    """
    Calcula o valor acumulado da Selic desde a data base, até uma data final
    
    Parâmetros: Data base
                Data final
    Retorno: Taxa total acumulada
    """
    selic_periodo = 1
    taxas_selic = dict(HistoricoTaxaSelic.objects.filter(data__range=[data_base, data_final - datetime.timedelta(days=1)]).values('taxa_diaria').distinct().order_by('taxa_diaria').annotate(qtd_dias=Count('taxa_diaria')).values_list('taxa_diaria', 'qtd_dias'))
    for (taxa, qtd_dias) in taxas_selic.items():
        selic_periodo *= (taxa**qtd_dias)
    return selic_periodo - 1

def buscar_valores_diarios_di():
    """Busca valores históricos do DI no site da CETIP"""
    ftp = FTP('ftp.cetip.com.br')
    ftp.login()
    ftp.cwd('MediaCDI')
    linhas = []
    ftp.retrlines('NLST', linhas.append)
    linhas.sort()
    for nome in linhas:
        # Verifica se são os .txt do CDI
        if '.txt' in nome:
            # Testa se data do arquivo é maior do que a última data registrada
            data = datetime.date(int(nome[0:4]), int(nome[4:6]), int(nome[6:8]))
            if not HistoricoTaxaDI.objects.filter(data=data).exists():
                taxa = []
                ftp.retrlines('RETR ' + nome, taxa.append)
#                 print '%s: %s' % (data, Decimal(taxa[0]) / 100)
                historico = HistoricoTaxaDI(data = data, taxa = Decimal(taxa[0]) / 100)
                historico.save()
                
def buscar_valores_mensal_ipca():
    """Busca valores históricos do IPCA no site do IBGE"""
    meses = {'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6, 'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12}
    req = Request('ftp://ftp.ibge.gov.br/Precos_Indices_de_Precos_ao_Consumidor/IPCA/Serie_Historica/ipca_SerieHist.zip')
    response = urlopen(req)
#     doc_zip = response.read()
    zipdata = StringIO()
    zipdata.write(response.read())
    
    if zipfile.is_zipfile(zipdata):
        # Abrir e ler
        unzipped = zipfile.ZipFile(zipdata)
        for libitem in unzipped.namelist():
            doc_xls = unzipped.read(libitem)
    
            book = pyexcel.get_book(file_type="xls", file_content=doc_xls, name_columns_by_row=0)
            sheets = book.to_dict()
            
            # Guardar ano atual
            ano_atual = 0
            valor_mes_anterior = 0
            valor_mes_atual = 0
            for linha in sheets[u'Série Histórica IPCA']:
                if isinstance(linha[0], float):
                    ano_atual = int(linha[0])
                # Se mês não está definido, pular linha
                if linha[1] in meses:
                    mes = meses[linha[1]]
                else:
                    continue
                valor_mes_atual = Decimal(linha[2])
                if valor_mes_anterior > 0 and not HistoricoIPCA.objects.filter(data_inicio=datetime.date(ano_atual, mes, 16), ipcaprojetado__isnull=True).exists():
                    indice_mes_atual = (valor_mes_atual / valor_mes_anterior) - 1
                    data_inicio = datetime.date(ano_atual, mes, 16)
                    
                    gerar_ipca_oficial(indice_mes_atual, data_inicio)
#                     print HistoricoIPCA.objects.all().count(), novo.valor, novo.data_inicio
                valor_mes_anterior = valor_mes_atual

def gerar_ipca_oficial(valor, data_inicio):
    """
    Gera valor de IPCA oficial
    
    Parâmetros: Valor do IPCA no mês
                Data de início
    """
    ultimo_dia_util = calendar.monthrange(data_inicio.year, data_inicio.month)[1]
    data_fim = (data_inicio.replace(day=ultimo_dia_util) + datetime.timedelta(days=1)).replace(day=15)
    novo = HistoricoIPCA(valor=valor, data_inicio=data_inicio, data_fim=data_fim)
    
    # Apagar valores projetados anteriores
    if HistoricoIPCA.objects.filter(ipcaprojetado__isnull=False, data_inicio__lte=data_inicio).exists():
        HistoricoIPCA.objects.filter(ipcaprojetado__isnull=False, data_inicio__lte=data_inicio).delete()
    
    # Salvar novo valor
    novo.save()
    
def buscar_ipca_projetado():
    """Busca valores de IPCA projetado no site da Anbima"""
    req = Request('http://www.anbima.com.br/pt_br/informar/estatisticas/precos-e-indices/projecao-de-inflacao-gp-m.htm')
    response = urlopen(req)
    data = response.read()
    
    # Delimitar parte a ser tratada
    inicio = data.find('IPCA-15')
    fim = data.find('Fonte', inicio)
    string_importante = data[inicio:fim]
    
    # Buscar informações de projeções na página
    projecoes = string_importante.split('<div class="both">')[1:]
    valores = []
    datas_inicio = []
    for projecao in projecoes:
        projecao = projecao[projecao.find('strong'):]
        valor = re.sub(r'.*?>', '', projecao[:projecao.find('</strong>')])
        valores.append(valor)
        data_inicio = datetime.datetime.strptime(re.findall(r'\d+/\d+/\d+', projecao)[0], '%d/%m/%Y')
        datas_inicio.append(data_inicio)
    for indice in range(len(valores)):
        valor = valores[indice]
        # Valores indefinidos são mostrados como '-'
        if valor != '-':
            valor = Decimal(valor.replace(',', '.'))/100
            data_inicio = datas_inicio[indice]
            # Verifica se chegou ao último registro
            if indice == len(valores) - 1:
                # Se sim, adicionar data padrão de fim (dia 15 do próximo mês)
                ultimo_dia_util = calendar.monthrange(data_inicio.year, data_inicio.month)[1]
                data_fim = (data_inicio.replace(day=ultimo_dia_util) + datetime.timedelta(days=1)).replace(day=15)
            else:
                # Se não, um dia antes da próxima data de início
                data_fim = datas_inicio[indice+1] - datetime.timedelta(days=1)
            if not HistoricoIPCA.objects.filter(data_inicio=data_inicio).exists():
                try:
                    with transaction.atomic():
                        ipca_projetado = HistoricoIPCA(valor=valor, data_inicio=data_inicio, data_fim=data_fim)
                        ipca_projetado.save()
                        marcar_projetado = IPCAProjetado(ipca=ipca_projetado)
                        marcar_projetado.save()
                except:
                    raise
            else:
                print HistoricoIPCA.objects.filter(data_inicio=data_inicio, ipcaprojetado__isnull=False).exists()
                
def gerar_ipca_projetado():
    """Gera valor de IPCA projetado"""
    pass