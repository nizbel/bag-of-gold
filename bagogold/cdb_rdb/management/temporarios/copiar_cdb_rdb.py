# -*- coding: utf-8 -*-
from bagogold.cdb_rdb.models import CDB_RDB, OperacaoCDB_RDB,\
    HistoricoCarenciaCDB_RDB, HistoricoVencimentoCDB_RDB,\
    HistoricoPorcentagemCDB_RDB, OperacaoVendaCDB_RDB
from bagogold.bagogold.models.cdb_rdb import CDB_RDB as CDB_RDB_old,\
    OperacaoCDB_RDB as OperacaoCDB_RDB_old,\
    HistoricoCarenciaCDB_RDB as HistoricoCarenciaCDB_RDB_old,\
    HistoricoPorcentagemCDB_RDB as HistoricoPorcentagemCDB_RDB_old,\
    OperacaoVendaCDB_RDB as OperacaoVendaCDB_RDB_old
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'TEMPORÁRIO copia os modelos de CDB/RDB de dentro do app bagogold para os novos modelos'

    def handle(self, *args, **options):
        CDB_RDB.objects.all().delete()
        OperacaoCDB_RDB.objects.all().delete()
        OperacaoVendaCDB_RDB.objects.all().delete()
        HistoricoCarenciaCDB_RDB.objects.all().delete()
        HistoricoVencimentoCDB_RDB.objects.all().delete()
        HistoricoPorcentagemCDB_RDB.objects.all().delete()
        
        for cdb_rdb in CDB_RDB_old.objects.all().values():
            print cdb_rdb
            CDB_RDB.objects.create(**cdb_rdb)
            
        for operacao in OperacaoCDB_RDB_old.objects.all().values():
            print operacao
            OperacaoCDB_RDB.objects.create(**operacao)
            
        for operacao_venda in OperacaoVendaCDB_RDB_old.objects.all().values():
            print operacao_venda
            OperacaoVendaCDB_RDB.objects.create(**operacao_venda)
            
        for porcentagem in HistoricoPorcentagemCDB_RDB_old.objects.all().values():
            print porcentagem
            HistoricoPorcentagemCDB_RDB.objects.create(**porcentagem)
            
        for carencia in HistoricoCarenciaCDB_RDB_old.objects.all().values():
            print carencia
            HistoricoCarenciaCDB_RDB.objects.create(**carencia)
            
        # Vencimento não pode ser copiado diretamente pois é um modelo novo
        for carencia in HistoricoCarenciaCDB_RDB_old.objects.all():
            print carencia.carencia, carencia.data, carencia.cdb_rdb.id
            HistoricoVencimentoCDB_RDB.objects.create(vencimento=carencia.carencia, data=carencia.data, cdb_rdb=CDB_RDB.objects.get(id=carencia.cdb_rdb.id))
        