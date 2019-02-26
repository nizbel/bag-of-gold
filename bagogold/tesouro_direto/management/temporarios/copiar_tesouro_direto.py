# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from django.db import transaction

from bagogold.bagogold.models.td import Titulo as Titulo_old, \
    OperacaoTitulo as OperacaoTitulo_old, HistoricoTitulo as HistoricoTitulo_old, \
    ValorDiarioTitulo as ValorDiarioTitulo_old
from bagogold.tesouro_direto.models import Titulo, OperacaoTitulo, \
    HistoricoTitulo, ValorDiarioTitulo


class Command(BaseCommand):
    help = 'TEMPORÁRIO copia os modelos de Tesouro Direto de dentro do app bagogold para os novos modelos'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                Titulo.objects.all().delete()
                OperacaoTitulo.objects.all().delete()
                HistoricoTitulo.objects.all().delete()
                ValorDiarioTitulo.objects.all().delete()
                
                for titulo in Titulo_old.objects.all().values():
                    print titulo
                    Titulo.objects.create(**titulo)
                    
                for operacao in OperacaoTitulo_old.objects.all().values():
                    print operacao
                    OperacaoTitulo.objects.create(**operacao)
                    
                for historico in HistoricoTitulo_old.objects.all().values():
                    print historico
                    HistoricoTitulo.objects.create(**historico)
                    
                for valor_diario in ValorDiarioTitulo_old.objects.all().values():
                    print valor_diario
                    ValorDiarioTitulo.objects.create(**valor_diario)
                    
        except Exception as e:
            print e
