# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls.base import reverse

from bagogold.bagogold.models.divisoes import Divisao, \
    DivisaoOperacaoLCI_LCA
from bagogold.bagogold.models.investidores import Investidor
from bagogold.lci_lca.models import LetraCredito, HistoricoCarenciaLetraCredito, \
    HistoricoPorcentagemLetraCredito, HistoricoVencimentoLetraCredito, \
    OperacaoLetraCredito, OperacaoVendaLetraCredito


class EditarOperacaoLetraCreditoTestCase(TestCase):
    def setUp(self):
        # Usuário com 1 divisão
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        
        lci = LetraCredito.objects.create(investidor=nizbel.investidor, nome='LCI', tipo_rendimento=LetraCredito.LCI_LCA_DI)
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, carencia=720, data=None)
        HistoricoPorcentagemLetraCredito.objects.create(letra_credito=lci, porcentagem=90, data=None)
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, vencimento=720, data=None)
        
        compra_1 = OperacaoLetraCredito.objects.create(quantidade=1000, data=datetime.date(2018, 10, 4), 
                                                      tipo_operacao='C', letra_credito=lci, investidor=nizbel.investidor)
        DivisaoOperacaoLCI_LCA.objects.create(operacao=compra_1, divisao=Divisao.objects.get(investidor=nizbel.investidor), quantidade=compra_1.quantidade)
        
        # Usuário várias divisões
        multi_div = User.objects.create_user('multi_div', 'multi_div@teste.com', 'multi_div')
        
        div_geral = Divisao.objects.get(investidor=multi_div.investidor)
        nova_div = Divisao.objects.create(investidor=multi_div.investidor, nome='Nova')
        
        compra_2 = OperacaoLetraCredito.objects.create(quantidade=1000, data=datetime.date(2018, 4, 15), 
                                                      tipo_operacao='C', letra_credito=lci, investidor=multi_div.investidor)
        div_geral_compra_2 = DivisaoOperacaoLCI_LCA.objects.create(operacao=compra_2, divisao=div_geral, quantidade=600)
        nova_div_compra_2 = DivisaoOperacaoLCI_LCA.objects.create(operacao=compra_2, divisao=nova_div, quantidade=400)
        
    def test_usuario_deslogado(self):
        """Testa se redireciona ao receber usuário deslogado"""
        investidor = Investidor.objects.get(user__username='nizbel')
        operacao_id = OperacaoLetraCredito.objects.get(investidor=investidor).id
        response = self.client.get(reverse('lci_lca:editar_operacao_lci_lca', kwargs={'operacao_id': operacao_id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)
        
    def test_usuario_logado(self):
        """Testa se resposta da página está OK"""
        investidor = Investidor.objects.get(user__username='nizbel')
        operacao_id = OperacaoLetraCredito.objects.get(investidor=investidor).id
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.get(reverse('lci_lca:editar_operacao_lci_lca', kwargs={'operacao_id': operacao_id}))
        self.assertEqual(response.status_code, 200)
    
    def test_outro_usuario_tentando_editar(self):
        """Testa um usuário que não seja o dono da operação"""
        investidor = Investidor.objects.get(user__username='nizbel')
        operacao_id = OperacaoLetraCredito.objects.get(investidor=investidor).id
        self.client.login(username='multi_div', password='multi_div')
        response = self.client.get(reverse('lci_lca:editar_operacao_lci_lca', kwargs={'operacao_id': operacao_id}))
        self.assertEqual(response.status_code, 403)
    
    def test_editar_operacao_sucesso_1_div(self):
        """Testa a edição de operação com sucesso com uma divisão"""
        investidor = Investidor.objects.get(user__username='nizbel')
        operacao = OperacaoLetraCredito.objects.get(investidor=investidor)
        self.client.login(username='nizbel', password='nizbel')
        
        self.assertFalse(OperacaoLetraCredito.objects.filter(quantidade=1100, investidor=investidor,
                                                              data=datetime.date(2018, 4, 12)).exists())
        self.assertFalse(DivisaoOperacaoLCI_LCA.objects.filter(divisao=Divisao.objects.get(investidor=investidor), quantidade=1100, 
                                                              operacao__id=operacao.id).exists())
        
        response = self.client.post(reverse('lci_lca:editar_operacao_lci_lca', kwargs={'operacao_id': operacao.id}), {
            'letra_credito': operacao.letra_credito_id, 'save': 1, 'id_investidor': investidor.id, 'tipo_operacao': 'C',
            'data': datetime.date(2018, 4, 12), 'quantidade': 1100,
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('lci_lca:historico_lci_lca'))
        self.assertTrue(OperacaoLetraCredito.objects.filter(quantidade=1100, investidor=investidor,
                                                              data=datetime.date(2018, 4, 12)).exists())
        self.assertTrue(DivisaoOperacaoLCI_LCA.objects.filter(divisao=Divisao.objects.get(investidor=investidor), quantidade=1100, 
                                                              operacao__id=operacao.id).exists())
                                                              
#     def test_editar_operacao_sucesso_multi_div(self):
#         """Testa a edição de operação com sucesso com várias divisões"""
#         investidor = Investidor.objects.get(user__username='multi_div')
#         fork_id = Fork.objects.get(investidor=investidor).id
#         self.client.login(username='multi_div', password='multi_div')
#         
#         bitcoin = Criptomoeda.objects.get(ticker='BTC')
#         bcash = Criptomoeda.objects.get(ticker='BCH')
#         
#         div_geral = Divisao.objects.get(investidor=investidor, nome='Geral')
#         nova_div = Divisao.objects.get(investidor=investidor, nome='Nova')
#         
#         self.assertFalse(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
#                                           quantidade=Decimal('0.9661'), investidor=investidor).exists())
#         self.assertFalse(DivisaoForkCriptomoeda.objects.filter(divisao=nova_div, quantidade=Decimal('0.0661'), 
#                                                               fork__id=fork_id).exists())
#         
#         response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
#             'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
#             'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9661'),
#             'divisaoforkcriptomoeda_set-INITIAL_FORMS': '2', 'divisaoforkcriptomoeda_set-TOTAL_FORMS': '2',
#             'divisaoforkcriptomoeda_set-0-divisao': div_geral.id, 'divisaoforkcriptomoeda_set-0-quantidade': Decimal('0.9'),
#             'divisaoforkcriptomoeda_set-0-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=div_geral).id,
#             'divisaoforkcriptomoeda_set-1-divisao': nova_div.id, 'divisaoforkcriptomoeda_set-1-quantidade': Decimal('0.0661'),
#             'divisaoforkcriptomoeda_set-1-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=nova_div).id,
#         })
#         
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
#         self.assertTrue(Fork.objects.filter(moeda_origem=bitcoin, moeda_recebida=bcash, data=datetime.date(2017, 7, 1), 
#                                           quantidade=Decimal('0.9661'), investidor=investidor).exists())
#         self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=div_geral, quantidade=Decimal('0.9'), 
#                                                               fork__id=fork_id).exists())
#         self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=nova_div, quantidade=Decimal('0.0661'), 
#                                                               fork__id=fork_id).exists())
#         
#         # Testar excluir uma divisão
#         response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
#             'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
#             'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9661'),
#             'divisaoforkcriptomoeda_set-INITIAL_FORMS': '2', 'divisaoforkcriptomoeda_set-TOTAL_FORMS': '2',
#             'divisaoforkcriptomoeda_set-0-divisao': div_geral.id, 'divisaoforkcriptomoeda_set-0-quantidade': Decimal('0.9661'),
#             'divisaoforkcriptomoeda_set-0-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=div_geral).id,
#             'divisaoforkcriptomoeda_set-1-divisao': nova_div.id, 'divisaoforkcriptomoeda_set-1-quantidade': Decimal('0.0661'),
#             'divisaoforkcriptomoeda_set-1-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=nova_div).id,
#             'divisaoforkcriptomoeda_set-1-DELETE': 1,
#         })
#         
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
#         self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=div_geral, quantidade=Decimal('0.9661'), 
#                                                               fork=Fork.objects.get(investidor=investidor)).exists())
#         self.assertFalse(DivisaoForkCriptomoeda.objects.filter(divisao=nova_div, fork__id=fork_id).exists())
#         
#         # Testar adicionar uma divisão
#         response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
#             'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
#             'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9661'),
#             'divisaoforkcriptomoeda_set-INITIAL_FORMS': '1', 'divisaoforkcriptomoeda_set-TOTAL_FORMS': '2',
#             'divisaoforkcriptomoeda_set-0-divisao': div_geral.id, 'divisaoforkcriptomoeda_set-0-quantidade': Decimal('0.9'),
#             'divisaoforkcriptomoeda_set-0-id': DivisaoForkCriptomoeda.objects.get(fork__id=fork_id, divisao=div_geral).id,
#             'divisaoforkcriptomoeda_set-1-divisao': nova_div.id, 'divisaoforkcriptomoeda_set-1-quantidade': Decimal('0.0661'),
#         })
#         
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(response.url, reverse('criptomoeda:historico_criptomoeda'))
#         self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=div_geral, quantidade=Decimal('0.9'), 
#                                                               fork__id=fork_id).exists())
#         self.assertTrue(DivisaoForkCriptomoeda.objects.filter(divisao=nova_div, quantidade=Decimal('0.0661'), 
#                                                               fork__id=fork_id).exists())
        
#         
#         
#             'data': datetime.date(2017, 7, 1), 'quantidade': Decimal('0.9663'),
#             'moeda_origem': bitcoin.id, 'moeda_recebida': bcash.id, 'save': 1,
#         """Testa editar venda com quantidade insuficiente na operação de compra"""
#         bcash = Criptomoeda.objects.get(ticker='BCH')
#         bitcoin = Criptomoeda.objects.get(ticker='BTC')
#         fork_id = Fork.objects.get(investidor=investidor).id
#         investidor = Investidor.objects.get(user__username='nizbel')
#         response = self.client.post(reverse('criptomoeda:editar_fork', kwargs={'id_fork': fork_id}), {
#         self.assertEqual(response.status_code, 200)
#         self.assertTrue(len(response.context_data['form_fork'].errors) > 0)
#         self.client.login(username='nizbel', password='nizbel')
#         })
#     def test_editar_fork_qtd_insuficiente(self):
    
    def test_editar_operacao_compra_para_venda(self):
        """Testa editar operação de compra transformando em operação de venda"""
        investidor = Investidor.objects.get(user__username='nizbel')
        operacao = OperacaoLetraCredito.objects.get(investidor=investidor)
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.post(reverse('lci_lca:editar_operacao_lci_lca', kwargs={'operacao_id': operacao.id}), {
            'letra_credito': operacao.letra_credito_id, 'save': 1, 'id_investidor': investidor.id, 'tipo_operacao': 'V',
            'data': operacao.data, 'quantidade': operacao.quantidade,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_operacao_lci_lca'].errors) > 0)
        
    def test_excluir_operacao_1_div_sucesso(self):
        """Testa a exclusão de operação com sucesso com 1 divisão"""
        investidor = Investidor.objects.get(user__username='nizbel')
        operacao_id = OperacaoLetraCredito.objects.get(investidor=investidor).id
        
        self.client.login(username='nizbel', password='nizbel')
        
        self.assertTrue(OperacaoLetraCredito.objects.filter(id=operacao_id, investidor=investidor).exists())
        self.assertTrue(DivisaoOperacaoLCI_LCA.objects.filter(divisao=Divisao.objects.get(investidor=investidor), 
                                                              operacao__id=operacao_id).exists())
        
        response = self.client.post(reverse('lci_lca:editar_operacao_lci_lca', kwargs={'operacao_id': operacao_id}), {
            'delete': 1,
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('lci_lca:historico_lci_lca'))
        self.assertFalse(OperacaoLetraCredito.objects.filter(id=operacao_id, investidor=investidor).exists())
        self.assertFalse(DivisaoOperacaoLCI_LCA.objects.filter(divisao=Divisao.objects.get(investidor=investidor), 
                                                              operacao__id=operacao_id).exists())
                                                              
    def test_excluir_operacao_multi_div_sucesso(self):
        """Testa a exclusão de operação com sucesso com várias divisões"""
        investidor = Investidor.objects.get(user__username='multi_div')
        operacao_id = OperacaoLetraCredito.objects.get(investidor=investidor).id
        
        self.client.login(username='multi_div', password='multi_div')
        
        self.assertTrue(OperacaoLetraCredito.objects.filter(id=operacao_id, investidor=investidor).exists())
        self.assertTrue(DivisaoOperacaoLCI_LCA.objects.filter(operacao__id=operacao_id).count() > 0)
        
        response = self.client.post(reverse('lci_lca:editar_operacao_lci_lca', kwargs={'operacao_id': operacao_id}), 
                                    {'delete': 1})
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('lci_lca:historico_lci_lca'))
        self.assertFalse(OperacaoLetraCredito.objects.filter(id=operacao_id, investidor=investidor).exists())
        self.assertFalse(DivisaoOperacaoLCI_LCA.objects.filter(operacao__id=operacao_id).exists())
        
    def test_nao_permitir_excluir_operacao_com_venda(self):
        """Testa o bloqueio de exclusao de uma operação de compra que já possua venda cadastrada"""
        investidor = Investidor.objects.get(user__username='nizbel')
        operacao = OperacaoLetraCredito.objects.get(investidor=investidor)
        
        self.client.login(username='nizbel', password='nizbel')
        
        # Cadastrar venda
        venda = OperacaoLetraCredito.objects.create(investidor=investidor, data=datetime.date(2018, 5, 10), quantidade=500,
            tipo_operacao='V', letra_credito=operacao.letra_credito)
        OperacaoVendaLetraCredito.objects.create(operacao_compra=operacao, operacao_venda=venda)
        
        response = self.client.post(reverse('lci_lca:editar_operacao_lci_lca', kwargs={'operacao_id': operacao.id}),
                                    {'delete': 1})
        
        self.assertEqual(response.status_code, 200)
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(unicode(messages[0]), u'Não é possível excluir operação de compra que já tenha vendas registradas')
        # Verifica que operação não foi apagada
        self.assertTrue(OperacaoLetraCredito.objects.filter(investidor=investidor, id=operacao.id).exists())