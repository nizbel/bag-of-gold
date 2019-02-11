# -*- encoding: utf-8 -*-
from bagogold import settings
from django.core.management.base import BaseCommand
from os import walk
import re

class Command(BaseCommand):
    help = 'Minifica HTMLs na pasta templates'

    def handle(self, *args, **options):
        arqs = []
        for (dirpath, _, arq_nomes) in walk(settings.PROJECT_ROOT + '/templates'):
            arqs.extend(['%s/%s' % (dirpath, arq_nome) for arq_nome in arq_nomes if arq_nome[-4:] == 'html'])
            
        for arq_nome in arqs:
            with open(arq_nome, 'r+') as arquivo:
                text = arquivo.read()
                # Retirar comentários do javascript
                text = re.sub('\/\*.*?\*\/', '', re.sub('[^:]\/\/.*\n', '\n', text), flags=re.DOTALL)
                # Minificar HTML
                text = re.sub('>\s+<', '> <', re.sub('\n\s+', ' ', re.sub('<!--[^\[\]]+?-->', '', text)))
                arquivo.seek(0)
                arquivo.write(text)
                arquivo.truncate()
        
#         print u'%s arquivo(s) minificados' % (len(arqs))