# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class LCI_LCAConfig(AppConfig):
    name = 'bagogold.lci_lca'
    def ready(self):
        import signals