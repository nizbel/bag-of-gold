# -*- coding: utf-8 -*-
from StringIO import StringIO
from bagogold import settings
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from bagogold.fundo_investimento.models import FundoInvestimento, Administrador, \
    DocumentoCadastro, LinkDocumentoCadastro
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction
from lxml import etree
from urllib2 import urlopen
import datetime
import os
import random
import time
import traceback
import zeep
import zipfile

class Command(BaseCommand):
    help = 'Buscar fundos de investimento na CVM'

    def handle(self, *args, **options):
        FundoInvestimento.objects.all().delete()
        Administrador.objects.all().delete()
        try:
            wsdl = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
            client = zeep.Client(wsdl=wsdl)
            resposta = client.service.Login(2377, '16335')
            headerSessao = resposta['header']
    #         print headerSessao
        
            # Buscar dias úteis que não tenham sido inseridos previamente
            dias_uteis = [ultimo_dia_util() - datetime.timedelta(days=1)]
            for _ in range(2):
                dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                while DocumentoCadastro.objects.filter(data_referencia=dia_util).exists():
                    dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                dias_uteis.append(dia_util)
            
            # Busca de competencias
            for dia_util in dias_uteis:
                print 'Dia', dia_util
                respostaCompetencias = client.service.solicAutorizDownloadCadastro(dia_util, 'Teste', _soapheaders=[headerSessao])
                # Criar documento
                novo_documento = DocumentoCadastro.objects.create(data_referencia=dia_util, data_pedido_cvm=datetime.date.today())
                url = respostaCompetencias['body']['solicAutorizDownloadCadastroResult']
                # Criar link
                LinkDocumentoCadastro.objects.create(url=url, documento=novo_documento)
#                 url = 'http://cvmweb.cvm.gov.br/swb/sistemas/scw/DownloadArqs/LeDownloadArqs.aspx?VL_GUID=8fc00daf-4fc8-4d83-bc4c-3e45cc79576c&PK_SESSAO=963322175&PK_ARQ_INFORM_DLOAD=196451'
                download = urlopen(url)
                arquivo_zipado = StringIO(download.read())
                unzipped = zipfile.ZipFile(arquivo_zipado)
#                 print unzipped.namelist()
                for libitem in unzipped.namelist():
                    file(libitem,'wb').write(unzipped.read(libitem))
                    arquivo_cadastro = file(libitem, 'r')
                    tree = etree.parse(arquivo_cadastro)
                    fundos = list()
                    try:
                        with transaction.atomic():
                            # Lê o arquivo procurando nós CADASTRO (1 para cada fundo)
                            for element in tree.getroot().iter('CADASTRO'):
                                campos = {key: value for (key, value) in [(elemento.tag, elemento.text) for elemento in element.iter()]}
                                # Verificar se administrador já existe
                                if not Administrador.objects.filter(cnpj=campos['CNPJ_ADMINISTRADOR']).exists():
                                    novo_administrador = Administrador(nome=campos['NOME_ADMINISTRADOR'], cnpj=campos['CNPJ_ADMINISTRADOR'])
                                    novo_administrador.save()
                                 
                                # Verificar se fundo já existe
                                if not FundoInvestimento.objects.filter(cnpj=campos['CNPJ']).exists():
                                    novo_fundo = FundoInvestimento(cnpj=campos['CNPJ'], nome=campos['NOME'], administrador=Administrador.objects.get(cnpj=campos['CNPJ_ADMINISTRADOR']),
                                                                   data_constituicao=campos['DT_CONSTITUICAO'], situacao=FundoInvestimento.buscar_tipo_situacao(campos['SITUACAO']), 
                                                                   tipo_prazo=(FundoInvestimento.PRAZO_LONGO if campos['TRATAMENTO_TRIBUTARIO'].upper() == 'SIM' else FundoInvestimento.PRAZO_CURTO),
                                                                   classe=FundoInvestimento.buscar_tipo_classe(campos['CLASSE']), exclusivo_qualificados=(campos['INVESTIDORES_QUALIFICADOS'].upper() == 'SIM'))
                                    novo_fundo.save()
                                else:
                                    # TODO Verificar se houve alteração no fundo
                                    pass
                                
                                
    #                             print novo_fundo                                                                  
                    except:
                        raise
                    os.remove(libitem)
                # TODO verificar fundos que existem porém não foram listados, ou seja, estão terminados
                
        except:
            if settings.ENV == 'DEV':
                if campos:
                    print campos
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar fundos investimento', traceback.format_exc())

def ultimo_dia_util():
    dia = datetime.date.today() - datetime.timedelta(days=1)
    while dia.weekday() > 4 or verificar_feriado_bovespa(dia):
        dia = dia - datetime.timedelta(days=1)
    return dia

def buscar_data_aleatoria(data_inicial, data_final):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """
    stime = time.mktime(data_inicial.timetuple())
    etime = time.mktime(data_final.timetuple())

    ptime = stime + random.random() * (etime - stime)

    return datetime.date.fromtimestamp(ptime)

def buscar_dia_util_aleatorio(data_inicial, data_final):
    data_aleatoria = buscar_data_aleatoria(data_inicial, data_final)
    while data_aleatoria.weekday() > 4 or verificar_feriado_bovespa(data_aleatoria):
        data_aleatoria = buscar_data_aleatoria(data_inicial, data_final)
    return data_aleatoria