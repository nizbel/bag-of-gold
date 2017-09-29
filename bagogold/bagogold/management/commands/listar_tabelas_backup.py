# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import connection

TABELAS_SEM_BACKUP = ['bagogold_valordiarioacao', 'bagogold_valordiariofii', 'bagogold_valordiariotitulo', 'criptomoeda_valordiariocriptomoeda', 'django_session']

class Command(BaseCommand):
    help = 'Lista tabelas para backup'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        lista_tabelas = connection.introspection.get_table_list(cursor)
        lista_tabelas = [tabela.name for tabela in lista_tabelas if tabela.type == 't' and tabela.name not in TABELAS_SEM_BACKUP]
        str_lista = ['--table "public.%s"' % (tabela) for tabela in sorted(lista_tabelas)]
        str_lista = ' '.join(str_lista)
        print str_lista