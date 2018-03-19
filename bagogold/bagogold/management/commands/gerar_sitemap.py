# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from bagogold.bagogold.utils.sitemap import gerar_sitemap

class Command(BaseCommand):
    help = 'Gerar sitemap'

    def handle(self, *args, **options):
        gerar_sitemap()

