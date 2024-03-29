# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import os
from shutil import copyfile

from bagogold import settings
from bagogold.bagogold.utils import filetest
from bagogold.settings import ENV, CAMINHO_BACKUPS


class Command(BaseCommand):
    help = 'Apaga backups repetidos'

    def handle(self, *args, **options):
        apagar_backups_repetidos()
        
        
def apagar_backups_repetidos():
#     CAMINHO_BACKUPS = "%s/backups" % (settings.BASE_DIR)
    
    # Último backup para comparar com os novos
    ultimo_backup = None
    
    # Lista de arquivos a apagar
    backups_apagar = list()
    
    # Lista de nomes dos arquivos ordenados por data
    backups_ord = list()
    for backup in os.listdir(CAMINHO_BACKUPS):
        if backup.startswith('backup-'):
            backups_ord.append(backup)
        elif backup.startswith('ultimo_backup-'):
            ultimo_backup = backup
    
    # Verifica se há backups na pasta para apagar
    if len(backups_ord) == 0 and ultimo_backup == None:
        return
    
    # Ordenar
    backups_ord.sort(key=lambda x: x.split('-')[4] + x.split('-')[3] + x.split('-')[2] + x.split('-')[1])
        
    # Buscar último backup registrado
    if not os.path.isfile('/%s/%s' % (CAMINHO_BACKUPS, ultimo_backup)):
        ultimo_backup_temp = backups_ord.pop(0)
    else:
        ultimo_backup_temp = ultimo_backup
        
    # Remover da lista ordenada os que tiverem data anterior
    string_data_ult_backup = ultimo_backup_temp.split('-')[4] + ultimo_backup_temp.split('-')[3] + ultimo_backup_temp.split('-')[2] + ultimo_backup_temp.split('-')[1]
    chegou_na_data = (len(backups_ord) > 0)
    while (not chegou_na_data) and len(backups_ord) > 0:
        backup = backups_ord[0]
        string_data = backup.split('-')[4] + backup.split('-')[3] + backup.split('-')[2] + backup.split('-')[1]
        if string_data <= string_data_ult_backup:
            backups_ord.pop(0)
        else:
            chegou_na_data = True
    
    # Verificar quais são repetidos
    for backup in backups_ord:
#             print 'Verificando', backup
        backup_repetido = filetest.cmp('/%s/%s' % (CAMINHO_BACKUPS, ultimo_backup_temp), '/%s/%s' % (CAMINHO_BACKUPS, backup))
#             print 'É repetido?', backup_repetido
        if backup_repetido:
            backups_apagar.append(backup)
        else:
            ultimo_backup_temp = backup
    
    # Apagar arquivos
#         print backups_apagar
    for backup in backups_apagar:
        os.remove('/%s/%s' % (CAMINHO_BACKUPS, backup))

    if ultimo_backup == None:
        copyfile('/%s/%s' % (CAMINHO_BACKUPS, ultimo_backup_temp), '/%s/ultimo_%s' % (CAMINHO_BACKUPS, ultimo_backup_temp))
    elif ultimo_backup_temp != ultimo_backup:
        os.remove('/%s/%s' % (CAMINHO_BACKUPS, ultimo_backup))
        copyfile('/%s/%s' % (CAMINHO_BACKUPS, ultimo_backup_temp), '/%s/ultimo_%s' % (CAMINHO_BACKUPS, ultimo_backup_temp))