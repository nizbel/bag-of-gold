# -*- coding: utf-8 -*-
from StringIO import StringIO
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from django.core.management.base import BaseCommand
from lxml import etree
from urllib2 import urlopen
import datetime
import zeep
import zipfile

class Command(BaseCommand):
    help = 'Buscar fundos de investimento na CVM'

    def handle(self, *args, **options):
        wsdl = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
        client = zeep.Client(wsdl=wsdl)
        resposta = client.service.Login(2377, '16335')
        headerSessao = resposta['header']
#         print headerSessao
        
        # Busca de competencias
        try:
#             respostaCompetencias = client.service.solicAutorizDownloadCadastro(ultimo_dia_util(), 'Teste', _soapheaders=[headerSessao])
#             print respostaCompetencias
#             url = respostaCompetencias['body']['solicAutorizDownloadCadastroResult']
            url = 'http://cvmweb.cvm.gov.br/swb/sistemas/scw/DownloadArqs/LeDownloadArqs.aspx?VL_GUID=db4de580-e312-4428-81c9-bc9b4ca3d2da&PK_SESSAO=963284648&PK_ARQ_INFORM_DLOAD=196451'
            download = urlopen(url)
            arquivo_zipado = StringIO(download.read())
            unzipped = zipfile.ZipFile(arquivo_zipado)
            print unzipped.namelist()
            for libitem in unzipped.namelist():
                filecontent = file(libitem,'wb').write(unzipped.read(libitem))
                arquivo_cadastro = file(libitem, 'r')
                print arquivo_cadastro
                tree = etree.parse(arquivo_cadastro)
                # Listas para verificar opções de classe e situação
                lista_classe = list()
                lista_situacao = list()
                for element in tree.getroot().iter('CADASTRO'):
                    print [(elemento, elemento.text) for elemento in element.iter()]
        except Exception as e:
            print 'Erro:', unicode(e)

def ultimo_dia_util():
    dia = datetime.date.today() - datetime.timedelta(days=1)
    while dia.weekday() > 4 or verificar_feriado_bovespa(dia):
        dia = dia - datetime.timedelta(days=1)
    return dia