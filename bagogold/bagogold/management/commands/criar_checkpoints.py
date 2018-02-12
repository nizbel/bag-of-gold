# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import CheckpointDivisaoFII, \
    CheckpointDivisaoProventosFII, DivisaoOperacaoFII
from bagogold.fii.models import OperacaoFII, CheckpointProventosFII, \
    CheckpointFII
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

class Command(BaseCommand):
    help = 'TEMPORÁRIO Criar checkpoints de FII'

    def handle(self, *args, **options):
        CheckpointProventosFII.objects.all().delete()
        CheckpointFII.objects.all().delete()
        for operacao in OperacaoFII.objects.all().order_by('data'):
            post_save.send(OperacaoFII, instance=operacao, created=False)
        for checkpoint in CheckpointFII.objects.all().order_by('investidor', 'ano'):
            print checkpoint.investidor, checkpoint.ano, checkpoint.fii, checkpoint.quantidade, checkpoint.preco_medio
        for checkpoint in CheckpointProventosFII.objects.all().order_by('investidor', 'ano'):
            print 'Provento', checkpoint.investidor, checkpoint.ano, checkpoint.valor
        
        # Divisões
        CheckpointDivisaoFII.objects.all().delete()
        CheckpointDivisaoProventosFII.objects.all().delete()
        for operacao_divisao in DivisaoOperacaoFII.objects.all().order_by('operacao__data'):
            post_save.send(DivisaoOperacaoFII, instance=operacao_divisao, created=False)
        for checkpoint in CheckpointDivisaoFII.objects.all().order_by('divisao__investidor', 'ano'):
            print checkpoint.divisao.investidor, checkpoint.divisao, checkpoint.ano, checkpoint.fii, checkpoint.quantidade, checkpoint.preco_medio
        for checkpoint in CheckpointDivisaoProventosFII.objects.all().order_by('divisao__investidor', 'ano'):
            print 'Provento', checkpoint.divisao.investidor, checkpoint.divisao, checkpoint.ano, checkpoint.valor
            
