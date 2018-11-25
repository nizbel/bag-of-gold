# -*- coding: utf-8 -*-
from StringIO import StringIO
import csv
import datetime
import os
import random
import time
import traceback
from urllib2 import urlopen, Request, HTTPError, URLError
import zipfile

import boto3
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction
from lxml import etree
import zeep

from bagogold import settings
from bagogold.bagogold.utils.misc import ultimo_dia_util, \
    buscar_dia_util_aleatorio, verifica_se_dia_util
from bagogold.fundo_investimento.management.commands.preencher_historico_fundo_investimento import formatar_cnpj
from bagogold.fundo_investimento.models import FundoInvestimento, Administrador, \
    DocumentoCadastro, LinkDocumentoCadastro, Auditor, Gestor,\
    GestorFundoInvestimento
from bagogold.fundo_investimento.utils import \
    criar_slug_fundo_investimento_valido
from bagogold.settings import CAMINHO_FUNDO_INVESTIMENTO_CADASTRO
from conf.conf import FI_LOGIN, FI_PASSWORD
from conf.settings_local import AWS_STORAGE_BUCKET_NAME


class Command(BaseCommand):
    help = 'Buscar fundos de investimento na CVM'

    def add_arguments(self, parser):
#         parser.add_argument('--aleatorio', action='store_true')
        parser.add_argument('-d', '--data', type=str, help='Informa uma data no formato YYYYMMDD')

    def handle(self, *args, **options):
        try:
            data_pesquisa = datetime.date(2018, 10, 26)
            novo_documento = DocumentoCadastro.objects.get(data_referencia=data_pesquisa)
            
#             with transaction.atomic():
#                 # Buscar arquivo CSV
#                 if options['data']:
#                     data_pesquisa = datetime.datetime.strptime(options['data'], '%Y%m%d')
#                 else:
#                     # Busca data do último dia útil
#                     data_pesquisa = ultimo_dia_util()
#                 link_arquivo_csv, nome_arquivo, arquivo_csv = buscar_arquivo_csv_cadastro(data_pesquisa)
#                    
#                 # Gerar documento
#                 novo_documento = DocumentoCadastro.objects.create(data_referencia=data_pesquisa, data_pedido_cvm=datetime.date.today())
#                 LinkDocumentoCadastro.objects.create(url=link_arquivo_csv, documento=novo_documento)
#                  
#                 # Salvar arquivo em media no bucket
#                 caminho_arquivo = CAMINHO_FUNDO_INVESTIMENTO_CADASTRO + nome_arquivo
#                 boto3.client('s3').put_object(Body=arquivo_csv.read(), Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
            
            with transaction.atomic():
                # Processar arquivo
#                 processar_arquivo_csv(arquivo_csv)
                with open('../Downloads/inf_cadastral_fi_20181026.csv') as f:
                    processar_arquivo_csv(novo_documento, f)
                    
                if 2 == 2:
                    raise ValueError('TESTE')
            
            # Sem erros, apagar arquivo
#             boto3.client('s3').delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar fundos investimento', traceback.format_exc().decode('utf-8'))
        
        if 2 == 2: 
            return
            

#     def handle(self, *args, **options):        
        try:
            wsdl = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
            client = zeep.Client(wsdl=wsdl)
            resposta = client.service.Login(FI_LOGIN, FI_PASSWORD)
            headerSessao = resposta['header']
    #         print headerSessao
        
            dias_uteis = list()
            if not options['aleatorio']:
                # Buscar último dia útil
                dias_uteis.append(ultimo_dia_util())
            else:
                # Buscar dias úteis que não tenham sido inseridos previamente
                for _ in range(3):
                    dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                    while DocumentoCadastro.objects.filter(data_referencia=dia_util, leitura_realizada=True).exists():
                        dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                    dias_uteis.append(dia_util)
                
                
            # Busca de competencias
            for dia_util in dias_uteis:
                # Testa se já não foi criado o link para o documento (apenas para não aleatório pois o aleatório evita datas já cadastradas)
                if not DocumentoCadastro.objects.filter(data_referencia=dia_util).exists():
                    try:
                        with transaction.atomic():
                            respostaCompetencias = client.service.solicAutorizDownloadCadastro(dia_util, 'Teste', _soapheaders=[headerSessao])
                            # Criar documento
                            novo_documento = DocumentoCadastro.objects.create(data_referencia=dia_util, data_pedido_cvm=datetime.date.today())
                            url = respostaCompetencias['body']['solicAutorizDownloadCadastroResult']
                            # Criar link
                            LinkDocumentoCadastro.objects.create(url=url, documento=novo_documento)
                    except zeep.exceptions.Fault as erro_wsdl:
                        # Verifica se não encontrou arquivo para os parâmetros
                        if u'Arquivo para download não encontrado para os parâmetros especificados' in erro_wsdl:
                            # Nesse caso, verificar se é a busca aleatoria para adicionar mais uma data para dias_uteis 
                            if options['aleatorio']:
                                dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                                while DocumentoCadastro.objects.filter(data_referencia=dia_util).exists():
                                    dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                                dias_uteis.append(dia_util)
                            # Se busca do último dia útil, procurar ultimo dia util antes do dia apontado que não tenha documentos lidos
                            else:
                                while DocumentoCadastro.objects.filter(data_referencia=dia_util, leitura_realizada=True).exists() or not verifica_se_dia_util(dia_util):
                                    dia_util -= datetime.timedelta(days=1)
                                dias_uteis.append(dia_util)
                        else:
                            if settings.ENV == 'DEV':
                                print traceback.format_exc()
                            elif settings.ENV == 'PROD':
                                mail_admins(u'Erro em Buscar fundos investimento', u'%s aconteceu para dia %s' % (erro_wsdl, dia_util.strftime('%d/%m/%Y')))
                        continue
                else:
                    documento_cadastro = DocumentoCadastro.objects.get(data_referencia=dia_util)
                    if not documento_cadastro.leitura_realizada:
                        # Se não for do mesmo dia, gerar novo
                        if (datetime.date.today() - documento_cadastro.data_pedido_cvm).days > 0:
                            try:
                                respostaCompetencias = client.service.solicAutorizDownloadCadastro(dia_util, 'Teste', _soapheaders=[headerSessao])
                                url = respostaCompetencias['body']['solicAutorizDownloadCadastroResult']
                                # Atualizar link
                                link = LinkDocumentoCadastro.objects.get(documento=novo_documento)
                                link.url = url
                                link.save()
                            except zeep.exceptions.Fault as erro_wsdl:
                                # Verifica se não encontrou arquivo para os parâmetros
                                if u'Arquivo para download não encontrado para os parâmetros especificados' in erro_wsdl:
                                    # Nesse caso, verificar se é a busca aleatoria para adicionar mais uma data para dias_uteis 
                                    if options['aleatorio']:
                                        dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                                        while DocumentoCadastro.objects.filter(data_referencia=dia_util).exists():
                                            dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                                        dias_uteis.append(dia_util)
                                else:
                                    if settings.ENV == 'DEV':
                                        print traceback.format_exc()
                                    elif settings.ENV == 'PROD':
                                        mail_admins(u'Erro em Buscar fundos investimento', u'%s aconteceu para dia %s' % (erro_wsdl, dia_util.strftime('%d/%m/%Y')))
                                continue
                        else:
                            # Mesmo dia, pegar link cadastrado
                            url = LinkDocumentoCadastro.objects.get(documento__data_referencia=dia_util).url
                    else:
                        url = LinkDocumentoCadastro.objects.get(documento__data_referencia=dia_util).url
#                 url = 'http://cvmweb.cvm.gov.br/swb/sistemas/scw/DownloadArqs/LeDownloadArqs.aspx?VL_GUID=8fc00daf-4fc8-4d83-bc4c-3e45cc79576c&PK_SESSAO=963322175&PK_ARQ_INFORM_DLOAD=196451'
                # Tenta extrair arquivo, se não conseguir, continua com o próximo
                try:
                    download = urlopen(url)
                    arquivo_zipado = StringIO(download.read())
                    unzipped = zipfile.ZipFile(arquivo_zipado)
                except:
                    if settings.ENV == 'DEV':
                        print traceback.format_exc()
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro em Buscar fundos investimento na data %s' % (dia_util.strftime('%d/%m/%Y')), traceback.format_exc().decode('utf-8'))
                    continue
                for libitem in unzipped.namelist():
                    try:
                        nome_arquivo = settings.CAMINHO_FUNDO_INVESTIMENTO_CADASTRO + libitem
                        # Ler arquivo
                        file(nome_arquivo,'wb').write(unzipped.read(libitem))
                        arquivo_cadastro = file(nome_arquivo, 'r')
                        tree = etree.parse(arquivo_cadastro)
                        if not options['aleatorio']:
                            fundos = list()
                        # Definir campos para traceback
                        campos = None
                        with transaction.atomic():
                            # Lê o arquivo procurando nós CADASTRO (1 para cada fundo)
                            for element in tree.getroot().iter('CADASTRO'):
                                campos = {key: value for (key, value) in [(elemento.tag, elemento.text) for elemento in element.iter()]}
                                # Verificar se administrador já existe
                                if not Administrador.objects.filter(cnpj=campos['CNPJ_ADMINISTRADOR']).exists():
                                    novo_administrador = Administrador(nome=campos['NOME_ADMINISTRADOR'].strip(), cnpj=campos['CNPJ_ADMINISTRADOR'].strip())
                                    novo_administrador.save()
                                 
                                # Verificar se fundo já existe
                                if not FundoInvestimento.objects.filter(cnpj=campos['CNPJ']).exists():
                                    novo_fundo = FundoInvestimento(cnpj=campos['CNPJ'].strip(), nome=campos['NOME'].strip(), administrador=Administrador.objects.get(cnpj=campos['CNPJ_ADMINISTRADOR']),
                                                                   data_constituicao=campos['DT_CONSTITUICAO'].strip(), situacao=FundoInvestimento.buscar_tipo_situacao(campos['SITUACAO']), 
                                                                   tipo_prazo=definir_prazo__pelo_cadastro(campos['TRATAMENTO_TRIBUTARIO']),
                                                                   classe=FundoInvestimento.buscar_tipo_classe(campos['CLASSE']), exclusivo_qualificados=(campos['INVESTIDORES_QUALIFICADOS'].strip().upper() == 'SIM'),
                                                                   ultimo_registro=dia_util, slug=criar_slug_fundo_investimento_valido(campos['NOME'].strip()))
                                    novo_fundo.save()
                                else:
                                    # Verificar se houve alteração no fundo
                                    fundo = FundoInvestimento.objects.get(cnpj=campos['CNPJ'])
                                    if fundo.ultimo_registro < dia_util:
                                        fundo.ultimo_registro = dia_util
                                        # Verificar alteração de administrador
                                        if campos['CNPJ_ADMINISTRADOR'] != fundo.administrador.cnpj:
                                            fundo.administrador = Administrador.objects.get(cnpj=campos['CNPJ_ADMINISTRADOR'])
                                        if campos['SITUACAO'] != None and campos['SITUACAO'] != fundo.descricao_situacao():
                                            fundo.situacao = FundoInvestimento.buscar_tipo_situacao(campos['SITUACAO'])
                                        if campos['CLASSE'] != None and campos['CLASSE'] != fundo.descricao_classe():
                                            fundo.classe = FundoInvestimento.buscar_tipo_classe(campos['CLASSE'])
                                        if campos['NOME'] != None and campos['NOME'].strip() != fundo.nome:
                                            fundo.nome = campos['NOME'].strip()
                                        fundo.save()
                                    
                                # Adicionar a lista de fundos para comparar posteriormente
                                if not options['aleatorio']:
                                    fundos.append(campos['CNPJ'])
                                
#                                 print novo_fundo             
                            documento = DocumentoCadastro.objects.get(data_referencia=dia_util)  
                            documento.leitura_realizada = True
                            documento.save()             
                        os.remove(nome_arquivo)                                
                    except:
                        # Apagar arquivo caso haja erro, enviar mensagem para email
                        try:
                            os.remove(nome_arquivo)
                        except OSError:
                            pass
                        if settings.ENV == 'DEV':
                            print traceback.format_exc()
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro em Buscar fundos investimento na data %s' % (dia_util.strftime('%d/%m/%Y')), traceback.format_exc().decode('utf-8'))
                # Verificar fundos que existem porém não foram listados, ou seja, estão terminados
                if not options['aleatorio']:
                    # Verificar fundos não encontrados no cadastro para terminar
                    for fundo in FundoInvestimento.objects.all().exclude(situacao=FundoInvestimento.SITUACAO_TERMINADO):
                        if fundo.cnpj not in fundos:
                            fundo.situacao = FundoInvestimento.SITUACAO_TERMINADO
                            fundo.save()
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

def processar_arquivo_csv(documento, dados_arquivo):
    """
    Ler o arquivo CSV com dados do cadastro de fundos de investimento
    
    Parâmetros: Documento cadastral
                Dados do arquivo CSV
                Data do documento
    """
#     try:
#     nome_arquivo = settings.CAMINHO_FUNDO_INVESTIMENTO_CADASTRO + libitem
#     # Ler arquivo
#     file(nome_arquivo,'wb').write(unzipped.read(libitem))
#     arquivo_cadastro = file(nome_arquivo, 'r')
#     tree = etree.parse(arquivo_cadastro)
#     if not options['aleatorio']:
#         fundos = list()
#     # Definir campos para traceback
#     campos = None

#     with open("data1.txt") as f:
    try:
        with transaction.atomic():
            csv_reader = csv.reader(dados_arquivo, delimiter=';')
            
#             fundos = list()
            
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
#                     print row
                else:
                    if linha % 1000 == 0:
                        print linha
                        
                    row = [campo.strip().decode('utf-8') for campo in row]
                    
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
            
            print datetime.datetime.now() - inicio_geral
            
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
#     with transaction.atomic():
#         # Lê o arquivo procurando nós CADASTRO (1 para cada fundo)
#         for element in tree.getroot().iter('CADASTRO'):
#             campos = {key: value for (key, value) in [(elemento.tag, elemento.text) for elemento in element.iter()]}
#             # Verificar se administrador já existe
#             if not Administrador.objects.filter(cnpj=campos['CNPJ_ADMINISTRADOR']).exists():
#                 novo_administrador = Administrador(nome=campos['NOME_ADMINISTRADOR'].strip(), cnpj=campos['CNPJ_ADMINISTRADOR'].strip())
#                 novo_administrador.save()
#              
#             # Verificar se fundo já existe
#             if not FundoInvestimento.objects.filter(cnpj=campos['CNPJ']).exists():
#                 novo_fundo = FundoInvestimento(cnpj=campos['CNPJ'].strip(), nome=campos['NOME'].strip(), administrador=Administrador.objects.get(cnpj=campos['CNPJ_ADMINISTRADOR']),
#                                                data_constituicao=campos['DT_CONSTITUICAO'].strip(), situacao=FundoInvestimento.buscar_tipo_situacao(campos['SITUACAO']), 
#                                                tipo_prazo=definir_prazo__pelo_cadastro(campos['TRATAMENTO_TRIBUTARIO']),
#                                                classe=FundoInvestimento.buscar_tipo_classe(campos['CLASSE']), exclusivo_qualificados=(campos['INVESTIDORES_QUALIFICADOS'].strip().upper() == 'SIM'),
#                                                ultimo_registro=dia_util, slug=criar_slug_fundo_investimento_valido(campos['NOME'].strip()))
#                 novo_fundo.save()
#             else:
#                 # Verificar se houve alteração no fundo
#                 fundo = FundoInvestimento.objects.get(cnpj=campos['CNPJ'])
#                 if fundo.ultimo_registro < dia_util:
#                     fundo.ultimo_registro = dia_util
#                     # Verificar alteração de administrador
#                     if campos['CNPJ_ADMINISTRADOR'] != fundo.administrador.cnpj:
#                         fundo.administrador = Administrador.objects.get(cnpj=campos['CNPJ_ADMINISTRADOR'])
#                     if campos['SITUACAO'] != None and campos['SITUACAO'] != fundo.descricao_situacao():
#                         fundo.situacao = FundoInvestimento.buscar_tipo_situacao(campos['SITUACAO'])
#                     if campos['CLASSE'] != None and campos['CLASSE'] != fundo.descricao_classe():
#                         fundo.classe = FundoInvestimento.buscar_tipo_classe(campos['CLASSE'])
#                     if campos['NOME'] != None and campos['NOME'].strip() != fundo.nome:
#                         fundo.nome = campos['NOME'].strip()
#                     fundo.save()
#                 
#             # Adicionar a lista de fundos para comparar posteriormente
# #             if not options['aleatorio']:
# #                 fundos.append(campos['CNPJ'])
#             
#             print novo_fundo             
#         documento = DocumentoCadastro.objects.get(data_referencia=dia_util)  
#         documento.leitura_realizada = True
#         documento.save()             
#     except:
#         # Apagar arquivo caso haja erro, enviar mensagem para email
#         try:
#             os.remove(nome_arquivo)
#         except OSError:
#             pass
#         if settings.ENV == 'DEV':
#             print traceback.format_exc()
#         elif settings.ENV == 'PROD':
#             mail_admins(u'Erro em Buscar fundos investimento na data %s' % (dia_util.strftime('%d/%m/%Y')), traceback.format_exc().decode('utf-8'))
#     # Verificar fundos que existem porém não foram listados, ou seja, estão terminados
#     if not options['aleatorio']:
#         # Verificar fundos não encontrados no cadastro para terminar
#         for fundo in FundoInvestimento.objects.all().exclude(situacao=FundoInvestimento.SITUACAO_TERMINADO):
#             if fundo.cnpj not in fundos:
#                 fundo.situacao = FundoInvestimento.SITUACAO_TERMINADO
#                 fundo.save()
    

def processar_linhas_documento_cadastro(rows, campos):
#     if 2 == 2:
#         rows = list()
#         continue
    
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
    
    inicio = datetime.datetime.now()
#     for row_atual in [row_dados for row_dados in rows if row_dados[campos['CNPJ_ADMIN']] != '']:
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
#                 if fundo.ultimo_registro < data_documento:
#                     fundo.ultimo_registro = data_documento
                # Verificar alterações
                alterado = False
                if row_atual[campos['CNPJ_ADMIN']] != '' and (fundo.administrador == None or row_atual[campos['CNPJ_ADMIN']] != fundo.administrador.cnpj):
                    for administrador in lista_administradores_existentes:
                        if administrador.cnpj == row_atual[campos['CNPJ_ADMIN']]:
                            fundo.administrador = administrador
                            alterado = True
                            break
#                     fundo.administrador = Administrador.objects.get(cnpj=row_atual[campos['CNPJ_ADMIN']])
                if row_atual[campos['CNPJ_AUDITOR']] != '' and (fundo.auditor == None or row_atual[campos['CNPJ_AUDITOR']] != fundo.auditor.cnpj):
                    for auditor in lista_auditores_existentes:
                        if auditor.cnpj == row_atual[campos['CNPJ_AUDITOR']]:
                            fundo.auditor = auditor
                            alterado = True
                            break
#                     fundo.auditor = Auditor.objects.get(cnpj=row_atual[campos['CNPJ_AUDITOR']])
                if row_atual[campos['SIT']] != '' and row_atual[campos['SIT']].upper() != fundo.descricao_situacao().upper():
#                     print row_atual[campos['SIT']].upper(), fundo.descricao_situacao().upper(), fundo.cnpj
                    fundo.situacao = FundoInvestimento.buscar_tipo_situacao(row_atual[campos['SIT']])
                    alterado = True
                if row_atual[campos['CLASSE']] != '' and row_atual[campos['CLASSE']].upper() != fundo.descricao_classe().upper():
#                     print row_atual[campos['CLASSE']].upper(), fundo.descricao_classe().upper()
                    fundo.classe = FundoInvestimento.buscar_tipo_classe(row_atual[campos['CLASSE']])
                    alterado = True
                if row_atual[campos['DENOM_SOCIAL']] != '' and row_atual[campos['DENOM_SOCIAL']] != fundo.nome:
#                     print row_atual[campos['DENOM_SOCIAL']], '<-', fundo.nome
                    fundo.nome = row_atual[campos['DENOM_SOCIAL']]
                    # Alterar slug
                    fundo.slug = criar_slug_fundo_investimento_valido(fundo.nome)
                    alterado = True
                if row_atual[campos['DT_CANCEL']] != '' and fundo.data_cancelamento == None:
#                     print row_atual[campos['CLASSE']].upper(), fundo.descricao_classe().upper()
                    fundo.data_cancelamento = row_atual[campos['DT_CANCEL']]
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
                                       tipo_prazo=definir_prazo__pelo_cadastro(row_atual[campos['TRIB_LPRAZO']]),
                                       classe=FundoInvestimento.buscar_tipo_classe(row_atual[campos['CLASSE']]), exclusivo_qualificados=(row_atual[campos['INVEST_QUALIF']].upper() == 'S'),
                                       data_registro=datetime.datetime.strptime(row_atual[campos['DT_REG']], '%Y-%m-%d'),
                                       slug=criar_slug_fundo_investimento_valido(row_atual[campos['DENOM_SOCIAL']]))
            if row_atual[campos['CNPJ_ADMIN']] != '':
                for administrador in lista_administradores_existentes:
                    if administrador.cnpj == row_atual[campos['CNPJ_ADMIN']]:
                        novo_fundo.administrador = administrador
                        break
#                 novo_fundo.administrador=Administrador.objects.get(cnpj=row_atual[campos['CNPJ_ADMIN']])
            if row_atual[campos['CNPJ_AUDITOR']] != '':
                for auditor in lista_auditores_existentes:
                    if auditor.cnpj == row_atual[campos['CNPJ_AUDITOR']]:
                        novo_fundo.auditor = auditor
                        break
#                 novo_fundo.auditor=Auditor.objects.get(cnpj=row_atual[campos['CNPJ_AUDITOR']])
            if row_atual[campos['DT_CANCEL']] != '':
                novo_fundo.data_cancelamento=row_atual[campos['DT_CANCEL']]
            novo_fundo.save()
            
            # Adicionar gestor
            for gestor in lista_gestores_existentes:
                if gestor.cnpj == row_atual[campos['CPF_CNPJ_GESTOR']]:
                    gestor_fundo_investimento = GestorFundoInvestimento(fundo_investimento=novo_fundo, gestor=gestor)
                    gestor_fundo_investimento.save()
                    break
            
#             lista_fundos_existentes.append(novo_fundo)
            lista_fundos_existentes.insert(0, novo_fundo) 
    print 'fundo', datetime.datetime.now() - inicio
  
#     # Adicionar a lista de fundos para comparar posteriormente
#     for row_atual in rows:
#         fundos.append(row_atual[campos['CNPJ_FUNDO']])   

def definir_prazo__pelo_cadastro(str_tributacao_documento):
    return FundoInvestimento.PRAZO_CURTO if str_tributacao_documento.strip().upper() == 'N' else FundoInvestimento.PRAZO_LONGO