# -*- coding: utf-8 -*-
from subprocess import check_output

from django.core.management.base import BaseCommand

from bagogold import settings


class Command(BaseCommand):
    help = 'Define versão atual pelo Mercurial'

    def handle(self, *args, **options):
        output = check_output(['hg', 'log', '-b', 'prod', '--template', '.'])
        current_version = '1.0.%s' % (len(output) - 150)
        with open('version', 'w') as arq_versao:
            arq_versao.write(current_version)
