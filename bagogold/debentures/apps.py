# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class DebenturesConfig(AppConfig):
    name = 'bagogold.debentures'
    def ready(self):
        import signals