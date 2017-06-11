# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fundo_investimento import \
    OperacaoFundoInvestimento
from bagogold.fundo_investimento.models import \
    OperacaoFundoInvestimento as NovaOperacaoFundo, FundoInvestimento
from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = 'TEMPORÁRIO migra operações de fundo de investimento para o novo formato'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                for operacao in OperacaoFundoInvestimento.objects.all():
                    nova_operacao = NovaOperacaoFundo(data=operacao.data, tipo_operacao=operacao.tipo_operacao, valor=operacao.valor, quantidade=operacao.quantidade,
                                                      investidor=operacao.investidor, fundo_investimento=FundoInvestimento.objects.get(nome='CLARITAS INSTITUCIONAL FUNDO DE INVESTIMENTO MULTIMERCADO'))
                    print nova_operacao
        except:
            pass
