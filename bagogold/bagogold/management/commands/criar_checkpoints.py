# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import OperacaoFII, CheckpointProventosFII, \
    CheckpointFII
from bagogold.bagogold.models.investidores import Investidor
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

class Command(BaseCommand):
    help = 'TEMPORÁRIO Criar checkpoints '

    def handle(self, *args, **options):
        CheckpointProventosFII.objects.all().delete()
        CheckpointFII.objects.all().delete()
        for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.all().order_by('investidor').distinct('investidor')):
            primeira_operacao = OperacaoFII.objects.filter(investidor=investidor)[0]
            post_save.send(OperacaoFII, instance=primeira_operacao, created=False)
            print investidor
            for checkpoint in CheckpointFII.objects.filter(investidor=investidor).order_by('ano'):
                print checkpoint.ano, checkpoint.quantidade, checkpoint.preco_medio
            for checkpoint in CheckpointProventosFII.objects.filter(investidor=investidor).order_by('ano'):
                print 'Provento', checkpoint.ano, checkpoint.valor