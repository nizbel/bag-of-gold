# -*- coding: utf-8 -*-
import csv
import datetime
import traceback
from urllib2 import urlopen, Request, HTTPError

import boto3
from botocore.exceptions import ClientError
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction

from bagogold import settings
from bagogold.bagogold.utils.misc import ultimo_dia_util
from bagogold.fundo_investimento.management.commands.preencher_historico_fundo_investimento import formatar_cnpj
from bagogold.fundo_investimento.models import FundoInvestimento, Administrador, \
    DocumentoCadastro, LinkDocumentoCadastro, Auditor, Gestor, \
    GestorFundoInvestimento
from bagogold.fundo_investimento.utils import \
    criar_slug_fundo_investimento_valido
from bagogold.settings import CAMINHO_FUNDO_INVESTIMENTO_CADASTRO
from conf.settings_local import AWS_STORAGE_BUCKET_NAME


class Command(BaseCommand):
    help = 'Buscar fundos de investimento na CVM'

    def add_arguments(self, parser):
        parser.add_argument('-d', '--data', type=str, help='Data no formato DDMMAAAA')

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Buscar arquivo CSV
                if options['data']:
                    data_pesquisa = datetime.datetime.strptime(options['data'], '%d%m%Y').date()
                    if data_pesquisa < datetime.date(2017, 7, 3):
                        raise ValueError('Data deve ser a partir de 03/07/2017')
                else:
                    # Busca data do último dia útil
                    data_pesquisa = ultimo_dia_util()
                    
                # Verifica se o documento existe
                if DocumentoCadastro.objects.filter(data_referencia=data_pesquisa).exists():
                    documento = DocumentoCadastro.objects.get(data_referencia=data_pesquisa)
                    
                    # Verificar se já foi lido
                    if documento.leitura_realizada:
                        return
                    else:
                        # Verificar se arquivo existe na AWS
                        nome_arquivo = documento.linkdocumentocadastro.url.split('/')[-1]
                        caminho_arquivo = CAMINHO_FUNDO_INVESTIMENTO_CADASTRO + nome_arquivo
                        if not verificar_arquivo_s3(caminho_arquivo):
                            # Salvar arquivo no bucket
                            _, nome_arquivo, arquivo_csv = buscar_arquivo_csv_cadastro(data_pesquisa)
                            
                            # Salvar arquivo em media no bucket
                            caminho_arquivo = CAMINHO_FUNDO_INVESTIMENTO_CADASTRO + nome_arquivo
                            boto3.client('s3').put_object(Body=arquivo_csv.read(), Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
                    
                        # Preparar arquivo para processamento
                        arquivo_csv = boto3.client('s3').get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)['Body'].read().splitlines(True)
                    
                else:
                    # Caso o documento ainda não exista, baixar
                    link_arquivo_csv, nome_arquivo, arquivo_csv = buscar_arquivo_csv_cadastro(data_pesquisa)
                        
                    # Gerar documento
                    documento = DocumentoCadastro.objects.create(data_referencia=data_pesquisa, data_pedido_cvm=datetime.date.today())
                    LinkDocumentoCadastro.objects.create(url=link_arquivo_csv, documento=documento)
                      
                    # Salvar arquivo em media no bucket
                    caminho_arquivo = CAMINHO_FUNDO_INVESTIMENTO_CADASTRO + nome_arquivo
                    boto3.client('s3').put_object(Body=arquivo_csv.fp.read(), Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
                    
                    # Preparar arquivo para processamento
                    arquivo_csv = boto3.client('s3').get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)['Body'].read().splitlines(True)
                    
            with transaction.atomic():
                # Processar arquivo
                processar_arquivo_csv(documento, arquivo_csv)
                    
            # Sem erros, apagar arquivo
            boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar fundos investimento', traceback.format_exc().decode('utf-8'))
        


def buscar_arquivo_csv_cadastro(data):
    """
    Busca o arquivo CSV de cadastro de fundos de investimento com base em uma data
    
    Parâmetros: Data
    Retorno: (Link para arquivo, Arquivo CSV)
    """
    # FORMATO: http://dados.cvm.gov.br/dados/FI/CAD/DADOS/inf_cadastral_fi_YYYYMMDD.csv
    url_csv = 'http://dados.cvm.gov.br/dados/FI/CAD/DADOS/inf_cadastral_fi_%s.csv' % (data.strftime('%Y%m%d'))
    req = Request(url_csv)
    try:
        response = urlopen(req, timeout=45)
    except HTTPError as e:
        raise ValueError('%s na url %s' % (e.code, url_csv))
    
    dados = response
    nome_csv = url_csv.split('/')[-1]
    
    return (url_csv, nome_csv, dados)

def processar_arquivo_csv(documento, dados_arquivo, codificacao='latin-1'):
    """
    Ler o arquivo CSV com dados do cadastro de fundos de investimento
    
    Parâmetros: Documento cadastral
                Dados do arquivo CSV
                Data do documento
    """
    try:
        with transaction.atomic():
            csv_reader = csv.reader(dados_arquivo, delimiter=';')
            
#             fundos = list()
            
#             inicio_geral = datetime.datetime.now()
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
#                     print row
                else:
#                     if linha % 1000 == 0:
#                         print linha
                                        
                    row = [campo.strip().decode(codificacao) for campo in row]
                    
                    # Se CNPJ não estiver preenchido, pular
                    if row[campos['CNPJ_FUNDO']] == '':
#                         print 'CNPJ NAO PREENCHIDO'
                        continue
                    
#                     fundos.append({'CNPJ_FUNDO': row[campos['CNPJ_FUNDO']], 'DENOM_SOCIAL': row[campos['DENOM_SOCIAL']], 'DT_REG': row[campos['DT_REG']], 
#                                    'DT_CANCEL': row[campos['DT_CANCEL']], 'CNPJ_ADMIN': row[campos['CNPJ_ADMIN']], 
#                                    'CPF_CNPJ_GESTOR': row[campos['CPF_CNPJ_GESTOR']], 'CNPJ_AUDITOR': row[campos['CNPJ_AUDITOR']]})
                    
                    # Formatar CNPJ
                    if len(row[campos['CNPJ_FUNDO']]) < 18:
                        row[campos['CNPJ_FUNDO']] = formatar_cnpj(row[campos['CNPJ_FUNDO']])
                        
                    # Formatar CNPJ de administrador
                    if row[campos['CNPJ_ADMIN']] != '' and len(row[campos['CNPJ_ADMIN']]) < 18:
                        row[campos['CNPJ_ADMIN']] = formatar_cnpj(row[campos['CNPJ_ADMIN']])
                        
                    # Formatar CNPJ de auditor
                    if row[campos['CNPJ_AUDITOR']] != '' and len(row[campos['CNPJ_AUDITOR']]) < 18:
                        row[campos['CNPJ_AUDITOR']] = formatar_cnpj(row[campos['CNPJ_AUDITOR']])
                            
                    rows.append(row)
                    
                    if len(rows) == 250:
                        processar_linhas_documento_cadastro(rows, campos)
                        rows = list()    
            
            # Verificar se terminou de iterar no arquivo mas ainda possui linhas a processar
            if len(rows) > 0:
                processar_linhas_documento_cadastro(rows, campos)
                rows = list()  
            
#             print datetime.datetime.now() - inicio_geral
            
#             # Verificar se fundos possuem multiplos administradores/gestores/auditores
#             fundos_repetidos = {}
#             
#             # Organizar por cnpj
#             fundos.sort(key=lambda k: k['CNPJ_FUNDO'])
#             
#             for indice, fundo in enumerate(fundos):
#                 for prox_fundo in fundos[indice+1:]:
#                     if fundo['CNPJ_FUNDO'] == prox_fundo['CNPJ_FUNDO']:
#                         print indice, '->', fundo['CNPJ_FUNDO'], 'existem mais registros'
#                         
#                         # Preparar lista de repetidos
#                         if fundo['CNPJ_FUNDO'] not in fundos_repetidos.keys():
#                             fundos_repetidos[fundo['CNPJ_FUNDO']] = list()
#                         
#                         # Adicionar a lista de repetidos
#                         if fundo not in fundos_repetidos[fundo['CNPJ_FUNDO']]:
#                             fundos_repetidos[fundo['CNPJ_FUNDO']].append(fundo)
#                         if prox_fundo not in fundos_repetidos[fundo['CNPJ_FUNDO']]:
#                             fundos_repetidos[fundo['CNPJ_FUNDO']].append(prox_fundo)
#                     elif fundo['CNPJ_FUNDO'] < prox_fundo['CNPJ_FUNDO']:
#                         break
#                   
#             for cnpj in fundos_repetidos.keys():          
#                 print cnpj, len(fundos_repetidos[cnpj]) #, fundos_repetidos[cnpj]
#                 admins = list()
#                 gestores = list()
#                 auditores = list()
#                 for fundo in fundos_repetidos[cnpj]:
#                     if fundo['CNPJ_ADMIN'] not in admins:
#                         admins.append(fundo['CNPJ_ADMIN'])
#                     if fundo['CPF_CNPJ_GESTOR'] not in gestores:
#                         gestores.append(fundo['CPF_CNPJ_GESTOR'])
#                     if fundo['CNPJ_AUDITOR'] not in auditores:
#                         auditores.append(fundo['CNPJ_AUDITOR'])
# #                 if len(admins) > 1:
# #                     print 'admins', admins
# #                 if len(gestores) > 1:
# #                     print 'gestores', gestores
#                 if len(auditores) > 1:
#                     print 'auditores', auditores
                
            
#             # Verificar fundos que existem porém não foram listados, ou seja, estão terminados
#             # Verificar fundos não encontrados no cadastro para terminar
#             qtd_terminados = 0
#             for fundo in FundoInvestimento.objects.filter(ultimo_registro__lt=data_documento):
#                 if fundo.cnpj not in fundos:
#                     fundo.situacao = FundoInvestimento.SITUACAO_TERMINADO
#                     fundo.save()
#                     qtd_terminados += 1
#                     if len(fundo.cnpj) == 18:
#                         print fundo.cnpj
#             print 'TERMINADOS', qtd_terminados
                         
#             documento = DocumentoCadastro.objects.get(data_referencia=data_documento)  
            documento.leitura_realizada = True
            documento.save() 
            
#             if 2 == 2:
#                 raise ValueError('TESTE')
    except:
        print 'Linha', linha
        raise 

def processar_linhas_documento_cadastro(rows, campos):
    """
    Processa linhas de um documento de cadastro de fundos de investimento em CSV
    
    Parâmetros: Linhas do documento
                Dicionário de campos
    """
    # Adicionar administradores
    # Guardar administradores únicos válidos
    lista_administradores = [{'ADMIN': row_atual[campos['ADMIN']], 'CNPJ_ADMIN': row_atual[campos['CNPJ_ADMIN']]} for row_atual in rows \
                             if row_atual[campos['CNPJ_ADMIN']] != '']
    lista_administradores = [administrador for indice, administrador in enumerate(lista_administradores) \
                             if administrador not in lista_administradores[indice + 1:]]
        
    lista_administradores_existentes = list(Administrador.objects.filter(
        cnpj__in=[administrador['CNPJ_ADMIN'] for administrador in lista_administradores]))
    
    # Verificar se administradores já existem
#     inicio = datetime.datetime.now()
    for administrador in [novo_admin for novo_admin in lista_administradores if novo_admin['CNPJ_ADMIN'] not in \
                          [administrador_existente.cnpj for administrador_existente in lista_administradores_existentes]]:
        novo_administrador = Administrador(nome=administrador['ADMIN'], cnpj=administrador['CNPJ_ADMIN'])
        novo_administrador.save()
        lista_administradores_existentes.append(novo_administrador)
#     print 'admin', datetime.datetime.now() - inicio

    # Adicionar auditores
    # Guardar auditores únicos válidos
    lista_auditores = [{'AUDITOR': row_atual[campos['AUDITOR']], 'CNPJ_AUDITOR': row_atual[campos['CNPJ_AUDITOR']]} for row_atual in rows \
                             if row_atual[campos['CNPJ_AUDITOR']] != '']
    lista_auditores = [auditor for indice, auditor in enumerate(lista_auditores) \
                             if auditor not in lista_auditores[indice + 1:]]
        
    lista_auditores_existentes = list(Auditor.objects.filter(
        cnpj__in=[auditor['CNPJ_AUDITOR'] for auditor in lista_auditores]))
    
    # Verificar se auditores já existem
#     inicio = datetime.datetime.now()
    for auditor in [novo_audit for novo_audit in lista_auditores if novo_audit['CNPJ_AUDITOR'] not in \
                          [auditor_existente.cnpj for auditor_existente in lista_auditores_existentes]]:
        novo_auditor = Auditor(nome=auditor['AUDITOR'], cnpj=auditor['CNPJ_AUDITOR'])
        novo_auditor.save()
        lista_auditores_existentes.append(novo_auditor)
#     print 'audit', datetime.datetime.now() - inicio

    # Adicionar gestores
    # Guardar gestores únicos válidos
    lista_gestores = [{'GESTOR': row_atual[campos['GESTOR']], 'CPF_CNPJ_GESTOR': row_atual[campos['CPF_CNPJ_GESTOR']]} for row_atual in rows \
                             if row_atual[campos['CPF_CNPJ_GESTOR']] != '']
    lista_gestores = [gestor for indice, gestor in enumerate(lista_gestores) \
                             if gestor not in lista_gestores[indice + 1:]]

    lista_gestores_existentes = list(Gestor.objects.filter(
        cnpj__in=[gestor['CPF_CNPJ_GESTOR'] for gestor in lista_gestores]))
    
    # Verificar se auditores já existem
#     inicio = datetime.datetime.now()
    for gestor in [novo_gest for novo_gest in lista_gestores if novo_gest['CPF_CNPJ_GESTOR'] not in \
                          [gestor_existente.cnpj for gestor_existente in lista_gestores_existentes]]:
        novo_gestor = Gestor(nome=gestor['GESTOR'], cnpj=gestor['CPF_CNPJ_GESTOR'])
        novo_gestor.save()
        lista_gestores_existentes.append(novo_gestor)
#     print 'audit', datetime.datetime.now() - inicio

    # Verificar fundos existentes
    lista_fundos_existentes = list(FundoInvestimento.objects.filter(
        cnpj__in=[row_atual[campos['CNPJ_FUNDO']] for row_atual in rows]).select_related('administrador', 'auditor').prefetch_related('gestorfundoinvestimento_set'))
    
    # Ordenar fundos existentes
    lista_fundos_existentes.sort(key=lambda fundo: fundo.cnpj)
    
    # Ordenar rows
    rows.sort(key=lambda row: row[campos['CNPJ_FUNDO']])
    
#     inicio = datetime.datetime.now()
    for row_atual in rows:
        
        # Verificar se o primeiro registro é menor que o cnpj atual, removê-lo para diminuir iterações
        while len(lista_fundos_existentes) > 0 and row_atual[campos['CNPJ_FUNDO']] > lista_fundos_existentes[0].cnpj:
            lista_fundos_existentes.pop(0)
        
        encontrado = False
        for fundo_existente in lista_fundos_existentes:
            if row_atual[campos['CNPJ_FUNDO']] == fundo_existente.cnpj and row_atual[campos['DT_REG']] == fundo_existente.data_registro.strftime('%Y-%m-%d'):
#                 print 'Existente'
                # Verificar se houve alteração no fundo
                fundo = fundo_existente
                # Verificar alterações
                alterado = False
                if row_atual[campos['CNPJ_ADMIN']] != '' and (fundo.administrador == None or row_atual[campos['CNPJ_ADMIN']] != fundo.administrador.cnpj):
                    for administrador in lista_administradores_existentes:
                        if administrador.cnpj == row_atual[campos['CNPJ_ADMIN']]:
                            fundo.administrador = administrador
                            
                            alterado = True
                            break

                if row_atual[campos['CNPJ_AUDITOR']] != '' and (fundo.auditor == None or row_atual[campos['CNPJ_AUDITOR']] != fundo.auditor.cnpj):
                    for auditor in lista_auditores_existentes:
                        if auditor.cnpj == row_atual[campos['CNPJ_AUDITOR']]:
                            fundo.auditor = auditor
                            
                            alterado = True
                            break

                if row_atual[campos['SIT']] != '' and row_atual[campos['SIT']].upper() != fundo.descricao_situacao().upper():
                    fundo.situacao = FundoInvestimento.buscar_tipo_situacao(row_atual[campos['SIT']])
                    alterado = True
                    
                if row_atual[campos['CLASSE']] != '' and row_atual[campos['CLASSE']].upper() != fundo.descricao_classe().upper():
                    fundo.classe = FundoInvestimento.buscar_tipo_classe(row_atual[campos['CLASSE']])
                    alterado = True
                    
                if row_atual[campos['DENOM_SOCIAL']] != '' and row_atual[campos['DENOM_SOCIAL']] != fundo.nome:
                    fundo.nome = row_atual[campos['DENOM_SOCIAL']]
                    # Alterar slug
                    fundo.slug = criar_slug_fundo_investimento_valido(fundo.nome)
                    alterado = True
                    
                if row_atual[campos['DT_CANCEL']] != '' and fundo.data_cancelamento == None:
                    fundo.data_cancelamento = row_atual[campos['DT_CANCEL']]
                    # Se possui data de cancelamento, situação deve ser TERMINADO
                    fundo.situacao = FundoInvestimento.SITUACAO_TERMINADO
                    alterado = True
                
                if alterado:
                    fundo.save()
                    
                # Procurar gestores
                if row_atual[campos['CPF_CNPJ_GESTOR']] != '' \
                and row_atual[campos['CPF_CNPJ_GESTOR']] not in fundo.gestorfundoinvestimento_set.all().values_list('gestor__cnpj', flat=True):
                    for gestor in lista_gestores_existentes:
                        if gestor.cnpj == row_atual[campos['CPF_CNPJ_GESTOR']]:
                            gestor_fundo_investimento = GestorFundoInvestimento(fundo_investimento=fundo, gestor=gestor)
                            gestor_fundo_investimento.save()
                            break
                        
                encontrado = True
                break
            
            # Se encontrou um fundo existente com CNPJ maior, pela ordenação, parar de procurar
            elif row_atual[campos['CNPJ_FUNDO']] < fundo_existente.cnpj:
                break
        
        if not encontrado:
            novo_fundo = FundoInvestimento(cnpj=row_atual[campos['CNPJ_FUNDO']], nome=row_atual[campos['DENOM_SOCIAL']], 
                                       data_constituicao=row_atual[campos['DT_CONST']], situacao=FundoInvestimento.buscar_tipo_situacao(row_atual[campos['SIT']]), 
                                       tipo_prazo=definir_prazo_pelo_cadastro(row_atual[campos['TRIB_LPRAZO']]),
                                       classe=FundoInvestimento.buscar_tipo_classe(row_atual[campos['CLASSE']]), exclusivo_qualificados=(row_atual[campos['INVEST_QUALIF']].upper() == 'S'),
                                       data_registro=datetime.datetime.strptime(row_atual[campos['DT_REG']], '%Y-%m-%d'),
                                       slug=criar_slug_fundo_investimento_valido(row_atual[campos['DENOM_SOCIAL']]))
            if row_atual[campos['CNPJ_ADMIN']] != '':
                for administrador in lista_administradores_existentes:
                    if administrador.cnpj == row_atual[campos['CNPJ_ADMIN']]:
                        novo_fundo.administrador = administrador
                        break

            if row_atual[campos['CNPJ_AUDITOR']] != '':
                for auditor in lista_auditores_existentes:
                    if auditor.cnpj == row_atual[campos['CNPJ_AUDITOR']]:
                        novo_fundo.auditor = auditor
                        break
                    
            if row_atual[campos['DT_CANCEL']] != '':
                novo_fundo.data_cancelamento=row_atual[campos['DT_CANCEL']]
                # Se possui data de cancelamento, situação deve ser TERMINADO
                novo_fundo.situacao = FundoInvestimento.SITUACAO_TERMINADO
            
            novo_fundo.save()
            
            # Adicionar gestor
            for gestor in lista_gestores_existentes:
                if gestor.cnpj == row_atual[campos['CPF_CNPJ_GESTOR']]:
                    gestor_fundo_investimento = GestorFundoInvestimento(fundo_investimento=novo_fundo, gestor=gestor)
                    gestor_fundo_investimento.save()
                    break
            
            lista_fundos_existentes.insert(0, novo_fundo) 
#     print 'fundo', datetime.datetime.now() - inicio
  

def definir_prazo_pelo_cadastro(str_tributacao_documento):
    """Busca prazo do fundo de investimento"""
    return FundoInvestimento.PRAZO_CURTO if str_tributacao_documento.strip().upper() == 'N' else FundoInvestimento.PRAZO_LONGO

def verificar_arquivo_s3(caminho_arquivo):
    """
    Verifica se arquivo com o caminho especificado existe no bucket do S3
    
    Parâmetros: Caminho do arquivo
    Retorno: True ou False
    """
    try:
        _ = boto3.client('s3').head_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
        return True
    except ClientError as exc:
        if exc.response['Error']['Code'] != '404':
            raise
        else:
            return False