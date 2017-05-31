# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import zeep

class Command(BaseCommand):
    help = 'Preencher historico de fundos de investimento'

    def handle(self, *args, **options):
        wsdl = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
        client = zeep.Client(wsdl=wsdl)
        resposta = client.service.Login(2377, '16335')
        headerSessao = resposta['header']
        print headerSessao
        
        # Busca de competencias
        try:
            respostaCompetencias = client.service.solicAutorizDownloadArqAnual(209, 'Teste', _soapheaders=[headerSessao])
            print respostaCompetencias
        except Exception as e:
            print 'Erro:', unicode(e)
            
            