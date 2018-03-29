# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class LetraCambioConfig(AppConfig):
    name = 'bagogold.lc'
    def ready(self):
        import signals