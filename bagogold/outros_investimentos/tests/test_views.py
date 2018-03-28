# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoInvestimento, Divisao
from bagogold.bagogold.models.investidores import Investidor
from bagogold.outros_investimentos.models import Investimento, Amortizacao, \
    ImpostoRendaRendimento, Rendimento
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
import datetime

class ViewInserirRendimentoTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
        investimento_1 = Investimento.objects.create(nome='Investimento 1', descricao='', quantidade=Decimal(1000), investidor=user.investidor,
                                                     data=datetime.date(2017, 3, 1))
        
        divisao = Divisao.objects.get(investidor=user.investidor)
        
        divisao_investimento_1 = DivisaoInvestimento.objects.create(divisao=divisao, investimento=investimento_1, quantidade=Decimal(1000))
        
    def test_inserir_rendimento(self):
        """Testa acesso a tela de inserir rendimentos"""
        investidor = Investidor.objects.get(user__username='teste')
        investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        
        self.client.login(username='teste', password='teste')
        response = self.client.get(reverse('outros_investimentos:inserir_rendimento', kwargs={'investimento_id': investimento.id}))
        self.assertEquals(response.status_code, 200)
        
    def test_inserir_rendimento_form_invalido(self):
        """Testa envio de formulário com rendimento inválido"""
        investidor = Investidor.objects.get(user__username='teste')
        investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        
        self.client.login(username='teste', password='teste')
        # Testar form sem informação de imposto
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'investimento_id': investimento.id}), 
                                    {'investimento': investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertIn('imposto_renda', response.context_data['form_rendimento'].errors.keys())
        
        # Testar form com informação de imposto específico porém sem detalhar percentual
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'investimento_id': investimento.id}), 
                                    {'investimento': investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_rendimento'].errors) > 0)
        
    def test_inserir_rendimento_form_valido_sem_imposto(self):
        """Testa envio de formulário com rendimento válido sem IR"""
        investidor = Investidor.objects.get(user__username='teste')
        investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'investimento_id': investimento.id}), 
                                    {'investimento': investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_SEM_IMPOSTO})
        
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(investimento=investimento).exists())
        self.assertFalse(ImpostoRendaRendimento.objects.filter(rendimento__investimento=investimento).exists())
        
    def test_inserir_rendimento_form_valido_com_imposto(self):
        """Testa envio de formulário com rendimento válido com IR longo prazo"""
        investidor = Investidor.objects.get(user__username='teste')
        investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'investimento_id': investimento.id}), 
                                    {'investimento': investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_LONGO_PRAZO})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(investimento=investimento).exists())
        self.assertTrue(ImpostoRendaRendimento.objects.filter(rendimento__investimento=investimento).exists())
        
    def test_inserir_rendimento_form_valido_com_imposto_especifico(self):
        """Testa envio de formulário com rendimento válido com IR específico"""
        investidor = Investidor.objects.get(user__username='teste')
        investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'investimento_id': investimento.id}), 
                                    {'investimento': investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO,
                                     'percentual_imposto': 8})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(investimento=investimento).exists())
        self.assertTrue(ImpostoRendaRendimento.objects.filter(rendimento__investimento=investimento).exists())
        self.assertTrue(ImpostoRendaValorEspecifico.objects.filter(imposto__rendimento__investimento=investimento).exists())