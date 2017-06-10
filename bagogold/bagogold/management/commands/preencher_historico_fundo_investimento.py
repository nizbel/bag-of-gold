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
                # Data fixa para buscar todos os dias a partir
                data_pesquisa = datetime.date(2017, 5, 26)
                print data_pesquisa
                try:
                    respostaCompetencias = client.service.solicAutorizDownloadArqComptc(209, data_pesquisa, 'Teste', _soapheaders=[headerSessao])
                    print respostaCompetencias
                except zeep.exceptions.Fault as erro_wsdl:
                    print unicode(erro_wsdl)
                if 2 == 2:
                    return
            elif options['arquivo']:
                pass
                # Ler da pasta específica para fundos de investimento
#                 for file in pasta:
#                     ler_arquivo()
            else:
                # Buscar último dia útil
#                 data_pesquisa = ultimo_dia_util()
                # TODO apagar codigo de teste
                unzipped = zipfile.ZipFile(file('20170527000000dfea0fc03d0e46978ec6cd53a11e2c5b.zip', 'r'))
                for libitem in unzipped.namelist()[:100]:
#                     print libitem
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
                                # Verificar se valor da cota é maior que 0
#                                 if valor_cota > 0:
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

#                         historicos = list()
#                         texto_arquivo = re.sub('<INFORME_DIARIO>.*?<VL_QUOTA>[\s0,]*?</VL_QUOTA>.*?</INFORME_DIARIO>', '', unzipped.read(libitem))
#                         for informe_diario in re.findall('<INFORME_DIARIO>.*?</INFORME_DIARIO>', texto_arquivo, re.DOTALL):
#                             print 'fundo', formatar_cnpj(informe_diario.split('<CNPJ_FDO>')[1].split('</CNPJ_FDO>')[0])
#                             print 'valor', Decimal(re.sub('[^\d,]', '', informe_diario.split('<VL_QUOTA>')[1].split('</VL_QUOTA>')[0]).replace(',', '.'))
#                             print 'data', informe_diario.split('<DT_COMPTC>')[1].split('</DT_COMPTC>')[0]
#                             cnpj_fundo = formatar_cnpj(informe_diario.split('<CNPJ_FDO>')[1].split('</CNPJ_FDO>')[0].strip())
#                             if FundoInvestimento.objects.filter(cnpj=cnpj_fundo).exists():
#                                 fundo = FundoInvestimento.objects.get(cnpj=cnpj_fundo)
#                                 data = informe_diario.split('<DT_COMPTC>')[1].split('</DT_COMPTC>')[0].strip()
#                                 if not HistoricoValorCotas.objects.filter(data=data, fundo_investimento=fundo).exists():
#                                 valor_cota = Decimal(re.sub('[^\d,]', '', informe_diario.split('<VL_QUOTA>')[1].split('</VL_QUOTA>')[0]).replace(',', '.'))
#                                     historico_fundo = HistoricoValorCotas(data=data, fundo_investimento=fundo, valor_cota=valor_cota)
#                                     historicos.append(historico_fundo)
                                    
                                    
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
        except:
            raise

        print datetime.datetime.now() - inicio_geral

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