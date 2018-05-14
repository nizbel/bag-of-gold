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
        # Usuário com 1 divisão
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        
        bitcoin = Criptomoeda.objects.create(nome='Bitcoin', ticker='BTC')
        bcash = Criptomoeda.objects.create(nome='Bitcoin Cash', ticker='BCH')
        
        compra_1 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.9662'), preco_unitario=Decimal('10000'), data=datetime.date(2017, 6, 6), 
                                                      tipo_operacao='C', criptomoeda=bitcoin, investidor=nizbel.investidor)
        DivisaoOperacaoCriptomoeda.objects.create(operacao=compra_1, divisao=Divisao.objects.get(investidor=nizbel.investidor), quantidade=compra_1.quantidade)
        
        fork = Fork.objects.create(moeda_origem=bitcoin, moeda_recebida=bcash, quantidade=Decimal('0.9662'), data=datetime.date(2017, 7, 2), investidor=nizbel.investidor)
        DivisaoForkCriptomoeda.objects.create(divisao=Divisao.objects.get(investidor=nizbel.investidor), fork=fork, quantidade=fork.quantidade)
        
        # Usuário várias divisões
        multi_div = User.objects.create_user('multi_div', 'multi_div@teste.com', 'multi_div')
        
        div_geral = Divisao.objects.get(investidor=multi_div.investidor)
        nova_div = Divisao.objects.create(investidor=multi_div.investidor, nome='Nova')
        
        compra_2 = OperacaoCriptomoeda.objects.create(quantidade=Decimal('0.9662'), preco_unitario=Decimal('10000'), data=datetime.date(2017, 6, 6), 
                                                      tipo_operacao='C', criptomoeda=bitcoin, investidor=multi_div.investidor)
        div_geral_compra_2 = DivisaoOperacaoCriptomoeda.objects.create(operacao=compra_2, divisao=div_geral, quantidade=Decimal('0.9'))
        nova_div_compra_2 = DivisaoOperacaoCriptomoeda.objects.create(operacao=compra_2, divisao=nova_div, quantidade=Decimal('0.0662'))
        
        fork = Fork.objects.create(moeda_origem=bitcoin, moeda_recebida=bcash, quantidade=Decimal('0.9662'), data=datetime.date(2017, 7, 2), investidor=multi_div.investidor)
        DivisaoForkCriptomoeda.objects.create(divisao=div_geral, fork=fork, quantidade=div_geral_compra_2.quantidade)
        DivisaoForkCriptomoeda.objects.create(divisao=nova_div, fork=fork, quantidade=nova_div_compra_2.quantidade)
        
    def test_usuario_deslogado(self):
        """Testa se redireciona ao receber usuário deslogado"""
        investidor = Investidor.objects.get(user__username='nizbel')
        fork_id = Fork.objects.get(investidor=investidor).id
        response = self.client.get(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)
        
    def test_usuario_logado(self):
        """Testa se resposta da página está OK"""
        investidor = Investidor.objects.get(user__username='nizbel')
        fork_id = Fork.objects.get(investidor=investidor).id
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.get(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}))
        self.assertEqual(response.status_code, 200)
    
    def test_outro_usuario_tentando_editar(self):
        """Testa um usuário que não seja o dono do Fork"""
        investidor = Investidor.objects.get(user__username='nizbel')
        fork_id = Fork.objects.get(investidor=investidor).id
        self.client.login(username='multi_div', password='multi_div')
        response = self.client.get(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}))
        self.assertEqual(response.status_code, 403)
    
    def test_editar_fork_sucesso_1_div(self):
        """Testa a edição de fork com sucesso com uma divisão"""
        investidor = Investidor.objects.get(user__username='nizbel')
        fork_id = Fork.objects.get(investidor=investidor).id
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH')
        
        self.assertFalse(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9661'), investidor=investidor).exists())
        self.assertFalse(DivisaoForkCriptomoeda.objects.filter(divisao=Divisao.objects.get(investidor=investidor), quantidade=Decimal('0.9661'), 
                                                              fork__id=fork_id).exists())
        
        response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9661'),
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
        self.assertTrue(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9661'), investidor=investidor).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=Divisao.objects.get(investidor=investidor), quantidade=Decimal('0.9661'), 
                                                              fork=Fork.objects.get(investidor=investidor)).exists())
                                                              
    def test_editar_fork_sucesso_multi_div(self):
        """Testa a edição de fork com sucesso com várias divisões"""
        investidor = Investidor.objects.get(user__username='multi_div')
        fork_id = Fork.objects.get(investidor=investidor).id
        self.client.login(username='multi_div', password='multi_div')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH')
        
        div_geral = Divisao.objects.get(investidor=investidor, nome='Geral')
        nova_div = Divisao.objects.get(investidor=investidor, nome='Nova')
        
        self.assertFalse(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9661'), investidor=investidor).exists())
        self.assertFalse(DivisaoForkCriptomoeda.objects.filter(divisao=nova_div, quantidade=Decimal('0.0661'), 
                                                              fork__id=fork_id).exists())
        
        response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9661'),
            'divisaoforkcriptomoeda_set-1-divisao': div_geral.id, 'divisaoforkcriptomoeda_set-1-quantidade': Decimal('0.9'),
            'divisaoforkcriptomoeda_set-1-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=div_geral).id,
            'divisaoforkcriptomoeda_set-0-divisao': nova_div.id, 'divisaoforkcriptomoeda_set-0-quantidade': Decimal('0.0661'),
            'divisaoforkcriptomoeda_set-0-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=nova_div).id,
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
        self.assertTrue(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
                                          quantidade=Decimal('0.9661'), investidor=investidor).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=div_geral, quantidade=Decimal('0.9'), 
                                                              fork__id=fork_id).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=nova_div, quantidade=Decimal('0.0661'), 
                                                              fork__id=fork_id).exists())
        
        # Testar excluir uma divisão
        response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9661'),
            'divisaoforkcriptomoeda_set-0-divisao': div_geral.id, 'divisaoforkcriptomoeda_set-0-quantidade': Decimal('0.9661'),
            'divisaoforkcriptomoeda_set-0-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=div_geral).id,
            'divisaoforkcriptomoeda_set-1-DELETE': 1,
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=div_geral, quantidade=Decimal('0.9661'), 
                                                              fork=Fork.objects.get(investidor=investidor)).exists())
        self.assertFalse(DivisaoForkCriptomoeda.objects.filter(divisao=nova_div, fork__id=fork_id).exists())
        
        # Testar adicionar uma divisão
        response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9661'),
            'divisaoforkcriptomoeda_set-0-divisao': div_geral.id, 'divisaoforkcriptomoeda_set-0-quantidade': Decimal('0.9'),
            'divisaoforkcriptomoeda_set-0-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=div_geral).id,
            'divisaoforkcriptomoeda_set-1-divisao': nova_div.id, 'divisaoforkcriptomoeda_set-1-quantidade': Decimal('0.0661'),
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=div_geral, quantidade=Decimal('0.9'), 
                                                              fork__id=fork_id).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=nova_div, quantidade=Decimal('0.0661'), 
                                                              fork__id=fork_id).exists())
        
    def test_editar_fork_qtd_insuficiente(self):
        """Testa editar fork com quantidade insuficiente de moeda de origem"""
        investidor = Investidor.objects.get(user__username='nizbel')
        fork_id = Fork.objects.get(investidor=investidor).id
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        bcash = Criptomoeda.objects.get(ticker='BCH')
        
        response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9663'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_fork'].errors) > 0)
    
    def test_editar_fork_mesma_moeda(self):
        """Testa editar fork inserindo a mesma moeda para origem e recebida"""
        investidor = Investidor.objects.get(user__username='nizbel')
        fork_id = Fork.objects.get(investidor=investidor).id
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        
        response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
            'moeda_origem': bitcoin.id, 'moeda_recebida': bitcoin.id, 'save': 1,
            'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9662'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_fork'].errors) > 0)
        
    def test_excluir_fork_1_div_sucesso(self):
        """Testa a exclusão de fork com sucesso com 1 divisão"""
        investidor = Investidor.objects.get(user__username='nizbel')
        fork_id = Fork.objects.get(investidor=investidor).id
        self.client.login(username='nizbel', password='nizbel')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        
        self.assertTrue(Fork.objects.filter(moeda_origem=bitcoin, investidor=investidor).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=Divisao.objects.get(investidor=investidor), 
                                                              fork__id=fork_id).exists())
        
        response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
            'delete': 1,
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
        self.assertFalse(Fork.objects.filter(moeda_origem=bitcoin, investidor=investidor).exists())
        self.assertFalse(DivisaoForkCriptomoeda.objects.filter(divisao=Divisao.objects.get(investidor=investidor), 
                                                              fork__id=fork_id).exists())
                                                              
    def test_excluir_fork_multi_div_sucesso(self):
        """Testa a exclusão de fork com sucesso com várias divisões"""
        investidor = Investidor.objects.get(user__username='multi_div')
        fork_id = Fork.objects.get(investidor=investidor).id
        
        self.client.login(username='multi_div', password='multi_div')
        
        bitcoin = Criptomoeda.objects.get(ticker='BTC')
        
        self.assertTrue(Fork.objects.filter(moeda_origem=bitcoin, investidor=investidor).exists())
        self.assertTrue(DivisaoForkCriptomoeda.objects.filter(fork__id=fork_id).count() > 0)
        
        response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
            'delete': 1,
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
        self.assertFalse(Fork.objects.filter(moeda_origem=bitcoin, investidor=investidor).exists())
        self.assertFalse(DivisaoForkCriptomoeda.objects.filter(fork__id=fork_id).exists())

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