# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from ftplib import FTP

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI


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
    ipca_inicial = HistoricoIPCA.objects.get(mes=data_base.month, ano=data_base.year)
    # Calcular quantidade de dias em que a taxa inicial foi aplicada
    ultimo_dia_mes_inicial = datetime.date(data_base.year, data_base.month, calendar.monthrange(data_base.year, data_base.month)[1])
    qtd_dias = (min(data_final, ultimo_dia_mes_inicial) - data_base).days
    # Transformar taxa mensal em diaria
    ipca_inicial_diario = pow(1 + ipca_inicial.valor/Decimal(100), Decimal(1)/30) - 1
    # Iniciar IPCA do periodo com o acumulado nos dias
    ipca_periodo = pow(1 + ipca_inicial_diario, qtd_dias) - 1
#     print 'IPCA inicial:', ipca_periodo
    # TODO melhorar isso
    for mes_historico in HistoricoIPCA.objects.filter((Q(mes__gt=ipca_inicial.mes) & Q(ano=ipca_inicial.ano)) | \
                                                      Q(ano__gt=ipca_inicial.ano)).filter(ano__lte=data_final.year).order_by('ano', 'mes'):
        if datetime.date(mes_historico.ano, mes_historico.mes, calendar.monthrange(mes_historico.ano, mes_historico.mes)[1]) <= data_final:
#             print mes_historico.ano, '/', mes_historico.mes, '->', ipca_periodo, (1 + mes_historico.valor/Decimal(100))
            ipca_periodo = (1 + ipca_periodo) * (1 + mes_historico.valor/Decimal(100)) - 1
    return ipca_periodo
    
def calcular_valor_acumulado_selic(data_base, data_final=datetime.date.today()):
    """
    Calcula o valor acumulado da Selic desde a data base, até uma data final
    
    Parâmetros: Data base
                Data final
    Retorno: Taxa total acumulada
    """
    selic_periodo = 1
    taxas_selic = dict(HistoricoTaxaSelic.objects.filter(data__range=[data_base, data_final]).order_by('taxa_diaria').annotate(qtd_dias=Count('taxa_diaria')).values_list('taxa_diaria', 'qtd_dias'))
    selic_periodo *= [taxa for (taxa, qtd_dias) in taxas_selic.items()]
    return selic_periodo

# TODO trazer busca de valores diários do DI para essa função
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