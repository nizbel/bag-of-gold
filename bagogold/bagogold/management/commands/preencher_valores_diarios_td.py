# -*- coding: utf-8 -*-
from bagogold.bagogold.testTD import buscar_valores_diarios
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Preenche valores diários para o Tesouro Direto'

    def handle(self, *args, **options):
        valores_diarios = buscar_valores_diarios()
        for valor_diario in valores_diarios:
            # Salva apenas valores que não estejam zerados na venda
            if valor_diario.preco_venda > 0:
                valor_diario.save()
