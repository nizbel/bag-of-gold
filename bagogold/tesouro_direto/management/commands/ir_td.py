# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from django.db import transaction

from bagogold.tesouro_direto.models import OperacaoTitulo, Titulo
from decimal import Decimal


class Command(BaseCommand):
    help = 'TEMPORÁRIO Testa valores para imposto de renda'

    def handle(self, *args, **options):
        qtd_total = 0
        lucro_total = 0
        taxas_semestrais = {}
        for operacao in OperacaoTitulo.objects.filter(titulo__tipo=Titulo.TIPO_OFICIAL_LETRA_TESOURO, titulo__data_vencimento__year=2017):
            print operacao
            
            qtd_total += operacao.quantidade
            
            print 'custodia:', Decimal('0.005') * operacao.quantidade * operacao.preco_unitario, operacao.taxa_custodia
            print 'taxa bovespa:', Decimal('0.003') * operacao.quantidade * operacao.preco_unitario, operacao.taxa_bvmf
            lucro = operacao.quantidade * (operacao.titulo.valor_vencimento() - operacao.preco_unitario)
            
            lucro_total += lucro
            
        print 'Qtd. total:', qtd_total
        print 'Lucro total:', lucro_total