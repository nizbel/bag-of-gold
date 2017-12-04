# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import ProventoFIIDocumento, \
    DocumentoProventoBovespa
from django.core.management.base import BaseCommand
from django.db import transaction
import datetime
import traceback


class Command(BaseCommand):
    help = 'TEMPORÁRIO Corrige proventos de FII que foram adicionados erroneamente sob a empresa GWIR'
    

    def handle(self, *args, **options):
        documentos = DocumentoProventoBovespa.objects.filter(tipo='F', data_referencia__gt=datetime.date(2017, 8, 20)).order_by('data_referencia')
#         proventos = ProventoFIIDocumento.objects.all()
        elementos_a_apagar = list()
#         print documentos.count()
        try:
            with transaction.atomic():
                for documento in documentos:
#                     print documento.ticker_empresa(), documento.documento.name, \
#                         ProventoFIIDocumento.objects.filter(documento=documento).count(), documento.data_referencia
                    for provento in ProventoFIIDocumento.objects.filter(documento=documento):
                        if provento not in elementos_a_apagar:
                            elementos_a_apagar.append(provento)
                        if provento.descricao_provento not in elementos_a_apagar:
                            elementos_a_apagar.append(provento.descricao_provento)
                        if provento.provento not in elementos_a_apagar:
                            elementos_a_apagar.append(provento.provento)
                    if documento not in elementos_a_apagar:
                        elementos_a_apagar.append(documento)
#                         provento.provento.delete()
#                         provento.documento.delete()
#                         provento.descricao_provento.delete()
#                         provento.delete()
                
                for elemento in reversed(elementos_a_apagar):
                    elemento.delete()
#                 print DocumentoProventoBovespa.objects.filter(tipo='F', data_referencia__gt=datetime.date(2017, 8, 20)).count()
#                 for provento in ProventoFIIDocumento.objects.all():
#                     if provento.provento.fii.ticker[:4] != provento.documento.ticker_empresa():
#                         print provento.documento.ticker_empresa(), provento.provento.fii.ticker, \
#                             ProventoFIIDocumento.objects.filter(documento=provento.documento).count()
#                 if 2 == 2:
#                     raise ValueError('Teste')
        except:
            print traceback.format_exc()