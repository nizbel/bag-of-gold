# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys
import time

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import connection
from django.template.loader import render_to_string

from bagogold import settings
from bagogold.bagogold.management.commands.apagar_backups_repetidos import \
    apagar_backups_repetidos
from conf.conf import DROPBOX_OAUTH2_TOKEN, DROPBOX_ROOT_PATH
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode


TABELAS_SEM_CONTEUDO = ['bagogold_valordiarioacao', 'fii_valordiariofii', 'tesouro_direto_valordiariotitulo', 'criptomoeda_valordiariocriptomoeda', 
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
        pattern = re.compile('backup-\d+-\d+-\d+-\d+')

        for (_, _, nomes_arquivo) in os.walk(DROPBOX_ROOT_PATH):
            for nome_arquivo in [nome for nome in nomes_arquivo if pattern.match(nome)]:
                backup(nome_arquivo)
                
#         arquivo = file(arquivo_dump, 'w+')
#         arquivo.write('#!/bin/sh\n')
#         arquivo.write('mv /home/bagofgold/bagogold/backups/backup-*?-*?-*?-* /home/bagofgold/Dropbox/BKP\ BOG/')
#         arquivo.close()
# 
#         subprocess.call(['sh', arquivo_dump])
#         os.remove(arquivo_dump)
# 
#         # Rodar dropbox
#         subprocess.call(['/home/bagofgold/bin/dropbox.py', 'start'])
#         while 'Up to date' not in subprocess.check_output(['/home/bagofgold/bin/dropbox.py', 'status']):
#             time.sleep(5)
#         subprocess.call(['/home/bagofgold/bin/dropbox.py', 'stop'])

def buscar_tabelas_string():
    cursor = connection.cursor()
    lista_tabelas = connection.introspection.get_table_list(cursor)
    lista_tabelas = [tabela.name for tabela in lista_tabelas if tabela.type == 't']
    str_lista = ['--table "public.%s"' % (tabela) for tabela in sorted(lista_tabelas)]
    str_lista.extend(['--exclude-table-data "public.%s"' % (tabela) for tabela in TABELAS_SEM_CONTEUDO])
    str_lista = ' '.join(str_lista)
    return str_lista

def backup(file_name):
    """Envia para o Dropbox"""
    dbx = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)
    file_path = DROPBOX_ROOT_PATH + file_name
    
    f = open(file_path)
    file_size = os.path.getsize(file_path)
    
    CHUNK_SIZE = 4 * 1024 * 1024
    
    try:
        if file_size <= CHUNK_SIZE:
        
            print dbx.files_upload(f.read(), '/' + file_path, mode=WriteMode('overwrite'))
        
        else:
        
            upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=f.tell())
            commit = dropbox.files.CommitInfo(path=('/' + file_path), autorename=True)
        
            while f.tell() < file_size:
                if ((file_size - f.tell()) <= CHUNK_SIZE):
                    print dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                    cursor,
                                                    commit)
                else:
                    dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = f.tell()
    
    except ApiError as err:
        # This checks for the specific error where a user doesn't have
        # enough Dropbox space quota to upload this file
        if (err.error.is_path() and
                err.error.get_path().reason.is_insufficient_space()):
            if settings.ENV == 'DEV':
                print err
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preparar backup', 'ERROR: Cannot back up; insufficient space.')
            return
        elif err.user_message_text:
            if settings.ENV == 'DEV':
                print err.user_message_text
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preparar backup', err.user_message_text)
            return
        else:
            if settings.ENV == 'DEV':
                print err
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Preparar backup', err)
            return
    
    
    f.close()
    # Apagar arquivo
    os.remove(file_path)