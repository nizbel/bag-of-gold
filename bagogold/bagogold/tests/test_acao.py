# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, Provento,\
    AtualizacaoSelicProvento
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic
from bagogold.bagogold.utils.acoes import verificar_tipo_acao
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from bagogold.bagogold.utils.taxas_indexacao import \
    calcular_valor_atualizado_com_taxas_selic
from decimal import Decimal
from django.db.models.aggregates import Count
from django.test import TestCase
import datetime

class VerificarTipoAcaoTestCase(TestCase):
    def test_verificar_tipo_acao(self):
        """Testar se os tipos de ações estão sendo convertidos corretamente"""
        self.assertEqual(verificar_tipo_acao('CMIG3'), 'ON')
        self.assertEqual(verificar_tipo_acao('CMIG4'), 'PN')
        self.assertEqual(verificar_tipo_acao('CMIG5'), 'PNA')
        self.assertEqual(verificar_tipo_acao('CMIG6'), 'PNB')
        self.assertEqual(verificar_tipo_acao('CMIG7'), 'PNC')
        self.assertEqual(verificar_tipo_acao('CMIG8'), 'PND')

class CalcularAtualizacaoProventoSelicTestCase(TestCase):
    def setUp(self):
        empresa = Empresa.objects.create(nome='BB', nome_pregao='BBAS')
        acao = Acao.objects.create(ticker='BBAS3', empresa=empresa)
        provento_1 = Provento.objects.create(data_ex=datetime.date(2017, 3, 2), data_pagamento=datetime.date(2017, 3, 10), acao=acao,
                                           valor_unitario=Decimal('0.13676821544'), tipo_provento='J', oficial_bovespa=True)
        
        provento_2 = Provento.objects.create(data_ex=datetime.date(2017, 3, 2), data_pagamento=datetime.date(2017, 3, 10), acao=acao,
                                           valor_unitario=Decimal('0.02531542157'), tipo_provento='J', oficial_bovespa=True)
        
        data = datetime.date(2016, 6, 1)
        while data < datetime.date(2017, 3, 10):
            # Testar se é a segunda antes do carnaval, também não há taxa selic para essa data
            if data.weekday() < 5 and not verificar_feriado_bovespa(data) and not data == datetime.date(2017, 2, 27):
                if data < datetime.date(2016, 12, 1):
                    taxa = Decimal('1.00052531')
                elif data < datetime.date(2017, 1, 12):
                    taxa = Decimal('1.00050788')
                elif data < datetime.date(2017, 2, 23):
                    taxa = Decimal('1.00048159')
                else:
                    taxa = Decimal('1.00045513')
                HistoricoTaxaSelic.objects.create(data=data, taxa_diaria=taxa)
            data += datetime.timedelta(days=1)
        
    def test_verificar_valor_rendimentos(self):
        """Verifica se os valores alcançados são iguais aos pegos na bovespa"""
        # Provento 1 deve ser próximo a 0,00319717853
        provento = Provento.objects.get(valor_unitario__gt=Decimal('0.1'))
        atualizacao = AtualizacaoSelicProvento(provento=provento)
        atualizacao.data_inicio = datetime.date(2016, 6, 30)
        atualizacao.data_fim = datetime.date(2016, 8, 30)
        historico_selic = HistoricoTaxaSelic.objects.filter(data__range=[atualizacao.data_inicio, atualizacao.data_fim]).values('taxa_diaria').annotate(qtd_dias=Count('taxa_diaria'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_selic:
            taxas_dos_dias[taxa_quantidade['taxa_diaria']] = taxa_quantidade['qtd_dias']
        
        atualizacao.valor_rendimento = calcular_valor_atualizado_com_taxas_selic(taxas_dos_dias, provento.valor_unitario) - atualizacao.provento.valor_unitario
        
        self.assertAlmostEqual(atualizacao.valor_rendimento, Decimal('0.00319717853'), delta=Decimal('0.00000000001'))
        
        # Provento 2 deve ser próximo a 0,00059183169
        provento = Provento.objects.get(valor_unitario__lt=Decimal('0.1'))
        atualizacao = AtualizacaoSelicProvento(provento=provento)
        atualizacao.data_inicio = datetime.date(2016, 12, 30)
        atualizacao.data_fim = datetime.date(2017, 3, 9)
        historico_selic = HistoricoTaxaSelic.objects.filter(data__range=[atualizacao.data_inicio, atualizacao.data_fim]).values('taxa_diaria').annotate(qtd_dias=Count('taxa_diaria'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_selic:
            taxas_dos_dias[taxa_quantidade['taxa_diaria']] = taxa_quantidade['qtd_dias']
        
        atualizacao.valor_rendimento = calcular_valor_atualizado_com_taxas_selic(taxas_dos_dias, provento.valor_unitario) - atualizacao.provento.valor_unitario
        
        self.assertAlmostEqual(atualizacao.valor_rendimento, Decimal('0.00059183169'), delta=Decimal('0.00000000001'))