# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo, HistoricoTitulo,\
    ValorDiarioTitulo, OperacaoTitulo
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'TEMPORÁRIO unifica títulos do TD com data de validade e tipo iguais'

    def handle(self, *args, **options):
        nomes_oficiais = [Titulo.TIPO_OFICIAL_LETRA_TESOURO, Titulo.TIPO_OFICIAL_SELIC, Titulo.TIPO_OFICIAL_IPCA, Titulo.TIPO_OFICIAL_IPCA_COM_JUROS, Titulo.TIPO_OFICIAL_PREFIXADO_COM_JUROS, Titulo.TIPO_OFICIAL_IGPM]
        for lista_nomes_tipo in [Titulo.TIPO_LETRA_TESOURO, Titulo.TIPO_SELIC, Titulo.TIPO_IPCA, Titulo.TIPO_IPCA_COM_JUROS, Titulo.TIPO_PREFIXADO_COM_JUROS, Titulo.TIPO_IGPM]:
            titulos = Titulo.objects.filter(tipo__in=lista_nomes_tipo).order_by('data_vencimento')
            for titulo in titulos.filter(tipo__in=nomes_oficiais):
                for titulo_comparar in titulos.filter(data_vencimento__gte=titulo.data_vencimento).exclude(tipo__in=nomes_oficiais):
                    if titulo_comparar.data_vencimento > titulo.data_vencimento:
#                         print titulo.tipo, titulo.data_vencimento, titulo_comparar.tipo, titulo_comparar.data_vencimento
                        break
                    elif titulo_comparar.data_vencimento == titulo.data_vencimento:
                        print titulo_comparar, titulo, u'são iguais'
                        historico_titulo = HistoricoTitulo.objects.filter(titulo=titulo).order_by('data').values('data', 'preco_compra', 'taxa_compra', 'preco_venda', 'taxa_venda')
                        historico_titulo_comparar = HistoricoTitulo.objects.filter(titulo=titulo_comparar).order_by('data').values('data', 'preco_compra', 'taxa_compra', 'preco_venda', 'taxa_venda')
                        problema_na_comparacao = False
                        for data in historico_titulo:
                            if data in historico_titulo_comparar:
                                pass
                            else:
                                if historico_titulo_comparar.filter(data=data['data']).exists():
                                    print 'DEU RUIM DIA', data.data
                                    problema_na_comparacao = True
                                    break
                        if not problema_na_comparacao:
                            try:
                                with transaction.atomic():
                                    ValorDiarioTitulo.objects.filter(titulo=titulo_comparar).delete()
                                    operacao_count = 0
                                    for operacao in OperacaoTitulo.objects.filter(titulo=titulo_comparar):
                                        operacao.titulo = titulo
                                        operacao.save()
                                        operacao_count += 1
                                    historico_alterado_count = 0
                                    historico_apagado_count = 0
                                    for historico in historico_titulo_comparar:
                                        if historico in historico_titulo:
                                            HistoricoTitulo.objects.filter(titulo=titulo_comparar, data=historico['data']).delete()
                                            historico_apagado_count += 1
                                        else:
                                            historico_base = HistoricoTitulo.objects.filter(titulo=titulo_comparar, data=historico['data'])
                                            historico_base.titulo = titulo
                                            historico_base.save()
                                            historico_alterado_count += 1
                                    print 'apagou', titulo_comparar, 'alterou operacoes:', operacao_count, 'alterou/deletou historicos', historico_alterado_count, historico_apagado_count
                                    raise ValueError('deu erro aqui')
                            except Exception as e:
                                print e