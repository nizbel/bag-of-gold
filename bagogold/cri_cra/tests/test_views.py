# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI,\
    HistoricoTaxaSelic, HistoricoIPCA
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from bagogold.cri_cra.models.cri_cra import CRI_CRA, OperacaoCRI_CRA


class PainelTestCase(TestCase):
    def setUp(self):
        # Criar usuário sem operações
        User.objects.create_user(username='test', password='test')
        
        # Criar usuário com operações
        nizbel = User.objects.create_user(username='nizbel', password='nizbel')
        
        # Criar usuário com operações todas vendidas
        vendido = User.objects.create_user(username='vendido', password='vendido')
        
        # Criar operações para os usuários
        cri_cra1 = CRI_CRA.objects.create(investidor=nizbel.investidor, nome='CRI', tipo_indexacao=CRI_CRA.TIPO_INDEXACAO_DI, porcentagem=98,
                                          data_emissao=datetime.date(2018, 2, 2), valor_emissao=1000, data_inicio_rendimento=datetime.date(2018, 2, 6),
                                          data_vencimento=datetime.date(2020, 2, 2))
        OperacaoCRI_CRA.objects.create(cri_cra=cri_cra1, quantidade=3, preco_unitario=Decimal(1000), data=datetime.date(2018, 5, 15), 
                                       tipo_operacao='C', taxa=0)
        
        cri_cra2 = CRI_CRA.objects.create(investidor=vendido.investidor, nome='CRA', tipo_indexacao=CRI_CRA.TIPO_INDEXACAO_DI, porcentagem=100,
                                          data_emissao=datetime.date(2018, 2, 2), valor_emissao=1000, data_inicio_rendimento=datetime.date(2018, 2, 6),
                                          data_vencimento=datetime.date(2020, 2, 2))
        OperacaoCRI_CRA.objects.create(cri_cra=cri_cra2, quantidade=3, preco_unitario=Decimal(1000), data=datetime.date(2018, 5, 15), 
                                       tipo_operacao='C', taxa=0)
        OperacaoCRI_CRA.objects.create(cri_cra=cri_cra2, quantidade=3, preco_unitario=Decimal(1100), data=datetime.date(2018, 5, 25), 
                                       tipo_operacao='V', taxa=0)
        
        # Histórico de DI
        date_list = [datetime.date(2018, 5, 20) - datetime.timedelta(days=x) for x in range(0, (datetime.date(2018, 5, 20) - datetime.date(2016, 10, 14)).days+1)]
        date_list = [data for data in date_list if data.weekday() < 5 and not verificar_feriado_bovespa(data)]
        
        for data in date_list:
            if data >= datetime.date(2016, 10, 20):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(13.88))
                HistoricoTaxaSelic.objects.create(data=data, taxa_diaria=Decimal('1.00001'))
                HistoricoIPCA.objects.create(data_inicio=data, data_fim=data, valor=Decimal('1.24'))
            else:
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal(14.13))
                HistoricoTaxaSelic.objects.create(data=data, taxa_diaria=Decimal('1.00001'))
                HistoricoIPCA.objects.create(data_inicio=data, data_fim=data, valor=Decimal('1.24'))
        
    def test_usuario_deslogado(self):
        """Testa usuário deslogado"""
        response = self.client.get(reverse('cri_cra:painel_cri_cra'))
        
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset({'cri_cra': {}, 'dados': {'total_rendimento_ate_vencimento': Decimal('0'), 
                                                                    'total_valor_atual': Decimal('0'), 'total_investido': Decimal('0')}}, 
                                                                    response.context_data)
        
    def test_usuario_logado_sem_operacoes(self):
        """Testa usuário logado sem operações"""
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('cri_cra:painel_cri_cra'))
        
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset({'cri_cra': {}, 'dados': {'total_rendimento_ate_vencimento': Decimal('0'), 
                                                                    'total_valor_atual': Decimal('0'), 'total_investido': Decimal('0')}}, 
                                                                    response.context_data)
        
    # TODO Verificar valores
#     def test_usuario_logado_com_operacoes(self):
#         """Testa usuário logado com operações"""
#         self.client.login(username='nizbel', password='nizbel')
#         response = self.client.get(reverse('cri_cra:painel_cri_cra'))
#          
#         self.assertEqual(response.status_code, 200)
#         self.assertDictContainsSubset({'cri_cra': {}, 'dados': {}}, response.context_data)
        
    def test_usuario_logado_com_operacoes_vendidas(self):
        """Testa usuário logado com operações vendidas"""
        self.client.login(username='vendido', password='vendido')
        response = self.client.get(reverse('cri_cra:painel_cri_cra'))
        
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset({'cri_cra': {}, 'dados': {'total_rendimento_ate_vencimento': Decimal('0'), 
                                                                    'total_valor_atual': Decimal('0'), 'total_investido': Decimal('0')}}, 
                                                                    response.context_data)