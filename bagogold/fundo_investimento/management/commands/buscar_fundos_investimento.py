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
    DocumentoCadastro, LinkDocumentoCadastro
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
#                     data_pesquisa = datetime.date.today()
#                 link_arquivo_csv, nome_arquivo, arquivo_csv = buscar_arquivo_csv_cadastro(data_pesquisa)
#                    
#                 # Gerar documento
#                 novo_documento = DocumentoCadastro.objects.create(data_referencia=data_pesquisa, data_pedido_cvm=datetime.date.today())
#                 LinkDocumentoCadastro.objects.create(url=link_arquivo_csv, documento=novo_documento)
#                  
#                 # Salvar arquivo em media no bucket
#                 caminho_arquivo = CAMINHO_FUNDO_INVESTIMENTO_CADASTRO + nome_arquivo
#                 boto3.client('s3').put_object(Body=arquivo_csv.read(), Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
            
            # Processar arquivo
#             processar_arquivo_csv(arquivo_csv)
            with open('../Downloads/inf_cadastral_fi_20181026.csv') as f:
                processar_arquivo_csv(novo_documento, f, data_pesquisa)
            
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

def processar_arquivo_csv(documento, dados_arquivo, data_documento):
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
            
            fundos = list()
            
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
                    if row[campos['CNPJ_FUNDO']] == '' or row[campos['CNPJ_ADMIN']] == '':
#                         print 'CNPJ NAO PREENCHIDO'
                        continue
                    
                    # Formatar CNPJ
                    if len(row[campos['CNPJ_FUNDO']]) < 18:
                        row[campos['CNPJ_FUNDO']] = formatar_cnpj(row[campos['CNPJ_FUNDO']])
                        
                    # Formatar CNPJ de administrador
                    if len(row[campos['CNPJ_ADMIN']]) < 18:
                        row[campos['CNPJ_ADMIN']] = formatar_cnpj(row[campos['CNPJ_ADMIN']])
                            
                    rows.append(row)
                    
                    if linha % 100 == 0:
                        # Guardar administradores únicos válidos
                        lista_administradores = [{'ADMIN': row_atual[campos['ADMIN']], 'CNPJ_ADMIN': row_atual[campos['CNPJ_ADMIN']]} for row_atual in rows \
                                                 if row_atual[campos['CNPJ_ADMIN']] != '']
                        lista_administradores = [administrador for indice, administrador in enumerate(lista_administradores) \
                                                 if administrador not in lista_administradores[indice + 1:]]
                            
                        lista_administradores_existentes = Administrador.objects.filter(
                            cnpj__in=[administrador['CNPJ_ADMIN'] for administrador in lista_administradores]).values_list('cnpj', flat=True)
                        
                        # Verificar se administradores já existem
#                         inicio = datetime.datetime.now()
                        for administrador in [novo_admin for novo_admin in lista_administradores if novo_admin['CNPJ_ADMIN'] not in lista_administradores_existentes]:
#                         for administrador in lista_administradores:
#                             if administrador['CNPJ_ADMIN'] not in lista_administradores_existentes:
                                novo_administrador = Administrador(nome=administrador['ADMIN'], cnpj=administrador['CNPJ_ADMIN'])
                                novo_administrador.save()
#                         print datetime.datetime.now() - inicio
                                
#                         # Verificar se administrador já existe
#                         if not Administrador.objects.filter(cnpj=row[campos['CNPJ_ADMIN']]).exists():
#                             novo_administrador = Administrador(nome=row[campos['ADMIN']], cnpj=row[campos['CNPJ_ADMIN']])
#                             novo_administrador.save()
                             
                        # Verificar fundos existentes
                        lista_fundos_existentes = list(FundoInvestimento.objects.filter(
                            cnpj__in=[row_atual[campos['CNPJ_FUNDO']] for row_atual in rows]).select_related('administrador'))
#                         lista_cnpjs_existentes = [fundo_existente.cnpj for fundo_existente in lista_fundos_existentes]
                        
#                         fundos_criados = list()
                        
#                         inicio = datetime.datetime.now()
#                         for row_atual in [row_dados for row_dados in rows if row_dados[campos['CNPJ_ADMIN']] != '']:
                        for row_atual in rows:
                            encontrado = False
                            for fundo_existente in lista_fundos_existentes:
                                if row_atual[campos['CNPJ_FUNDO']] == fundo_existente.cnpj:
                                    # Verificar se houve alteração no fundo
                                    fundo = fundo_existente
                                    if fundo.ultimo_registro < data_documento:
                                        fundo.ultimo_registro = data_documento
                                        # Verificar alteração de administrador
                                        if row[campos['CNPJ_ADMIN']] != '' and row[campos['CNPJ_ADMIN']] != fundo.administrador.cnpj:
                                            fundo.administrador = Administrador.objects.get(cnpj=row[campos['CNPJ_ADMIN']])
                                        if row[campos['SIT']] != '' and row[campos['SIT']] != fundo.descricao_situacao():
                                            fundo.situacao = FundoInvestimento.buscar_tipo_situacao(row[campos['SIT']])
                                        if row[campos['CLASSE']] != '' and row[campos['CLASSE']] != fundo.descricao_classe():
                                            fundo.classe = FundoInvestimento.buscar_tipo_classe(row[campos['CLASSE']])
                                        if row[campos['DENOM_SOCIAL']] != '' and row[campos['DENOM_SOCIAL']] != fundo.nome:
                                            fundo.nome = row[campos['DENOM_SOCIAL']]
                                        fundo.save()
                                    encontrado = True
                                    break
                            
                            if not encontrado:
                                novo_fundo = FundoInvestimento(cnpj=row_atual[campos['CNPJ_FUNDO']], nome=row_atual[campos['DENOM_SOCIAL']], 
                                                           administrador=Administrador.objects.get(cnpj=row_atual[campos['CNPJ_ADMIN']]),
                                                           data_constituicao=row_atual[campos['DT_CONST']], situacao=FundoInvestimento.buscar_tipo_situacao(row_atual[campos['SIT']]), 
                                                           tipo_prazo=definir_prazo__pelo_cadastro(row_atual[campos['TRIB_LPRAZO']]),
                                                           classe=FundoInvestimento.buscar_tipo_classe(row_atual[campos['CLASSE']]), exclusivo_qualificados=(row_atual[campos['INVEST_QUALIF']].upper() == 'S'),
                                                           ultimo_registro=data_documento, slug=criar_slug_fundo_investimento_valido(row_atual[campos['DENOM_SOCIAL']]))
                                novo_fundo.save()
                                lista_fundos_existentes.append(novo_fundo)
#                         print datetime.datetime.now() - inicio
                                        
                                        
                            ### VERSAO FUNCIONAL
# #                             if row_atual[campos['CNPJ_FUNDO']] not in [fundo_existente.cnpj for fundo_existente in lista_fundos_existentes] and row_atual[campos['CNPJ_FUNDO']] not in fundos_criados:
# #                             if row_atual[campos['CNPJ_FUNDO']] not in [fundo_existente.cnpj for fundo_existente in lista_fundos_existentes]:
#                             if row_atual[campos['CNPJ_FUNDO']] not in lista_cnpjs_existentes:
#                                 novo_fundo = FundoInvestimento(cnpj=row_atual[campos['CNPJ_FUNDO']], nome=row_atual[campos['DENOM_SOCIAL']], 
#                                                            administrador=Administrador.objects.get(cnpj=row_atual[campos['CNPJ_ADMIN']]),
#                                                            data_constituicao=row_atual[campos['DT_CONST']], situacao=FundoInvestimento.buscar_tipo_situacao(row_atual[campos['SIT']]), 
#                                                            tipo_prazo=definir_prazo__pelo_cadastro(row_atual[campos['TRIB_LPRAZO']]),
#                                                            classe=FundoInvestimento.buscar_tipo_classe(row_atual[campos['CLASSE']]), exclusivo_qualificados=(row_atual[campos['INVEST_QUALIF']].upper() == 'S'),
#                                                            ultimo_registro=data_documento, slug=criar_slug_fundo_investimento_valido(row_atual[campos['DENOM_SOCIAL']]))
#                                 novo_fundo.save()
# #                                 fundos_criados.append(novo_fundo.cnpj)
#                                 lista_fundos_existentes.append(novo_fundo)
#                                 lista_cnpjs_existentes.append(novo_fundo.cnpj)
# #                             elif row_atual[campos['CNPJ_FUNDO']] not in fundos_criados:
#                             else:
#                                 # Verificar se houve alteração no fundo
#                                 fundo = [fundo_existente for fundo_existente in lista_fundos_existentes if fundo_existente.cnpj == row_atual[campos['CNPJ_FUNDO']]][0]
#                                 if fundo.ultimo_registro < data_documento:
#                                     fundo.ultimo_registro = data_documento
#                                     # Verificar alteração de administrador
#                                     if row[campos['CNPJ_ADMIN']] != '' and row[campos['CNPJ_ADMIN']] != fundo.administrador.cnpj:
#                                         fundo.administrador = Administrador.objects.get(cnpj=row[campos['CNPJ_ADMIN']])
#                                     if row[campos['SIT']] != '' and row[campos['SIT']] != fundo.descricao_situacao():
#                                         fundo.situacao = FundoInvestimento.buscar_tipo_situacao(row[campos['SIT']])
#                                     if row[campos['CLASSE']] != '' and row[campos['CLASSE']] != fundo.descricao_classe():
#                                         fundo.classe = FundoInvestimento.buscar_tipo_classe(row[campos['CLASSE']])
#                                     if row[campos['DENOM_SOCIAL']] != '' and row[campos['DENOM_SOCIAL']] != fundo.nome:
#                                         fundo.nome = row[campos['DENOM_SOCIAL']]
#                                     fundo.save()
                            ### FIM VERSAO FUNCIONAL
                                
#                         # Verificar se fundo já existe
#                         if not FundoInvestimento.objects.filter(cnpj=row[campos['CNPJ_FUNDO']]).exists():
#                             novo_fundo = FundoInvestimento(cnpj=row[campos['CNPJ_FUNDO']], nome=row[campos['DENOM_SOCIAL']], 
#                                                            administrador=Administrador.objects.get(cnpj=row[campos['CNPJ_ADMIN']]),
#                                                            data_constituicao=row[campos['DT_CONST']], situacao=FundoInvestimento.buscar_tipo_situacao(row[campos['SIT']]), 
#                                                            tipo_prazo=definir_prazo__pelo_cadastro(row[campos['TRIB_LPRAZO']]),
#                                                            classe=FundoInvestimento.buscar_tipo_classe(row[campos['CLASSE']]), exclusivo_qualificados=(row[campos['INVEST_QUALIF']].upper() == 'S'),
#                                                            ultimo_registro=data_documento, slug=criar_slug_fundo_investimento_valido(row[campos['DENOM_SOCIAL']]))
#                             novo_fundo.save()
#                         else:
#                             # Verificar se houve alteração no fundo
#                             fundo = FundoInvestimento.objects.filter(cnpj=row[campos['CNPJ_FUNDO']]).select_related('administrador')[0]
#                             if fundo.ultimo_registro < data_documento:
#                                 fundo.ultimo_registro = data_documento
#                                 # Verificar alteração de administrador
#                                 if row[campos['CNPJ_ADMIN']] != '' and row[campos['CNPJ_ADMIN']] != fundo.administrador.cnpj:
#                                     fundo.administrador = Administrador.objects.get(cnpj=row[campos['CNPJ_ADMIN']])
#                                 if row[campos['SIT']] != '' and row[campos['SIT']] != fundo.descricao_situacao():
#                                     fundo.situacao = FundoInvestimento.buscar_tipo_situacao(row[campos['SIT']])
#                                 if row[campos['CLASSE']] != '' and row[campos['CLASSE']] != fundo.descricao_classe():
#                                     fundo.classe = FundoInvestimento.buscar_tipo_classe(row[campos['CLASSE']])
#                                 if row[campos['DENOM_SOCIAL']] != '' and row[campos['DENOM_SOCIAL']] != fundo.nome:
#                                     fundo.nome = row[campos['DENOM_SOCIAL']]
#                                 fundo.save()
                              
                        # Adicionar a lista de fundos para comparar posteriormente
                        for row_atual in rows:
                            fundos.append(row_atual[campos['CNPJ_FUNDO']])   
                        
                        rows = list()    
             
            print datetime.datetime.now() - inicio_geral
            # Verificar fundos que existem porém não foram listados, ou seja, estão terminados
            # Verificar fundos não encontrados no cadastro para terminar
            qtd_terminados = 0
            for fundo in FundoInvestimento.objects.filter(ultimo_registro__lt=data_documento).exclude(situacao=FundoInvestimento.SITUACAO_TERMINADO):
                if fundo.cnpj not in fundos:
                    fundo.situacao = FundoInvestimento.SITUACAO_TERMINADO
                    fundo.save()
                    qtd_terminados += 1
            print 'TERMINADOS', qtd_terminados
                         
#             documento = DocumentoCadastro.objects.get(data_referencia=data_documento)  
            documento.leitura_realizada = True
            documento.save() 
            
            if 2 == 2:
                raise ValueError('TESTE')
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
    
    
def definir_prazo__pelo_cadastro(str_tributacao_documento):
    return FundoInvestimento.PRAZO_CURTO if str_tributacao_documento.strip().upper() == 'N' else FundoInvestimento.PRAZO_LONGO