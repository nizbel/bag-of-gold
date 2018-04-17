# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import LetraCredito as LetraCredito_old, \
    OperacaoLetraCredito as OperacaoLetraCredito_old, \
    HistoricoCarenciaLetraCredito as HistoricoCarenciaLetraCredito_old, \
    HistoricoPorcentagemLetraCredito as HistoricoPorcentagemLetraCredito_old, \
    OperacaoVendaLetraCredito as OperacaoVendaLetraCredito_old
from bagogold.lci_lca.models import LetraCredito, OperacaoLetraCredito, \
    HistoricoCarenciaLetraCredito, HistoricoPorcentagemLetraCredito, \
    OperacaoVendaLetraCredito
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'TEMPORÁRIO copia os modelos de LCI/LCA de dentro do app bagogold para os novos modelos'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                LetraCredito.objects.all().delete()
                OperacaoLetraCredito.objects.all().delete()
                OperacaoVendaLetraCredito.objects.all().delete()
                HistoricoCarenciaLetraCredito.objects.all().delete()
                HistoricoPorcentagemLetraCredito.objects.all().delete()
                
                for lci_lca in LetraCredito_old.objects.all().values():
                    print lci_lca
                    LetraCredito.objects.create(**lci_lca)
                    
                for operacao in OperacaoLetraCredito_old.objects.all().values():
                    print operacao
                    OperacaoLetraCredito.objects.create(**operacao)
                    
                for operacao_venda in OperacaoVendaLetraCredito_old.objects.all().values():
                    print operacao_venda
                    OperacaoVendaLetraCredito.objects.create(**operacao_venda)
                    
                for porcentagem in HistoricoPorcentagemLetraCredito_old.objects.all().values():
                    print porcentagem
                    HistoricoPorcentagemLetraCredito.objects.create(**porcentagem)
                    
                for carencia in HistoricoCarenciaLetraCredito_old.objects.all().values():
                    print carencia
                    HistoricoCarenciaLetraCredito.objects.create(**carencia)
        except Exception as e:
            print e
