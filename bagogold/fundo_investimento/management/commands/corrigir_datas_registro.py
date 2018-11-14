# -*- coding: utf-8 -*-
import csv
import datetime
import traceback

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction

from bagogold import settings
from bagogold.fundo_investimento.management.commands.buscar_fundos_investimento import buscar_arquivo_csv_cadastro
from bagogold.fundo_investimento.management.commands.preencher_historico_fundo_investimento import formatar_cnpj
from bagogold.fundo_investimento.models import FundoInvestimento


class Command(BaseCommand):
    help = 'TEMPORÁRIO Busca dados de fundos da CVM para corrigir datas de registro dos fundos existentes'

    def add_arguments(self, parser):
        parser.add_argument('-d', '--data', type=str, help='Informa uma data no formato YYYYMMDD')
        parser.add_argument('-t', '--teste', action='store_true')

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Buscar arquivo CSV
                if options['data']:
                    data_pesquisa = datetime.datetime.strptime(options['data'], '%Y%m%d')
                else:
                    raise ValueError('Informe uma data')
                _, _, arquivo_csv = buscar_arquivo_csv_cadastro(data_pesquisa)
                    
                # Processar arquivo
                processar_datas_registro_arquivo_csv(arquivo_csv)
                
                # Travar transaction.atomic em caso de teste
                if options['teste']:
                    raise ValueError('ERRO DE TESTE')
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar fundos investimento', traceback.format_exc().decode('utf-8'))
        
        if 2 == 2: 
            return

def processar_datas_registro_arquivo_csv(dados_arquivo):
    """
    Ler o arquivo CSV com dados do cadastro de fundos de investimento para processar datas de registro
    
    Parâmetros: Dados do arquivo CSV
    """
#     with open("data1.txt") as f:
    try:
        with transaction.atomic():
            csv_reader = csv.reader(dados_arquivo, delimiter=';')
            
            inicio_geral = datetime.datetime.now()
            rows = list()
            for linha, row in enumerate(csv_reader):
                if linha == 0:
                    # Preparar dicionário com os campos disponíveis
                    # Campos disponíveis:
                    # 'CNPJ_FUNDO', 'DENOM_SOCIAL', 'DT_REG', 'DT_CONST', 'DT_CANCEL', 'SIT', 'DT_INI_SIT', 'DT_INI_ATIV', 
                    #'DT_INI_EXERC', 'DT_FIM_EXERC', 'CLASSE', 'DT_INI_CLASSE', 'RENTAB_FUNDO', 'CONDOM', 'FUNDO_COTAS', 
                    #'FUNDO_EXCLUSIVO', 'TRIB_LPRAZO', 'INVEST_QUALIF', 'TAXA_PERFM', 'VL_PATRIM_LIQ', 'DT_PATRIM_LIQ', 
                    #'DIRETOR', 'CNPJ_ADMIN', 'ADMIN', 'PF_PJ_GESTOR', 'CPF_CNPJ_GESTOR', 'GESTOR', 'CNPJ_AUDITOR', 'AUDITOR'
                    campos = {nome_campo: indice for (indice, nome_campo) in enumerate(row)}
                    print row
                else:
                    if linha % 1000 == 0:
                        print linha
                        
                    row = [campo.decode('latin-1').strip() for campo in row]
                    
                    # Se CNPJ não estiver preenchido, pular
                    if row[campos['CNPJ_FUNDO']] == '':
#                         print 'CNPJ NAO PREENCHIDO'
                        continue
                    
                    # Formatar CNPJ
                    if len(row[campos['CNPJ_FUNDO']]) < 18:
                        row[campos['CNPJ_FUNDO']] = formatar_cnpj(row[campos['CNPJ_FUNDO']])
                        
                    rows.append(row)
                    
                    if len(rows) == 250:
                        processar_datas_registro_linhas_documento_cadastro(rows, campos)
                        rows = list()    
            
            # Verificar se terminou de iterar no arquivo mas ainda possui linhas a processar
            if len(rows) > 0:
                processar_datas_registro_linhas_documento_cadastro(rows, campos)
                rows = list()  

            print datetime.datetime.now() - inicio_geral
                
            fundos_nao_alterados = FundoInvestimento.objects.filter(data_registro=datetime.date(2018, 11, 11))
            
            print len(fundos_nao_alterados)
            print fundos_nao_alterados
            
    except:
        print 'Linha', linha
        raise 

def processar_datas_registro_linhas_documento_cadastro(rows, campos):
    """
    Processa as datas de registro encontradas no documento de cadastro
    
    Parâmetros: Linhas do documento
                Dicionário de campos do documento
    """
    # Verificar fundos existentes
    lista_fundos_existentes = list(FundoInvestimento.objects.filter(
        cnpj__in=[row_atual[campos['CNPJ_FUNDO']] for row_atual in rows]))
    
    # Ordenar fundos existentes
    lista_fundos_existentes.sort(key=lambda fundo: fundo.cnpj)
     
    # Ordenar rows
    rows.sort(key=lambda row: row[campos['CNPJ_FUNDO']])
    
    alterados = 0
    for fundo_existente in lista_fundos_existentes:
        # Verificar se o primeiro registro é menor que o cnpj atual, removê-lo para diminuir iterações
        while len(rows) > 0 and fundo_existente.cnpj > rows[0][campos['CNPJ_FUNDO']]:
            rows.pop(0)
                
        for row_atual in rows:
            if row_atual[campos['CNPJ_FUNDO']] == fundo_existente.cnpj:
                # Verificar se houve alteração no fundo
                fundo = fundo_existente
                # Verificar alterações
                alterado = False
                if row_atual[campos['DT_REG']] != '' and row_atual[campos['DT_REG']] < fundo.data_registro.strftime('%Y-%m-%d'):
                    if fundo.data_registro != datetime.date(2018, 11, 11):
#                         print 'data registro era', fundo.data_registro
                        pass
                    fundo.data_registro = datetime.datetime.strptime(row_atual[campos['DT_REG']], '%Y-%m-%d')
                    alterado = True
                else:
#                     print 'nao alterado', row_atual[campos['DT_REG']], fundo.data_registro
                    pass
                if alterado:
                    fundo.save()
                    alterados += 1
                    
            elif row_atual[campos['CNPJ_FUNDO']] > fundo_existente.cnpj:
                break
    
    print alterados == len(lista_fundos_existentes), alterados, len(lista_fundos_existentes)
