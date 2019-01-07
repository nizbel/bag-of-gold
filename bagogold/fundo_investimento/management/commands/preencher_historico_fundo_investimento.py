# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
import os
import re
import traceback
from urllib2 import urlopen
import zipfile

from django.db import transaction
from lxml import etree
import zeep

from bagogold import settings
from bagogold.fundo_investimento.models import FundoInvestimento, \
    HistoricoValorCotas


class Command(BaseCommand):
    help = 'Preencher historico de fundos de investimento'

    def add_arguments(self, parser):
        parser.add_argument('--data', action='store_true')
        
        
        
        
        
        
    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Buscar arquivo CSV
                if options['data']:
                    data_pesquisa = datetime.datetime.strptime(options['data'], '%d%m%Y').date()
                else:
                    # Busca data do último dia útil
                    data_pesquisa = ultimo_dia_util()
                
                caminho_arquivo = CAMINHO_FUNDO_INVESTIMENTO_HISTORICO + nome_arquivo
                
                if not verificar_arquivo_s3(caminho_arquivo):
                # Caso o documento ainda não exista, baixar
                link_arquivo_csv, nome_arquivo, arquivo_csv = buscar_arquivo_csv_hiatorico(data_pesquisa)

                # Salvar arquivo em media no bucket
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
  


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    def handle(self, *args, **options):
        if options['anual'] and options['arquivo']:
            print 'Use apenas uma das opções, --anual ou --arquivo'
            return
        try:
            wsdl = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
            client = zeep.Client(wsdl=wsdl)
#             resposta = client.service.Login(FI_LOGIN, FI_PASSWORD)
            resposta = client.service.Login('FI_LOGIN', 'FI_PASSWORD')
            headerSessao = resposta['header']
#             print headerSessao

            if options['anual']:
                # Buscar arquivo anual
                try:
                    respostaCompetencias = client.service.solicAutorizDownloadArqAnual(209, 'Teste', _soapheaders=[headerSessao])
#                     print respostaCompetencias
                    download = urlopen(respostaCompetencias['body']['solicAutorizDownloadArqAnualResult'])
                    if 'filename=' in download.info()['Content-Disposition']:
                        nome_arquivo = re.findall('.*?filename\W*?([\d\w\.]+).*?', download.info()['Content-Disposition'])[0]
                    else:
                        nome_arquivo = datetime.date.today().strftime('anual%d-%m-%Y.zip')
                    file(settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO + nome_arquivo,'wb').write(download.read())
                except:
                    if settings.ENV == 'DEV':
                        print traceback.format_exc()
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro em Buscar historico anual de fundo de investimento', traceback.format_exc().decode('utf-8'))
                
            elif options['arquivo']:
                # Ler da pasta específica para fundos de investimento
                ver_arquivos_pasta()
                
            else:
                # Buscar último dia útil
                try:
                    resposta_ultimo_dia_util = client.service.solicAutorizDownloadArqEntrega(209, 'Teste', _soapheaders=[headerSessao])
#                     print resposta_ultimo_dia_util
                    download = urlopen(resposta_ultimo_dia_util['body']['solicAutorizDownloadArqEntregaResult'])
                    if 'filename=' in download.info()['Content-Disposition']:
                        nome_arquivo = re.findall('.*?filename\W*?([\d\w\.]+).*?', download.info()['Content-Disposition'])[0]
                    else:
                        nome_arquivo = datetime.date.today().strftime('ultimodia-%d-%m-%Y.zip')
                    file(settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO + nome_arquivo,'wb').write(download.read())
                    ver_arquivos_pasta()
                except:
                    if settings.ENV == 'DEV':
                        print traceback.format_exc()
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro em Buscar historico ultimo dia util de fundo de investimento', traceback.format_exc().decode('utf-8'))
        except:
            raise

def ver_arquivos_pasta():
    for arquivo in [os.path.join(settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO, arquivo) for arquivo in os.listdir(settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO) if os.path.isfile(os.path.join(settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO, arquivo))]:
        # Verifica se é zipado
        if zipfile.is_zipfile(arquivo):
            # Abrir e ler
            unzipped = zipfile.ZipFile(arquivo)
            # Guardar quantidade de erros
            qtd_erros = 0
            for libitem in unzipped.namelist():
                nome_arquivo = settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO + libitem
                # Escrever arquivo no disco para leitura
                file(nome_arquivo,'wb').write(re.sub('<INFORME_DIARIO>(?:(?!</INFORME_DIARIO>).)*<VL_QUOTA>[\s0,]*?</VL_QUOTA>.*?</INFORME_DIARIO>', '', unzipped.read(libitem), flags=re.DOTALL))
                qtd_erros += ler_arquivo(nome_arquivo)
            # Se quantidade de erros maior que 0, não apagar arquivo
            if qtd_erros == 0:
                os.remove(arquivo)
                    
        else:
            ler_arquivo(arquivo)
    
def ler_arquivo(libitem, apagar_caso_erro=True):
    erros = 0
    try:
        # Ler arquivo
        arquivo = file(libitem, 'r')
        tree = etree.parse(arquivo)
        # Guarda a quantidade a adicionar
        historicos = list()
        # Lê o arquivo procurando nós CADASTRO (1 para cada fundo)
        for element in tree.getroot().iter('INFORME_DIARIO'):
            try:
                campos = {key: value for (key, value) in [(elemento.tag, elemento.text) for elemento in element.iter()]}
                # Verificar se fundo existe
                if FundoInvestimento.objects.filter(cnpj=formatar_cnpj(campos['CNPJ_FDO'])).exists():
                    fundo = FundoInvestimento.objects.get(cnpj=formatar_cnpj(campos['CNPJ_FDO']))
                    if not HistoricoValorCotas.objects.filter(data=campos['DT_COMPTC'].strip(), fundo_investimento=fundo).exists():
                        valor_cota = Decimal(campos['VL_QUOTA'].strip().replace(',', '.'))
                        historico_fundo = HistoricoValorCotas(data=campos['DT_COMPTC'].strip(), fundo_investimento=fundo, valor_cota=valor_cota)
                        historicos.append(historico_fundo)
            except:
                erros += 1

        with transaction.atomic():
            # Limitar tamanho do bulk create para evitar erro de memoria
            limite_dados = 0
            while limite_dados < len(historicos):
                HistoricoValorCotas.objects.bulk_create(historicos[limite_dados:min(limite_dados+2000, len(historicos))])
                limite_dados += 2000
        os.remove(libitem)                                
    except:
        erros += 1
        # Apagar arquivo caso haja erro, enviar mensagem para email
        if apagar_caso_erro:
            os.remove(libitem)
        if settings.ENV == 'DEV':
            print traceback.format_exc()
        elif settings.ENV == 'PROD':
            mail_admins(u'Erro em Preencher histórico de fundos de investimento. Arquivo %s' % (libitem), traceback.format_exc().decode('utf-8'))
    return erros

def formatar_cnpj(string):
    string = re.sub(r'\D', '', string)
    while len(string) < 14:
        string = '0' + string
    return string[0:2] + '.' + string[2:5] + '.' + string[5:8] + '/' + string[8:12] + '-' + string[12:14]
