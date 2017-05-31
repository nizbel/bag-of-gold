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
#             respostaCompetencias = client.service.solicAutorizDownloadCadastro(ultimo_dia_util() - datetime.timedelta(days=1000), 'Teste', _soapheaders=[headerSessao])
#             print respostaCompetencias
#             url = respostaCompetencias['body']['solicAutorizDownloadCadastroResult']
            url = 'http://cvmweb.cvm.gov.br/swb/sistemas/scw/DownloadArqs/LeDownloadArqs.aspx?VL_GUID=bbb5ba32-06c0-4e33-b182-f6fb2f3e2b36&PK_SESSAO=963302186&PK_ARQ_INFORM_DLOAD=196451'
#             url_antiga = 'http://cvmweb.cvm.gov.br/swb/sistemas/scw/DownloadArqs/LeDownloadArqs.aspx?VL_GUID=95f00a14-1167-4b4b-8824-b690f4acd43f&PK_SESSAO=963302550&PK_ARQ_INFORM_DLOAD=189882'
            download = urlopen(url)
            arquivo_zipado = StringIO(download.read())
            unzipped = zipfile.ZipFile(arquivo_zipado)
#             print unzipped.namelist()
            for libitem in unzipped.namelist():
                filecontent = file(libitem,'wb').write(unzipped.read(libitem))
                arquivo_cadastro = file(libitem, 'r')
                tree = etree.parse(arquivo_cadastro)
                # Listas para verificar opções de classe e situação
#                 lista_classe = list()
#                 lista_situacao = list()
                for element in tree.getroot().iter('CADASTRO'):
                    for elemento in element.iter():
#                     print [(elemento, elemento.text) for elemento in element.iter()]
#                         if elemento.tag == 'SITUACAO':
#                             if elemento.text not in lista_situacao:
#                                 lista_situacao.append(elemento.text)
#                         if elemento.tag == 'CLASSE':
#                             if elemento.text not in lista_classe:
#                                 lista_classe.append(elemento.text)
#                 print lista_classe
#                 print lista_situacao
                
        except Exception as e:
            print 'Erro:', unicode(e)

def ultimo_dia_util():
    dia = datetime.date.today() - datetime.timedelta(days=1)
    while dia.weekday() > 4 or verificar_feriado_bovespa(dia):
        dia = dia - datetime.timedelta(days=1)
    return dia