# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import ProventoFII
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'TEMPORÁRIO adiciona tipo de rendimento a proventos de FII que não o tenham definido'

    def handle(self, *args, **options):
        for provento in ProventoFII.objects.all():
            if provento.tipo_provento not in [tipo_provento for tipo_provento, _ in ProventoFII.ESCOLHAS_TIPO_PROVENTO_FII]:
                provento.tipo_provento = ProventoFII.TIPO_PROVENTO_RENDIMENTO
                provento.save()