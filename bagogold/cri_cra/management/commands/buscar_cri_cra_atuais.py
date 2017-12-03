# -*- coding: utf-8 -*-
from bagogold.bagogold.models.cri_cra import CRI_CRA
from decimal import Decimal
from django.core.management.base import BaseCommand
import datetime
import mechanize



class Command(BaseCommand):
    help = 'Busca os CRI e CRA atualmente válidos'

    def handle(self, *args, **options):
        # Buscar CRIs
        url_cri = 'https://www.cetip.com.br/tituloscri'
        # Usar mechanize para simular clique do usuario no javascript
        br = mechanize.Browser()
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        response = br.open(url_cri)

        # Prepara para clicar no preenchimento da tabela        
        br.select_form(nr=0)
        br.set_all_readonly(False)
        
        br.find_control("ctl00$MainContent$btExportarCSV").disabled = True
        
        response = br.submit('ctl00$MainContent$btEnviar')
        
        # Clica na exportação da tabela
        br.select_form(nr=0)
        br.set_all_readonly(False)
        
        br.find_control("ctl00$MainContent$btEnviar").disabled = True
        
        response = br.submit('ctl00$MainContent$btExportarCSV')
        arquivo = response.read()
        for linha in arquivo.split('\n')[1:]:
            valores = linha.split(';')
            if len(valores) == 16:
                tipo = 'I'
                codigo = valores[0] 
                data_emissao = datetime.datetime.strptime(valores[7] , '%d/%m/%Y').date()
                valor_emissao = Decimal(valores[6].replace('.', '').replace(',', '.')) / Decimal(valores[5].replace('.', '').replace(',', '.')) 
                data_vencimento = datetime.datetime.strptime(valores[8] , '%d/%m/%Y').date()
                novo_cri = CRI_CRA(tipo=tipo, data_emissao=data_emissao, codigo=codigo, data_vencimento=data_vencimento, valor_emissao=valor_emissao)
#                 print novo_cri