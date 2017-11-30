# -*- coding: utf-8 -*-
from bagogold import settings
from django.core.management.base import BaseCommand
from django.db import connection
import re
import subprocess

TABELAS_SEM_BACKUP = ['bagogold_valordiarioacao', 'bagogold_valordiariofii', 'bagogold_valordiariotitulo', 'criptomoeda_valordiariocriptomoeda', 
                      'django_session']

class Command(BaseCommand):
    help = 'Lista tabelas para backup'

    def handle(self, *args, **options):
        str_tabelas = buscar_tabelas_string()

        # Testar ambiente
        if settings.ENV == 'DEV':
            arquivo_dump = 'db_dump.sh'
        elif settings.ENV == 'PROD':
            arquivo_dump = 'db_prod_dump.sh'
        # Alterar db_dump.sh correspondente
        arquivo = file(arquivo_dump, 'r+')
        conteudo = arquivo.read()

        novo_conteudo = re.sub('--table.*public\.[^\s"]+"', str_tabelas, conteudo, 1)  
        arquivo.seek(0)
        arquivo.truncate()
        arquivo.write(novo_conteudo)
        
        arquivo.close()
        
        # Verificar se é possível chamar o db_dump por subprocess
        subprocess.call(['sh', '%s/%s' % (settings.BASE_DIR, arquivo_dump)])

def buscar_tabelas_string():
    cursor = connection.cursor()
    lista_tabelas = connection.introspection.get_table_list(cursor)
    lista_tabelas = [tabela.name for tabela in lista_tabelas if tabela.type == 't' and tabela.name not in TABELAS_SEM_BACKUP]
    str_lista = ['--table "public.%s"' % (tabela) for tabela in sorted(lista_tabelas)]
    str_lista = ' '.join(str_lista)
    return str_lista