# -*- coding: utf-8 -*-
from bagogold.fundo_investimento.models import FundoInvestimento
from bagogold.fundo_investimento.utils import \
    criar_slug_fundo_investimento_valido
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'TEMPORÁRIO Preenche slugs para os fundos de investimento'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Reiniciar slugs
                for fundo in FundoInvestimento.objects.all():
                    fundo.slug = str(fundo.id)
                    fundo.save()

                # Preencher slugs
                for fundo in FundoInvestimento.objects.all():
                    fundo.slug = criar_slug_fundo_investimento_valido(fundo.nome)
                    fundo.save()
        except:
            print 'ERRO'