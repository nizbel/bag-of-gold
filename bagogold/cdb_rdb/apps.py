# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class CDB_RDBConfig(AppConfig):
    name = 'bagogold.cdb_rdb'
    def ready(self):
        import signals