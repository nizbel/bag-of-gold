# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand

from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo,\
    verifica_se_dia_util
from bagogold.tesouro_direto.models import OperacaoTitulo, Titulo,\
    HistoricoTitulo


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
            datas_avaliacao = [datetime.date(ano, 1, 1) for ano in range(operacao.data.year, operacao.titulo.data_vencimento.year + 1)] \
                                + [datetime.date(ano, 7, 1) for ano in range(operacao.data.year, operacao.titulo.data_vencimento.year + 1)]
            datas_avaliacao.sort()
            
            for data_avaliacao in datas_avaliacao:
                # Verificar se data de avaliação é dia útil, se não buscar próximo dia
                while not verifica_se_dia_util(data_avaliacao):
                    data_avaliacao = data_avaliacao + datetime.timedelta(days=1)
                
                if data_avaliacao <= operacao.data:
                    continue
                
                if data_avaliacao not in taxas_semestrais:
                    taxas_semestrais[data_avaliacao] = {}
                
                valor_na_data = HistoricoTitulo.objects.filter(titulo=operacao.titulo, data__lte=data_avaliacao)[0].preco_venda
                # Definir valores
                if data_avaliacao >= ultima_data_avaliacao_cust:
                    valor_custodia = valor_na_data * operacao.quantidade * (Decimal('1.005') ** \
                        (Decimal(qtd_dias_uteis_no_periodo(ultima_data_avaliacao_cust, data_avaliacao + datetime.timedelta(days=1)))/252) - 1)
                    ultima_data_avaliacao_cust = data_avaliacao + datetime.timedelta(days=1)
                else:
                    valor_custodia = 0
                valor_bvmf = valor_na_data * operacao.quantidade * (Decimal('1.003') ** \
                        (Decimal(qtd_dias_uteis_no_periodo(ultima_data_avaliacao_bvmf, data_avaliacao + datetime.timedelta(days=1)))/252) - 1)
                ultima_data_avaliacao_bvmf = data_avaliacao + datetime.timedelta(days=1)
                
                taxas_semestrais[data_avaliacao][operacao.id] = (valor_custodia, valor_bvmf)
        
        total_pago = 0
        print 'Taxas semestrais:'
        for semestre in sorted(taxas_semestrais.keys()):
            print semestre, taxas_semestrais[semestre]
            print sum([custodia for (custodia, _) in taxas_semestrais[semestre].values()]), \
            sum([bvmf for (_, bvmf) in taxas_semestrais[semestre].values()])
            total_pago += sum([custodia for (custodia, _) in taxas_semestrais[semestre].values()]) \
                + sum([bvmf for (_, bvmf) in taxas_semestrais[semestre].values()])
            if total_pago > 10:
                print 'Pago', total_pago
                total_pago = 0
        print 'Qtd. total:', qtd_total
        print 'Lucro total:', lucro_total