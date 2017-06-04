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
import re
import time
import traceback
import zeep
import zipfile

threads_rodando = {'Principal': 1}
historico_adicionar = list()

class SalvarHistoricoThread(Thread):
    def run(self):
        try:
            while len(historico_adicionar) > 0 or 'Principal' in threads_rodando.keys():
#                 inicio = datetime.datetime.now()
                try:
                    with transaction.atomic():
#                         if 'Principal' in threads_rodando.keys():
#                             while len(historico_adicionar) > 0:
#                                 historico = historico_adicionar.pop()
#                                 historico.save()
#                         else:
#                             for historico in historico_adicionar:
#                                 historico.save()
#                             del historico_adicionar[:]
                        HistoricoValorCotas.objects.bulk_create(historico_adicionar)
                        del historico_adicionar[:]
                except:
                    print 'erro no insert atomico'
                 
#                 print 'Tempo:', datetime.datetime.now() - inicio
                 
        except Exception as e:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(e).__name__, e.args)
                print message

class Command(BaseCommand):
    help = 'Preencher historico de fundos de investimento'

    def add_arguments(self, parser):
        parser.add_argument('--anual', action='store_true')
        parser.add_argument('--arquivo', action='store_true')
        
    def handle(self, *args, **options):
        HistoricoValorCotas.objects.all().delete()
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
                for libitem in unzipped.namelist()[:60]:
                    print libitem
                    inicio = datetime.datetime.now()
                    erros = 0
                    try:
                        # Ler arquivo
                        file(libitem,'wb').write(unzipped.read(libitem))
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
                                        valor_cota = Decimal(re.sub('[^\d,]', '', campos['VL_QUOTA']).replace(',', '.'))
                                        if valor_cota > 0:
                                            historico_fundo = HistoricoValorCotas(data=campos['DT_COMPTC'].strip(), fundo_investimento=fundo, valor_cota=valor_cota)
                                            historicos.append(historico_fundo)
                            except:
                                erros += 1
                                continue
                        with transaction.atomic():
                            HistoricoValorCotas.objects.bulk_create(historicos)
                    except:
                        print 'erro geral'
                        continue
                    print 'Tempo:', datetime.datetime.now() - inicio, 'Erros:', erros
        except:
            raise
        while 'Principal' in threads_rodando.keys():
            del threads_rodando['Principal']

        # Criar thread para salvar os valores de histórico
#         thread_salvar_historico = SalvarHistoricoThread()
#         thread_salvar_historico.start()
#         thread_salvar_historico.join()
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