# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, InvestidorRecusaDocumento, ProventoAcaoDocumento
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Busca proventos de ações na Bovespa'
    
    def handle(self, *args, **options):
        doc_com_recusa = InvestidorRecusaDocumento.objects.all().values_list('documento', flat=True)
        doc_com_provento = ProventoAcaoDocumento.objects.all().values_list('documento', flat=True)
        doc_pendentes = PendenciaDocumentoProvento.objects.filter(investidorresponsavelpendencia__isnull=True, tipo='L').values_list('documento', flat=True)
        for documento in DocumentoProventoBovespa.objects.filter(investidorleituradocumento__isnull=True, id__in=doc_pendentes, \
            tipo_documento__in=DocumentoProventoBovespa.TIPOS_DOCUMENTO_VALIDOS).exclude(id__in=doc_com_recusa).exclude(id__in=doc_com_provento):
            documento.delete()
