# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento
from bagogold.bagogold.utils.gerador_proventos import \
    ler_provento_estruturado_fii
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Lê proventos estruturados e cria descrição e provento'

    def handle(self, *args, **options):
        for pendencia in PendenciaDocumentoProvento.objects.filter(documento__tipo='F', documento__tipo_documento=DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO):
            try:
                ler_provento_estruturado_fii(pendencia.documento)
            except:
                pass
