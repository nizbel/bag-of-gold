# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
from subprocess import check_output
import re
 
class BagofGoldConfig(AppConfig):
    name = 'bagogold.bagogold'
    verbose_name = "Bag of Gold"
    def ready(self):
        output = check_output(['hg', 'log'])
        prod = re.findall(r'^branch:\s+prod', output, flags=re.MULTILINE)
        current_version = '1.0.%s' % (len(prod) - 143)
        print 'Current Bag of Gold version: ' + current_version
        settings.CURRENT_VERSION = current_version