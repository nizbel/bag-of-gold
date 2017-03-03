# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa
from bagogold.bagogold.utils.gerador_proventos import \
    ler_provento_estruturado_fii
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Lê proventos estruturados e cria descrição e provento'

    def handle(self, *args, **options):
        for documento in DocumentoProventoBovespa.objects.filter(protocolo='8679', tipo_documento=DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO):
            print documento
            ler_provento_estruturado_fii(documento)

