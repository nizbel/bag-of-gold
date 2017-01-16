# -*- coding: utf-8 -*-
from decimal import Decimal
from django.core.management.base import BaseCommand
from urllib2 import Request, urlopen, HTTPError, URLError
import datetime
import re



class Command(BaseCommand):
    help = 'Busca as Debêntures atualmente válidos'

    def handle(self, *args, **options):
        url_debentures = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/caracteristicas_r.asp?tip_deb=publicas&op_exc=Nada'
        
        codigos = buscar_lista_debentures(url_debentures)
#         codigos = ['AARJ11']
        for codigo in codigos:
            print codigo
#             buscar_info_debenture(codigo)
            buscar_historico_debenture(codigo)

def buscar_lista_debentures(url_debentures):
    req = Request(url_debentures)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        data = response.read()
        
        # Buscar pela URL padrão
        registros = re.findall('caracteristicas_d.asp\?tip_deb=publicas&selecao=([^"]+?)?"', data)
        registros = [registro.replace(' ', '') for registro in registros]
        
        return registros
    
def buscar_info_debenture(codigo):
    url_download_arquivo = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/caracteristicas_e.asp?Ativo=%s' % (codigo)
    req = Request(url_download_arquivo)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        data = response.read()

        for linha in data.decode('latin-1').split('\n'):
#             if u'Código do Ativo' in linha:
#                 for indice, campo in enumerate([campo.strip() for campo in linha.split('\t')]):
#                     print indice, campo
            if codigo in linha:
                campos = [campo.strip() for campo in linha.split('\t')]
                situacao = campos[5]
                data_emissao = datetime.datetime.strptime(campos[11] , '%d/%m/%Y').date()
                data_vencimento = None if campos[12] == 'Indeterminado' else datetime.datetime.strptime(campos[12] , '%d/%m/%Y').date()
                data_inicio_rentabilidade = campos[15]
                data_saida = campos[14]
                valor_nominal_emissao = campos[37]
                indice = campos[41]
                percentual_indice = campos[47]
                incentivada = campos[88]
#                 print ','.join(campos[41:71])

def buscar_historico_debenture(codigo):
    url_historico = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/puhistorico_e.asp?op_exc=Nada&ativo=%s&dt_ini=&dt_fim=' % (codigo)
    req = Request(url_historico)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        data = response.read()

        for linha in data.decode('latin-1').split('\n'):
#             if u'Código do Ativo' in linha:
#                 for indice, campo in enumerate([campo.strip() for campo in linha.split('\t')]):
#                     print indice, campo
            if codigo in linha:
                campos = [campo.strip() for campo in linha.split('\t')]
                if campos[4] != '-':
                    print campos[4], codigo, 'em', campos[0]
    
    # TODO ler como texto separado por \t
    
    