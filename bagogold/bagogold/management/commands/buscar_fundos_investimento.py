# -*- coding: utf-8 -*-
from StringIO import StringIO
from bagogold import settings
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from bagogold.fundo_investimento.models import FundoInvestimento, Administrador
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction
from lxml import etree
from urllib2 import urlopen
import datetime
import traceback
import zeep
import zipfile

class Command(BaseCommand):
    help = 'Buscar fundos de investimento na CVM'

    def handle(self, *args, **options):
        print FundoInvestimento.objects.all().count(), Administrador.objects.all().count()
        FundoInvestimento.objects.all().delete()
        Administrador.objects.all().delete()
        try:
            wsdl = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
            client = zeep.Client(wsdl=wsdl)
            resposta = client.service.Login(2377, '16335')
            headerSessao = resposta['header']
    #         print headerSessao
        
            # Busca de competencias
#             respostaCompetencias = client.service.solicAutorizDownloadCadastro(ultimo_dia_util(), 'Teste', _soapheaders=[headerSessao])
#             print respostaCompetencias
#             url = respostaCompetencias['body']['solicAutorizDownloadCadastroResult']
            url = 'http://cvmweb.cvm.gov.br/swb/sistemas/scw/DownloadArqs/LeDownloadArqs.aspx?VL_GUID=8fc00daf-4fc8-4d83-bc4c-3e45cc79576c&PK_SESSAO=963322175&PK_ARQ_INFORM_DLOAD=196451'
            download = urlopen(url)
            arquivo_zipado = StringIO(download.read())
            unzipped = zipfile.ZipFile(arquivo_zipado)
#             print unzipped.namelist()
            for libitem in unzipped.namelist():
                filecontent = file(libitem,'wb').write(unzipped.read(libitem))
                arquivo_cadastro = file(libitem, 'r')
                tree = etree.parse(arquivo_cadastro)
                try:
                    with transaction.atomic():
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
                            
                            print novo_fundo                                                                  
                except:
                    raise
        except:
            if settings.ENV == 'DEV':
                print campos
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar fundos investimento', traceback.format_exc())

def ultimo_dia_util():
    dia = datetime.date.today() - datetime.timedelta(days=1)
    while dia.weekday() > 4 or verificar_feriado_bovespa(dia):
        dia = dia - datetime.timedelta(days=1)
    return dia