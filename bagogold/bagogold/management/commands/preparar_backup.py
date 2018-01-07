# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.management.commands.apagar_backups_repetidos import \
    apagar_backups_repetidos
from django.core.management.base import BaseCommand
from django.db import connection
from django.template.loader import render_to_string
import os
import subprocess
import time

TABELAS_SEM_CONTEUDO = ['bagogold_valordiarioacao', 'bagogold_valordiariofii', 'bagogold_valordiariotitulo', 'criptomoeda_valordiariocriptomoeda', 
                      'django_session']

class Command(BaseCommand):
    help = 'Busca tabelas atuais na base e prepara backup'

    def handle(self, *args, **options):
        preparar_backup()
        
        
def preparar_backup():
    str_tabelas = buscar_tabelas_string()

    # Testar ambiente
    if settings.ENV == 'DEV':
        arquivo_dump = '%s/%s' % (settings.BASE_DIR, 'db_dump.sh')
        arquivo_base = 'db_dump.txt'
    elif settings.ENV == 'PROD':
        arquivo_dump = '%s/%s' % (settings.BASE_DIR, 'db_prod_dump.sh')
        arquivo_base = 'db_prod_dump.txt'

    # Alterar db_dump.sh correspondente
    arquivo = file(arquivo_dump, 'w+')

    arquivo.write(render_to_string(arquivo_base, {'tabelas': str_tabelas, 'nome_db': settings.DATABASES['default']['NAME']}))

    arquivo.close()

    # Verificar se é possível chamar o db_dump por subprocess
    subprocess.call(['sh', arquivo_dump])

    os.remove(arquivo_dump)

    # Apagar backups repetidos
    apagar_backups_repetidos()

    # Se produção, enviar backups para pasta do dropbox
    if settings.ENV == 'PROD':
        arquivo = file(arquivo_dump, 'w+')
        arquivo.write('#!/bin/sh\n')
        arquivo.write('mv /home/bagofgold/bagogold/backups/backup-*?-*?-*?-* /home/bagofgold/Dropbox/BKP\ BOG/')
        arquivo.close()

        subprocess.call(['sh', arquivo_dump])
        os.remove(arquivo_dump)

        # Rodar dropbox
        subprocess.call(['/home/bagofgold/bin/dropbox.py', 'start'])
        while 'Up to date' not in subprocess.check_output(['/home/bagofgold/bin/dropbox.py', 'status']):
            time.sleep(5)
        subprocess.call(['/home/bagofgold/bin/dropbox.py', 'stop'])

def buscar_tabelas_string():
    cursor = connection.cursor()
    lista_tabelas = connection.introspection.get_table_list(cursor)
    lista_tabelas = [tabela.name for tabela in lista_tabelas if tabela.type == 't']
    str_lista = ['--table "public.%s"' % (tabela) for tabela in sorted(lista_tabelas)]
    str_lista.extend(['--exclude-table-data "public.%s"' % (tabela) for tabela in TABELAS_SEM_CONTEUDO])
    str_lista = ' '.join(str_lista)
    return str_lista