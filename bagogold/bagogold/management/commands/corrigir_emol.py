# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao
from bagogold.bagogold.models.fii import OperacaoFII
from decimal import Decimal, ROUND_FLOOR
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Corrige os valores de emolumentos calculados erroneamente'
    
    def add_arguments(self, parser):
        parser.add_argument('save', type=int)
        
    def handle(self, *args, **options):
        for operacao_acao in OperacaoAcao.objects.filter(destinacao='B', emolumentos__gt=0):
            emolumentos_dt = (operacao_acao.preco_unitario * operacao_acao.quantidade * Decimal('0.025') / 100).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
            emolumentos_comum = (operacao_acao.preco_unitario * operacao_acao.quantidade * Decimal('0.0325') / 100).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
            if operacao_acao.emolumentos == emolumentos_dt:
                print 'DT', operacao_acao, operacao_acao.emolumentos
                if not options['save'] == 0:
                    operacao_acao.emolumentos = emolumentos_comum
                    operacao_acao.save()
            elif operacao_acao.emolumentos == emolumentos_comum:
                print 'Comum', operacao_acao, operacao_acao.emolumentos
            else:
                print 'Nao bateu', operacao_acao, operacao_acao.emolumentos, emolumentos_comum, emolumentos_dt
        for operacao_fii in OperacaoFII.objects.all():
            emolumentos_dt = (operacao_fii.preco_unitario * operacao_fii.quantidade * Decimal('0.025') / 100).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
            emolumentos_comum = (operacao_fii.preco_unitario * operacao_fii.quantidade * Decimal('0.0325') / 100).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
            if operacao_fii.emolumentos == emolumentos_dt:
                print 'DT', operacao_fii, operacao_fii.emolumentos
                if not options['save'] == 0:
                    operacao_fii.emolumentos = emolumentos_comum
                    operacao_fii.save()
            elif operacao_fii.emolumentos == emolumentos_comum:
                print 'Comum', operacao_fii, operacao_fii.emolumentos
            else:
                print 'Nao bateu', operacao_fii, operacao_fii.emolumentos, emolumentos_comum, emolumentos_dt
