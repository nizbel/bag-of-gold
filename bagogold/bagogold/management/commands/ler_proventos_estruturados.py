# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import ProventoFII, FII
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    ProventoFIIDescritoDocumentoBovespa, ProventoFIIDocumento
from bagogold.bagogold.utils.gerador_proventos import \
    ler_provento_estruturado_fii
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Lê proventos estruturados e cria descrição e provento'

    def handle(self, *args, **options):
        # Limpar no início
        documento_ids = DocumentoProventoBovespa.objects.filter(tipo='F', tipo_documento=DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO).values_list('id', flat=True)
        lista_ids_prov = list(ProventoFIIDocumento.objects.filter(documento__id__in=documento_ids).values_list('provento', flat=True))
        lista_ids_desc_prov = list(ProventoFIIDocumento.objects.filter(documento__id__in=documento_ids).values_list('descricao_provento', flat=True))
        for prov_doc in ProventoFIIDocumento.objects.filter(documento__id__in=documento_ids):
            prov_doc.delete()
        for prov in ProventoFII.objects.filter(id__in=lista_ids_prov):
            prov.delete()
        for desc_prov in ProventoFIIDescritoDocumentoBovespa.objects.filter(id__in=lista_ids_desc_prov):
            desc_prov.delete()
        
        print DocumentoProventoBovespa.objects.filter(tipo='F', tipo_documento=DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO).count()
        erros = list()
        for documento in DocumentoProventoBovespa.objects.filter(tipo='F', tipo_documento=DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO):
            try:
                ler_provento_estruturado_fii(documento)
                proventos_documento = ProventoFIIDocumento.objects.filter(documento=documento)
            except:
                erros.append(documento)
        print 'erros:', erros
        qtd_sem_proventos = 0
        for documento in DocumentoProventoBovespa.objects.filter(tipo='F', tipo_documento=DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO):
            if not ProventoFIIDocumento.objects.filter(documento=documento).exists():
                qtd_sem_proventos += 1
        print 'Qtd sem proventos', qtd_sem_proventos