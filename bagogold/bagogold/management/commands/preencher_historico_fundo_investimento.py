# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.utils.misc import ultimo_dia_util
from bagogold.fundo_investimento.models import FundoInvestimento, \
    HistoricoValorCotas
from decimal import Decimal
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction
from lxml import etree
from threading import Thread
from urllib2 import urlopen
import StringIO
import datetime
import os
import re
import time
import traceback
import zeep
import zipfile

class Command(BaseCommand):
    help = 'Preencher historico de fundos de investimento'

    def add_arguments(self, parser):
        parser.add_argument('--anual', action='store_true')
        parser.add_argument('--arquivo', action='store_true')
        
    def handle(self, *args, **options):
        if options['anual'] and options['arquivo']:
            print 'Use apenas uma das opções, --anual ou --arquivo'
#         HistoricoValorCotas.objects.all().delete()
        inicio_geral = datetime.datetime.now()
        try:
            wsdl = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
            client = zeep.Client(wsdl=wsdl)
            resposta = client.service.Login(2377, '16335')
            headerSessao = resposta['header']
#             print headerSessao

            dias_uteis = list()
            if options['anual']:
                # Buscar arquivo anual
                try:
                    respostaCompetencias = client.service.solicAutorizDownloadArqAnual(209, 'Teste', _soapheaders=[headerSessao])
#                     print respostaCompetencias
                    download = urlopen(respostaCompetencias['body']['solicAutorizDownloadArqAnualResult'])
                    arquivo_zipado = StringIO(download.read())
                    
                    # TESTE BUSCAR NOME ARQUIVO
                    req = Request(respostaCompetencias['body']['solicAutorizDownloadArqAnualResult'])
                    try:
                        response = urlopen(req, timeout=30)
                    except HTTPError as e:
                        print 'The server couldn\'t fulfill the request.'
                        print 'Error code: ', e.code
                        return 
                    except URLError as e:
                        print 'We failed to reach a server.'
                        print 'Reason: ', e.reason
                        return 
                    # Buscar informações da extensão
                    extensao = ''
                    meta = response.info()
                #     print meta
                    # Busca extensão pelo content disposition, depois pelo content-type se não encontrar
                    if meta.getheaders("Content-Disposition"):
                        content_disposition = meta.getheaders("Content-Disposition")[0]
                        if 'filename=' in content_disposition:
                            inicio = content_disposition.find('filename=')
                            fim = content_disposition.find(';', inicio) if content_disposition.find(';', inicio) != -1 else len(content_disposition)
                            if '.' in content_disposition[inicio:fim]:
                                extensao = content_disposition[inicio:fim].split('.')[-1].replace('"', '')
                    if extensao == '':
                        if meta.getheaders("Content-Type"):
                            content_type = meta.getheaders("Content-Type")[0]
                            if '/' in content_type:
                                extensao = content_type.split('/')[1]
                    resposta = response.read()
                #     print resposta
                    arquivo_rendimentos = StringIO(resposta)
                    return (arquivo_rendimentos, extensao)
                # FIM TESTE
                        
                except zeep.exceptions.Fault as erro_wsdl:
                    print unicode(erro_wsdl)
            elif options['arquivo']:
                # Ler da pasta específica para fundos de investimento
                ver_arquivos_pasta()
            else:
                # Buscar último dia útil
                try:
                    resposta_ultimo_dia_util = cliente.service.solicAutorizDownloadArqEntrega(209, 'Teste', _soapheaders=[headerSessao])
                except zeep.exceptions.Fault as erro_wsdl:
                    print unicode(erro_wsdl)
        except:
            raise

        print datetime.datetime.now() - inicio_geral

def ver_arquivos_pasta():
    onlyfiles = 
    for arquivo in [arquivo for arquivo in listdir(settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO) if isfile(join(settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO, arquivo))]:
        # Verifica se é zipado
        if zipfile.is_zipfile(arquivo):
            # Abrir e ler
            unzipped = zipfile.ZipFile(arquivo)
            for libitem in unzipped.namelist():
                nome_arquivo = settings.CAMINHO_FUNDO_INVESTIMENTO_HISTORICO + libitem
                # Escrever arquivo no disco para leitura
                file(nome_arquivo,'wb').write(unzipped.read(libitem))
                ler_arquivo(nome_arquivo)
        else:
            ler_arquivo(arquivo)
    
def ler_arquivo(libitem):
#     print libitem
    inicio = datetime.datetime.now()
    erros = 0
    try:
        # Ler arquivo
        file(libitem,'wb').write(re.sub('<INFORME_DIARIO>(?:(?!</INFORME_DIARIO>).)*<VL_QUOTA>[\s0,]*?</VL_QUOTA>.*?</INFORME_DIARIO>', '', unzipped.read(libitem), flags=re.DOTALL))
        arquivo_cadastro = file(libitem, 'r')
        tree = etree.parse(arquivo_cadastro)
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
                continue

        with transaction.atomic():
            HistoricoValorCotas.objects.bulk_create(historicos)
        
        os.remove(libitem)                                
    except:
        # Apagar arquivo caso haja erro, enviar mensagem para email
        os.remove(libitem)
        if settings.ENV == 'DEV':
            print traceback.format_exc()
        elif settings.ENV == 'PROD':
            mail_admins(u'Erro em Preencher histórico de fundos de investimento. Arquivo %s' % (libitem), traceback.format_exc())
        continue
    print 'Tempo:', datetime.datetime.now() - inicio, 'Erros:', erros

def formatar_cnpj(string):
    string = re.sub('\D', '', string)
    while len(string) < 14:
        string = '0' + string
    return string[0:2] + '.' + string[2:5] + '.' + string[5:8] + '/' + string[8:12] + '-' + string[12:14]
# def buscar_arquivo_zipado_cvm():
# 
# def extrair_arquivo(arquivo_zipado):
# 
# def ler_arquivo_diario(arquivo):