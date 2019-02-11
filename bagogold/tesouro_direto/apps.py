# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class TesouroDiretoConfig(AppConfig):
    name = 'bagogold.tesouro_direto'
    def ready(self):
        import signals