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
        parser.add_argument('--anual', action='store_true')
        parser.add_argument('--arquivo', action='store_true')
        
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
