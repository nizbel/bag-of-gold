# -*- coding: utf-8 -*-
import csv
import datetime
from decimal import Decimal
import traceback
from urllib2 import urlopen, Request, HTTPError

import boto3
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.query import Prefetch

from bagogold import settings
from bagogold.bagogold.utils.misc import ultimo_dia_util
from bagogold.fundo_investimento.management.commands.buscar_fundos_investimento import verificar_arquivo_s3
from bagogold.fundo_investimento.models import FundoInvestimento, \
    HistoricoValorCotas
from bagogold.fundo_investimento.utils import formatar_cnpj
from bagogold.settings import CAMINHO_FUNDO_INVESTIMENTO_HISTORICO
from conf.settings_local import AWS_STORAGE_BUCKET_NAME


class Command(BaseCommand):
    help = 'Preencher historico de fundos de investimento'

    def add_arguments(self, parser):
        parser.add_argument('--data', action='store_true')
        
        
        
    def handle(self, *args, **options):
        try:
#             with transaction.atomic():
#                 # Buscar arquivo CSV
#                 if options['data']:
#                     data_pesquisa = datetime.datetime.strptime(options['data'], '%d%m%Y').date()
#                 else:
#                     # Busca data do último dia útil
#                     data_pesquisa = ultimo_dia_util()
#                 
#                 caminho_arquivo = CAMINHO_FUNDO_INVESTIMENTO_HISTORICO + 'inf_diario_fi_%s.csv' % (data_pesquisa.strftime('%Y%m'))
#                 
#                 if not verificar_arquivo_s3(caminho_arquivo):
#                     # Caso o documento ainda não exista, baixar
#                     _, _, arquivo_csv = buscar_arquivo_csv_historico(data_pesquisa)
# 
#                     # Salvar arquivo em media no bucket
#                     boto3.client('s3').put_object(Body=arquivo_csv.fp.read(), Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
# 
#                 # Preparar arquivo para processamento
#                 arquivo_csv = boto3.client('s3').get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)['Body'].read().splitlines(True)
                    
            with transaction.atomic():
                # Processar arquivo
#                 processar_arquivo_csv(arquivo_csv)
                arquivo_csv = open('inf_diario_fi_201901.csv', 'r')
                processar_arquivo_csv(arquivo_csv)
                    
            # Sem erros, apagar arquivo
#             boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preencher histórico fundos investimento', traceback.format_exc().decode('utf-8'))
        


def buscar_arquivo_csv_historico(data):
    """
    Busca o arquivo CSV de cadastro de fundos de investimento com base em uma data
    
    Parâmetros: Data
    Retorno: (Link para arquivo, Arquivo CSV)
    """
    # FORMATO: http://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_YYYYMM.csv
    url_csv = 'http://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_%s.csv' % (data.strftime('%Y%m'))
    req = Request(url_csv)
    try:
        response = urlopen(req, timeout=45)
    except HTTPError as e:
        raise ValueError('%s na url %s' % (e.code, url_csv))
    
    dados = response
    nome_csv = url_csv.split('/')[-1]
    
    return (url_csv, nome_csv, dados)

def processar_arquivo_csv(dados_arquivo, codificacao='latin-1'):
    """
    Ler o arquivo CSV com dados do valor histórico de fundos de investimento
    
    Parâmetros: Dados do arquivo CSV
                Tipo de codificação
    """
    try:
        with transaction.atomic():
            csv_reader = csv.reader(dados_arquivo, delimiter=';')
            
            inicio_geral = datetime.datetime.now()
            rows = list()
            for linha, row in enumerate(csv_reader):
                if linha == 0:
                    # Preparar dicionário com os campos disponíveis
                    # Campos disponíveis:
                    # 'CNPJ_FUNDO', 'DT_COMPTC', 'VL_TOTAL', 'VL_QUOTA', 'VL_PATRIM_LIQ', 'CAPTC_DIA', 'RESG_DIA', 'NR_COTST'
                    campos = {nome_campo: indice for (indice, nome_campo) in enumerate(row)}
#                     print row
                else:
                    if linha % 1000 == 0:
                        print linha
                                        
                    row = [campo.strip().decode(codificacao) for campo in row]
                    
                    # Se CNPJ não estiver preenchido, pular
                    if row[campos['CNPJ_FUNDO']] == '':
#                         print 'CNPJ NAO PREENCHIDO'
                        continue
                    
                    # Formatar CNPJ
                    if len(row[campos['CNPJ_FUNDO']]) < 18:
                        row[campos['CNPJ_FUNDO']] = formatar_cnpj(row[campos['CNPJ_FUNDO']])
                        
                    rows.append(row)
                    
                    if len(rows) == 750:
                        processar_linhas_documento_historico(rows, campos)
                        rows = list()    
            
            # Verificar se terminou de iterar no arquivo mas ainda possui linhas a processar
            if len(rows) > 0:
                processar_linhas_documento_historico(rows, campos)
                rows = list()  
            
            print 'Geral:', datetime.datetime.now() - inicio_geral
            if 2 == 2:
                raise ValueError('TESTE')
    except:
        print 'Linha', linha
        raise 

def processar_linhas_documento_historico(rows, campos):
    """
    Processa linhas de um documento de valor histórico de fundos de investimento em CSV
    
    Parâmetros: Linhas do documento
                Dicionário de campos
    """
    inicio = datetime.datetime.now()
    # Descobrir mês/ano do arquivo de acordo com o primeiro registro
    ano, mes = rows[0][campos['DT_COMPTC']].split('-')[0:2]
#     ano, mes = int(ano), int(mes)
    
    # Verificar fundos existentes
    lista_fundos_existentes = list(FundoInvestimento.objects.filter(
        cnpj__in=list(set([row_atual[campos['CNPJ_FUNDO']] for row_atual in rows]))) \
            .prefetch_related(Prefetch('historicovalorcotas_set', queryset=HistoricoValorCotas.objects.filter(data__year=ano, data__month=mes))))
    
    # Ordenar fundos existentes
    lista_fundos_existentes.sort(key=lambda fundo: fundo.cnpj)
    
    # Ordenar rows
    rows.sort(key=lambda row: row[campos['CNPJ_FUNDO']])
    
    lista_historicos = list()
    organizar =( datetime.datetime.now() - inicio)
    
    inicio = datetime.datetime.now()
    for row_atual in rows:
        # Verificar se o primeiro registro é menor que o cnpj atual, removê-lo para diminuir iterações
        while len(lista_fundos_existentes) > 0 and row_atual[campos['CNPJ_FUNDO']] > lista_fundos_existentes[0].cnpj:
            lista_fundos_existentes.pop(0)
            
        for fundo_existente in lista_fundos_existentes:
            if row_atual[campos['CNPJ_FUNDO']] < fundo_existente.cnpj:
                break
            elif row_atual[campos['CNPJ_FUNDO']] == fundo_existente.cnpj:
#                 if not HistoricoValorCotas.objects.filter(data=row_atual[campos['DT_COMPTC']], fundo_investimento=fundo_existente).exists():
                if not datetime.datetime.strptime(row_atual[campos['DT_COMPTC']], '%Y-%m-%d').date() in [historico.data for historico in fundo_existente.historicovalorcotas_set.all()]:
                    valor_cota = Decimal(row_atual[campos['VL_QUOTA']])
                    historico_fundo = HistoricoValorCotas(data=row_atual[campos['DT_COMPTC']], fundo_investimento=fundo_existente, valor_cota=valor_cota)
                    lista_historicos.append(historico_fundo)
#                     historico_fundo.save()
                break
    
    HistoricoValorCotas.objects.bulk_create(lista_historicos)
    historico= ( datetime.datetime.now() - inicio)
    
    print organizar, historico, historico.total_seconds() / organizar.total_seconds()
