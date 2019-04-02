# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
from subprocess import check_output
import os
 
class BagofGoldConfig(AppConfig):
    name = 'bagogold.bagogold'
    verbose_name = "Bag of Gold"
    def ready(self):
#         if settings.ENV == 'PROD':
#             origWD = os.getcwd()
#             os.chdir(settings.PROD_HOME)
#         else:
#             os.chdir('/home/nizbel/bagogold')
#         output = check_output(['hg', 'log', '-b', 'prod', '--template', '.'])
#         if settings.ENV == 'PROD':
#             os.chdir(origWD)
#         current_version = '1.0.%s' % (len(output) - 150)
#         if settings.ENV == 'DEV':
#             print 'Current Bag of Gold version: ' + current_version
        try:
            with open('version', 'r') as arq_versao:
                versao_atual = arq_versao.read().strip()
                settings.CURRENT_VERSION = versao_atual
        except:
            settings.CURRENT_VERSION = '1.0.0'
        
        # Carregar sinais
        import bagogold.bagogold.signals