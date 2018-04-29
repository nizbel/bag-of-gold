# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from django.test.testcases import TestCase

from django.core.urlresolvers import reverse

from bagogold.bagogold.models.divisoes import DivisaoOperacaoCriptomoeda, \
    Divisao, DivisaoForkCriptomoeda
from bagogold.bagogold.models.investidores import Investidor
from bagogold.criptomoeda.models import Criptomoeda, OperacaoCriptomoeda, Fork


class EditarForkTestCase(TestCase):
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        
        bitcoin = Criptomoeda.objects.create(nome='Bitcoin', ticker='BTC')
        bcash = Criptomoeda.objects.create(nome='Bitcoin Cash', ticker='BCH')
        
        compra_1 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.9662'), preco_unitario=Decimal('10000'), data=datetime.date(2017, 6, 6), 
                                                      tipo_operacao='C', criptomoeda=bitcoin, investidor=nizbel.investidor)
        DivisaoOperacaoCriptomoeda.objects.create(operacao=compra_1, divisao=Divisao.objects.get(investidor=nizbel.investidor), quantidade=compra_1.quantidade)
        
    def test_usuario_deslogado(self):
        """Testa se redireciona ao receber usuário deslogado"""
        response = self.client.get(reverse('criptomoeda:editar_fork'))
        self.assertEqual(response.status_code, 302)
        # TODO Verificar se resposta foi para tela de login
        self.assertTrue('/login/' in response.url)
        
    def test_usuario_logado(self):
        """Testa se resposta da página está OK"""
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.get(reverse('criptomoeda:editar_fork'))
        self.assertEqual(response.status_code, 200)
    
    def test_editar_fork_sucesso(self):
        """Testa a inserção de fork com sucesso"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH')
        
        
        self.assertFalse(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9662'), investidor=investidor).exists())
        self.assertFalse(DivisaoForkCriptomoeda.objects.filter(divisao=Divisao.objects.get(investidor=investidor), quantidade=Decimal('0.9662'), 
                                                              fork=Fork.objects.get(investidor=investidor)).exists())
        
        response = self.client.post(reverse('criptomoeda:editar_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9662'),
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
        self.assertTrue(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9662'), investidor=investidor).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=Divisao.objects.get(investidor=investidor), quantidade=Decimal('0.9662'), 
                                                              fork=Fork.objects.get(investidor=investidor)).exists())
        
    def test_editar_fork_qtd_insuficiente(self):
        """Testa editar fork com quantidade insuficiente de moeda de origem"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH')
        
        response = self.client.post(reverse('criptomoeda:editar_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9663'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_fork'].errors) > 0)
    
    def test_editar_fork_mesma_moeda(self):
        """Testa editar fork inserindo a mesma moeda para origem e recebida"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH') 
        
        response = self.client.post(reverse('criptomoeda:editar_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bitcoin.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9662'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_fork'].errors) > 0)

class InserirForkTestCase(TestCase):
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        
        bitcoin = Criptomoeda.objects.create(nome='Bitcoin', ticker='BTC')
        bcash = Criptomoeda.objects.create(nome='Bitcoin Cash', ticker='BCH')
        
        compra_1 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.9662'), preco_unitario=Decimal('10000'), data=datetime.date(2017, 6, 6), 
                                                      tipo_operacao='C', criptomoeda=bitcoin, investidor=nizbel.investidor)
        DivisaoOperacaoCriptomoeda.objects.create(operacao=compra_1, divisao=Divisao.objects.get(investidor=nizbel.investidor), quantidade=compra_1.quantidade)
        
    def test_usuario_deslogado(self):
        """Testa se redireciona ao receber usuário deslogado"""
        response = self.client.get(reverse('criptomoeda:inserir_fork'))
        self.assertEqual(response.status_code, 302)
        # TODO Verificar se resposta foi para tela de login
        self.assertTrue('/login/' in response.url)
        
    def test_usuario_logado(self):
        """Testa se resposta da página está OK"""
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.get(reverse('criptomoeda:inserir_fork'))
        self.assertEqual(response.status_code, 200)
    
    def test_inserir_fork_sucesso(self):
        """Testa a inserção de fork com sucesso"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH')
        
        
        self.assertFalse(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9662'), investidor=investidor).exists())
        
        response = self.client.post(reverse('criptomoeda:inserir_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9662'),
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
        self.assertTrue(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9662'), investidor=investidor).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=Divisao.objects.get(investidor=investidor), quantidade=Decimal('0.9662'), 
                                                              fork=Fork.objects.get(investidor=investidor)).exists())
        
    def test_inserir_fork_qtd_insuficiente(self):
        """Testa inserir fork com quantidade insuficiente de moeda de origem"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH')
        
        response = self.client.post(reverse('criptomoeda:inserir_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9663'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_fork'].errors) > 0)
    
    def test_inserir_fork_mesma_moeda(self):
        """Testa inserir fork inserindo a mesma moeda para origem e recebida"""
        investidor = Investidor.objects.get(user__username='nizbel')
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH') 
        
        response = self.client.post(reverse('criptomoeda:inserir_fork'), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bitcoin.id,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9662'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_fork'].errors) > 0)