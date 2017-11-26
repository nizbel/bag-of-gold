# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import OperacaoFII, CheckpointProventosFII, \
    CheckpointFII
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

class Command(BaseCommand):
    help = 'TEMPORÁRIO Criar checkpoints de FII'

    def handle(self, *args, **options):
        CheckpointProventosFII.objects.all().delete()
        CheckpointFII.objects.all().delete()
        for operacao in OperacaoFII.objects.filter(quantidade__gt=0):
            post_save.send(OperacaoFII, instance=operacao, created=False)
        for checkpoint in CheckpointFII.objects.all().order_by('investidor', 'ano'):
            print checkpoint.investidor, checkpoint.ano, checkpoint.fii, checkpoint.quantidade, checkpoint.preco_medio
        for checkpoint in CheckpointProventosFII.objects.all().order_by('investidor', 'ano'):
            print 'Provento', checkpoint.investidor, checkpoint.ano, checkpoint.valor