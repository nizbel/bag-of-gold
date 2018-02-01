# -*- encoding: utf-8 -*-
from bagogold import settings
from django.core.management.base import BaseCommand

STATIC_FOLDER = settings.STATICFILES_DIRS[0]
CSS_BASE_FOLDER = STATIC_FOLDER + '/assets/global/css'
CSS_LAYOUT_FOLDER = STATIC_FOLDER + '/assets/layouts/layout3/css'
CSS_ICONS_FOLDER = ''

class Command(BaseCommand):
    help = 'Gera CSS definitivos'

    def handle(self, *args, **options):
        if settings.ENV != 'DEV':
            print u'Comando deve ser usado apenas para DEV'
            
        # CSS base
        texto = ''
        with open(CSS_BASE_FOLDER + '/components-md.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_BASE_FOLDER + '/plugins-md.min.css', 'r') as arquivo:
            texto += arquivo.read()

        with open(CSS_BASE_FOLDER + '/base.min.css', 'w') as arquivo_final:
            arquivo_final.write(texto)
        
        # CSS de layout
        texto = ''
        with open(CSS_LAYOUT_FOLDER + '/layout.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_LAYOUT_FOLDER + '/themes/default.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_LAYOUT_FOLDER + '/custom.min.css', 'r') as arquivo:
            texto += arquivo.read()

        with open(CSS_LAYOUT_FOLDER + '/layout-def.min.css', 'w') as arquivo_final:
            arquivo_final.write(texto)