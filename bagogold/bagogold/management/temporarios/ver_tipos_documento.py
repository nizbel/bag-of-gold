# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, ProventoAcaoDocumento
from django.core.management.base import BaseCommand
from django.db.models.aggregates import Count

class Command(BaseCommand):
    help = 'TEMPORÁRIO mostra tipos de documento'

    def handle(self, *args, **options):
        print 'Tipos com provento:'
        documentos = ProventoAcaoDocumento.objects.filter(provento__oficial_bovespa=True).values_list('documento', flat=True)
        print DocumentoProventoBovespa.objects.filter(id__in=documentos).values('tipo_documento').annotate(Count('tipo_documento')).values_list('tipo_documento', 'tipo_documento__count')
        
        print 'Tipos excluidos:'
        pendencias = PendenciaDocumentoProvento.objects.all().values_list('documento', flat=True)
        print DocumentoProventoBovespa.objects.filter(investidorleituradocumento__decisao='E').exclude(id__in=pendencias).values('tipo_documento').annotate(Count('tipo_documento')).values_list('tipo_documento', 'tipo_documento__count')
        
        print 'Tipos total:'
        print DocumentoProventoBovespa.objects.all().values('tipo_documento').annotate(Count('tipo_documento')).values_list('tipo_documento', 'tipo_documento__count')
        

