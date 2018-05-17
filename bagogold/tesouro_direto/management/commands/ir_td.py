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
        for operacao in OperacaoTitulo.objects.filter(titulo__tipo=Titulo.TIPO_OFICIAL_LETRA_TESOURO, titulo__data_vencimento__year=2017).order_by('data'):
            print operacao
            
            qtd_total += operacao.quantidade
            
            print 'custodia:', Decimal('0.005') * operacao.quantidade * operacao.preco_unitario, operacao.taxa_custodia
            print 'taxa bovespa:', Decimal('0.003') * operacao.quantidade * operacao.preco_unitario, operacao.taxa_bvmf
            
            lucro = operacao.quantidade * (operacao.titulo.valor_vencimento() - operacao.preco_unitario)
            lucro_total += lucro
            
            ultima_data_avaliacao_cust = operacao.data + datetime.timedelta(days=365)
            ultima_data_avaliacao_bvmf = operacao.data
            # Preencher primeiros dias úteis de janeiro e julho subsequentes
            for data_avaliacao in [datetime.date(ano, 1, 1) for ano in range(operacao.data.ano, operacao.titulo.data_vencimento.year + 1)] \
                                + [datetime.date(ano, 7, 1) for ano in range(operacao.data.ano, operacao.titulo.data_vencimento.year + 1)]:
                # Verificar se data de avaliação é dia útil, se não buscar próximo dia
                while not verificar_se_dia_util(data_avaliacao):
                    data_avaliacao = data_avaliacao + datetime.timedelta(days=1)
                
                if data_avaliacao not in taxas_semestrais:
                    taxas_semestrais[data_avaliacao] = {}
                
                # Definir valores
                if data_avaliacao >= ultima_data_avaliacao_cust:
                    valor_custodia = operacao.titulo.valor_na_data(data_avaliacao) * (Decimal('1.005') ** \
                        (Decimal(qtd_dias_uteis_no_periodo(ultima_data_avaliacao_cust, data_avaliacao + datetime.timedelta(days=1))/252) - 1)
                    ultima_data_avaliacao_cust = data_avaliacao + datetime.timedelta(days=1)
                else:
                    valor_custodia = 0
                valor_bvmf = operacao.titulo.valor_na_data(data_avaliacao) * (Decimal('1.003') ** \
                        (Decimal(qtd_dias_uteis_no_periodo(ultima_data_avaliacao_bvmf, data_avaliacao + datetime.timedelta(days=1))/252) - 1)
                ultima_data_avaliacao_bvmf = data_avaliacao + datetime.timedelta(days=1)
                
                taxas_semestrais[data_avaliacao][operacao.id] = (valor_custodia, valor_bvmf)
                
        print 'Taxas semestrais:', taxas_semestrais
        print 'Qtd. total:', qtd_total
        print 'Lucro total:', lucro_total