# -*- coding: utf-8 -*-
from bagogold.bagogold.models.debentures import HistoricoValorDebenture, \
    Debenture
from decimal import Decimal
from urllib2 import Request, urlopen, HTTPError, URLError
import datetime

def buscar_historico_debenture(codigo, data_inicio=''):
    if isinstance(data_inicio, datetime.date):
        data_inicio = data_inicio.strftime('%d/%m/%Y')
    url_historico = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/puhistorico_e.asp?op_exc=Nada&ativo=%s&dt_ini=%s&dt_fim=' % (codigo, data_inicio)
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
        # Carregar debenture
        debenture = Debenture.objects.get(codigo=codigo)

        for linha in data.decode('latin-1').split('\n'):
#             if u'Código do Ativo' in linha:
#                 for indice, campo in enumerate([campo.strip() for campo in linha.split('\t')]):
#                     print indice, campo
            if codigo in linha:
                campos = [campo.strip() for campo in linha.split('\t')]
                data = datetime.datetime.strptime(campos[0], '%d/%m/%Y').date()
                if not HistoricoValorDebenture.objects.filter(data=data, debenture=debenture).exists():
                    valor_nominal = Decimal(campos[2].replace('.', '').replace(',', '.'))
                    juros = Decimal(0) if campos[3] == '-' else Decimal(campos[3].replace('.', '').replace(',', '.'))
                    premio = Decimal(0) if campos[4] == '-' else Decimal(campos[4].replace('.', '').replace(',', '.'))
                    historico_debenture = HistoricoValorDebenture(data=data, debenture=debenture, valor_nominal=valor_nominal,
                                                                  juros=juros, premio=premio)
                    historico_debenture.save()
    