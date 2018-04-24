# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import CheckpointDivisaoCDB_RDB, \
    DivisaoOperacaoCDB_RDB
from bagogold.cdb_rdb.models import CheckpointCDB_RDB, OperacaoCDB_RDB
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

class Command(BaseCommand):
    help = 'TEMPORÁRIO Criar checkpoints de CDB/RDB'

    def handle(self, *args, **options):
        CheckpointCDB_RDB.objects.all().delete()
        for operacao in OperacaoCDB_RDB.objects.all().order_by('data'):
            post_save.send(OperacaoCDB_RDB, instance=operacao, created=False)
        for checkpoint in CheckpointCDB_RDB.objects.all().order_by('operacao__investidor', 'ano'):
            print checkpoint.operacao.investidor, checkpoint.ano, checkpoint.qtd_restante, checkpoint.qtd_atualizada
        
        # Divisões
        CheckpointDivisaoCDB_RDB.objects.all().delete()
        for operacao_divisao in DivisaoOperacaoCDB_RDB.objects.all().order_by('operacao__data'):
            post_save.send(DivisaoOperacaoCDB_RDB, instance=operacao_divisao, created=False)
        for checkpoint in CheckpointDivisaoCDB_RDB.objects.all().order_by('divisao_operacao__divisao__investidor', 'ano'):
            print checkpoint.divisao_operacao.operacao.investidor, checkpoint.divisao_operacao.divisao, checkpoint.ano, \
                checkpoint.qtd_restante, checkpoint.qtd_atualizada
            
