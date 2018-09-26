# -*- coding: utf-8 -*-
from cStringIO import StringIO
from urllib2 import Request, urlopen, HTTPError, URLError

from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa


class Command(BaseCommand):
    help = 'Copia documentos do site original para o site da AWS'

    def handle(documento, *args, **options):
        # TODO filtrar documentos que tenham sido validados como sem proventos
        for documento in DocumentoProventoBovespa.objects.all().exclude(investidorleituradocumento__decisao='E', investidorvalidacaodocumento__isnull=False):
            # Verifica se documento existe na AWS
            if documento.verificar_se_doc_existe():
                print 'documento existe'
            else:
                # Se não, buscar do bag of gold no rackspace
                url_documento = 'https://bagofgold.com.br' + reverse('gerador_proventos:baixar_documento_provento', kwargs={'id_documento': documento.id})
                print url_documento
                req = Request(url_documento)
                try:
                    response = urlopen(req, timeout=30)
                except HTTPError as e:
                    print 'The server couldn\'t fulfill the request.'
                    print 'Error code: ', e.code
                except URLError as e:
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
                else:
                    data = response.read()
                    
                    meta = response.info()
                    print meta
                    
                    extensao = ''
                    arquivo_rendimentos = StringIO(data)
                    documento.documento.save('%s-%s.%s' % (documento.ticker_empresa(), documento.protocolo, extensao), File(arquivo_rendimentos))
            
            if 2 == 2:
                raise ValueError('TESTE')