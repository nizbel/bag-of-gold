# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI, \
    HistoricoTaxaSelic, HistoricoIPCA
from bagogold.bagogold.utils.misc import verifica_se_dia_util
from bagogold.debentures.models import Debenture, OperacaoDebenture, \
    HistoricoValorDebenture


class DetalharDebentureTestCase (TestCase):
    @classmethod
    def setUpTestData(cls):
        # Usuário sem operações
        User.objects.create_user(username='nizbel', password='nizbel')
        
        # Usuário com operações
        tester = User.objects.create_user(username='tester', password='tester')
    
        # TODO Criar debenture
        cls.debenture = Debenture.objects.create(codigo='CMIG15', indice=Debenture.DI, porcentagem=100,
                                             data_emissao=datetime.date(2018, 1, 1), valor_emissao=1000,
                                             data_inicio_rendimento=datetime.date(datetime.date.today().year-1, 1, 3), 
                                             data_vencimento=datetime.date(datetime.date.today().year+2, 12, 31),
                                             incentivada=True, padrao_snd=True)
        
        # TODO Criar histórico de juros
        
        # TODO Criar histórico de amortizações
        
        # TODO Criar histórico de premio
        
        # Operações do usuário tester
        OperacaoDebenture.objects.create(investidor=tester.investidor, debenture=cls.debenture, preco_unitario=Decimal(10000),
                                         quantidade=5, data=datetime.date.today(), taxa=0, tipo_operacao='C')
        
    
    # TODO testar pagina de erro
    
    def test_usuario_deslogado(self):
        """Testa acesso de usuário deslogado"""
        response = self.client.get(reverse('debentures:detalhar_debenture', kwargs={'debenture_id': self.debenture.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['debenture'].codigo, self.debenture.codigo)
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['juros']), 0)
        self.assertEqual(len(response.context_data['amortizacoes']), 0)
        self.assertEqual(len(response.context_data['premios']), 0)
        
    def test_usuario_logado_sem_operacoes(self):
        """Testa acesso de usuário logado sem operações na debenture"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('debentures:detalhar_debenture', kwargs={'debenture_id': self.debenture.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['debenture'].codigo, self.debenture.codigo)
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['juros']), 0)
        self.assertEqual(len(response.context_data['amortizacoes']), 0)
        self.assertEqual(len(response.context_data['premios']), 0)
        
    def test_usuario_logado_com_operacoes(self):
        """Testa acesso de usuário logado com operações na debenture"""
        self.client.login(username='tester', password='tester')
        
        response = self.client.get(reverse('debentures:detalhar_debenture', kwargs={'debenture_id': self.debenture.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['debenture'].codigo, self.debenture.codigo)
        self.assertEqual(len(response.context_data['operacoes']), 1)
        self.assertEqual(len(response.context_data['juros']), 0)
        self.assertEqual(len(response.context_data['amortizacoes']), 0)
        self.assertEqual(len(response.context_data['premios']), 0)
        
class PainelTestCase (TestCase):
    @classmethod
    def setUpTestData(cls):
        # Usuário sem operações
        User.objects.create_user(username='nizbel', password='nizbel')
        
        # Usuário com operações
        tester = User.objects.create_user(username='tester', password='tester')
    
        # Criar debenture
        cls.debenture_di = Debenture.objects.create(codigo='CMIG15', indice=Debenture.DI, porcentagem=100,
                                             data_emissao=datetime.date(2018, 1, 1), valor_emissao=1000,
                                             data_inicio_rendimento=datetime.date(datetime.date.today().year-1, 1, 3), 
                                             data_vencimento=datetime.date(datetime.date.today().year+2, 12, 31),
                                             incentivada=True, padrao_snd=True)
        
        cls.debenture_ipca = Debenture.objects.create(codigo='CMIG19', indice=Debenture.IPCA, porcentagem=100,
                                             data_emissao=datetime.date(2018, 1, 1), valor_emissao=1000,
                                             data_inicio_rendimento=datetime.date(datetime.date.today().year-1, 1, 3), 
                                             data_vencimento=datetime.date(datetime.date.today().year+2, 12, 31),
                                             incentivada=True, padrao_snd=True)
        
        # Criar histórico de juros
        data_iteracao = datetime.date(datetime.date.today().year-1, 1, 1)
        lista_di = list()
        lista_selic = list()
        lista_ipca = list()
        lista_historico_debenture = list()
        
        cls.juros = 0
        while data_iteracao < datetime.date.today():
            if verifica_se_dia_util(data_iteracao):
                lista_di.append(HistoricoTaxaDI(data=data_iteracao, taxa=Decimal('6.39')))
                
                lista_selic.append(HistoricoTaxaSelic(data=data_iteracao, taxa_diaria=Decimal('1.000272')))
                
                cls.juros += Decimal('1')
                lista_historico_debenture.append(HistoricoValorDebenture(debenture=cls.debenture_di, valor_nominal=10000, juros=cls.juros, premio=0,
                                                                         data=data_iteracao))
                lista_historico_debenture.append(HistoricoValorDebenture(debenture=cls.debenture_ipca, valor_nominal=10000 + cls.juros/2, juros=cls.juros/2, premio=0,
                                                                         data=data_iteracao))
                
            # Adicionar ao primeiro dia pois IPCA é mensal
            if data_iteracao.day == 1:    
                data_ultimo_mes = data_iteracao.replace(day=1) - datetime.timedelta(days=1)
                lista_ipca.append(HistoricoIPCA(valor=Decimal('0.0031'), data_inicio=data_ultimo_mes.replace(day=16), 
                                                data_fim=data_iteracao.replace(day=15)))
            
            data_iteracao += datetime.timedelta(days=1)
            
        HistoricoTaxaDI.objects.bulk_create(lista_di)
        HistoricoTaxaSelic.objects.bulk_create(lista_selic)
        HistoricoIPCA.objects.bulk_create(lista_ipca)
        HistoricoValorDebenture.objects.bulk_create(lista_historico_debenture)
        
        # TODO Criar histórico de amortizações
        
        # TODO Criar histórico de premio
        
        # Operações do usuário tester
        OperacaoDebenture.objects.create(investidor=tester.investidor, debenture=cls.debenture_di, preco_unitario=Decimal(10000),
                                         quantidade=5, data=datetime.date.today(), taxa=0, tipo_operacao='C')
        OperacaoDebenture.objects.create(investidor=tester.investidor, debenture=cls.debenture_ipca, preco_unitario=Decimal(10000),
                                         quantidade=5, data=datetime.date.today(), taxa=0, tipo_operacao='C')
        
    
    # TODO testar pagina de erro
    
    def test_usuario_deslogado(self):
        """Testa acesso de usuário deslogado"""
        response = self.client.get(reverse('debentures:painel_debenture'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['debentures'], {})
        self.assertEqual(response.context_data['dados'], {})
        
    def test_usuario_logado_sem_operacoes(self):
        """Testa acesso de usuário logado sem operações na debenture"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('debentures:painel_debenture'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['debentures'], {})
        self.assertEqual(response.context_data['dados']['total_investido'], 0)
        self.assertEqual(response.context_data['dados']['total_nominal'], 0)
        self.assertEqual(response.context_data['dados']['total_juros'], 0)
        self.assertEqual(response.context_data['dados']['total_premio'], 0)
        self.assertEqual(response.context_data['dados']['total_somado'], 0)
        self.assertEqual(response.context_data['dados']['total_rendimento_ate_vencimento'], 0)
        
    def test_usuario_logado_com_operacoes(self):
        """Testa acesso de usuário logado com operações na debenture"""
        self.client.login(username='tester', password='tester')
        
        response = self.client.get(reverse('debentures:painel_debenture'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data['debentures']), 2)
        self.assertIn(self.debenture_di.id, response.context_data['debentures'].keys())
        self.assertIn(self.debenture_ipca.id, response.context_data['debentures'].keys())
        self.assertEqual(response.context_data['dados']['total_investido'], 100000)
        self.assertEqual(response.context_data['dados']['total_nominal'], response.context_data['dados']['total_investido'] + self.juros * Decimal('2.5'))
        self.assertEqual(response.context_data['dados']['total_juros'], self.juros * Decimal('7.5'))
        self.assertEqual(response.context_data['dados']['total_premio'], 0)
        self.assertEqual(response.context_data['dados']['total_somado'], response.context_data['dados']['total_nominal'] 
                         + response.context_data['dados']['total_juros'] + response.context_data['dados']['total_premio'])
        