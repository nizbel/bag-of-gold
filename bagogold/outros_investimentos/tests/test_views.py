# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoInvestimento, Divisao
from bagogold.bagogold.models.investidores import Investidor
from bagogold.outros_investimentos.models import Investimento, Amortizacao, \
    ImpostoRendaRendimento, Rendimento, ImpostoRendaValorEspecifico
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
        
        DivisaoInvestimento.objects.create(divisao=divisao, investimento=investimento_1, quantidade=Decimal(1000))
        
    def test_inserir_rendimento(self):
        """Testa acesso a tela de inserir rendimentos"""
        investidor = Investidor.objects.get(user__username='teste')
        investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        
        # Sem logar resposta deve ser redirecionamento para login
        response = self.client.get(reverse('outros_investimentos:inserir_rendimento', kwargs={'id_investimento': investimento.id}))
        self.assertEquals(response.status_code, 302)
        
        self.client.login(username='teste', password='teste')
        response = self.client.get(reverse('outros_investimentos:inserir_rendimento', kwargs={'id_investimento': investimento.id}))
        self.assertEquals(response.status_code, 200)
        
    def test_inserir_rendimento_form_invalido(self):
        """Testa envio de formulário com rendimento inválido"""
        investidor = Investidor.objects.get(user__username='teste')
        investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        
        self.client.login(username='teste', password='teste')
        # Testar form sem informação de imposto
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'id_investimento': investimento.id}), 
                                    {'investimento': investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertIn('imposto_renda', response.context_data['form_rendimento'].errors.keys())
        
        # Testar form com informação de imposto específico porém sem detalhar percentual
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'id_investimento': investimento.id}), 
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
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'id_investimento': investimento.id}), 
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
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'id_investimento': investimento.id}), 
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
        response = self.client.post(reverse('outros_investimentos:inserir_rendimento', kwargs={'id_investimento': investimento.id}), 
                                    {'investimento': investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO,
                                     'percentual_imposto': 8})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(investimento=investimento).exists())
        self.assertTrue(ImpostoRendaRendimento.objects.filter(rendimento__investimento=investimento).exists())
        self.assertTrue(ImpostoRendaValorEspecifico.objects.filter(imposto__rendimento__investimento=investimento).exists())
        
class ViewEditarRendimentoTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        
        investimento_1 = Investimento.objects.create(nome='Investimento 1', descricao='', quantidade=Decimal(1000), investidor=user.investidor,
                                                     data=datetime.date(2017, 3, 1))
        investimento_2 = Investimento.objects.create(nome='Investimento 2', descricao='', quantidade=Decimal(2000), investidor=user.investidor,
                                                     data=datetime.date(2017, 4, 1))
        
        divisao = Divisao.objects.get(investidor=user.investidor)
        
        DivisaoInvestimento.objects.create(divisao=divisao, investimento=investimento_1, quantidade=Decimal(1000))
        
        # Criar rendimento para os todos os tipos de tributação cadastrados
        rendimento_1 = Rendimento.objects.create(valor=Decimal(10), investimento=investimento_1, data=datetime.date(2017, 6, 1))
        rendimento_2 = Rendimento.objects.create(valor=Decimal(10), investimento=investimento_1, data=datetime.date(2017, 9, 1))
        ImpostoRendaRendimento.objects.create(rendimento=rendimento_2, tipo=ImpostoRendaRendimento.TIPO_LONGO_PRAZO)
        rendimento_3 = Rendimento.objects.create(valor=Decimal(10), investimento=investimento_1, data=datetime.date(2017, 12, 1))
        imposto_3 = ImpostoRendaRendimento.objects.create(rendimento=rendimento_3, tipo=ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO)
        ImpostoRendaValorEspecifico.objects.create(imposto=imposto_3, percentual=Decimal(8))
        
    def test_editar_rendimento(self):
        """Testa acesso a tela de editar rendimentos"""
        investidor = Investidor.objects.get(user__username='teste')
        rendimento = Rendimento.objects.get(investimento__investidor=investidor, data=datetime.date(2017, 6, 1))
        
        # Sem logar resposta deve ser redirecionamento para login
        response = self.client.get(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}))
        self.assertEquals(response.status_code, 302)
        
        self.client.login(username='teste', password='teste')
        response = self.client.get(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}))
        self.assertEquals(response.status_code, 200)
        
    def test_editar_rendimento_form_invalido(self):
        """Testa envio de formulário com rendimento inválido"""
        investidor = Investidor.objects.get(user__username='teste')
        rendimento = Rendimento.objects.get(investimento__investidor=investidor, data=datetime.date(2017, 6, 1))
        
        self.client.login(username='teste', password='teste')
        # Testar form sem informação de imposto
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2017, 6, 1), 'valor': 10})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertIn('imposto_renda', response.context_data['form_rendimento'].errors.keys())
        
        # Testar form com informação de imposto específico porém sem detalhar percentual
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2017, 6, 1), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_rendimento'].errors) > 0)
        
        # Testar form alterando investimento
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': Investimento.objects.get(nome='Investimento 2').id, 'data': datetime.date(2017, 6, 1), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO})
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(response.context_data['form_rendimento'].errors) > 0)
        
        
    def test_editar_rendimento_form_valido_sem_imposto(self):
        """Testa envio de formulário com rendimento válido sem IR"""
        investidor = Investidor.objects.get(user__username='teste')
        rendimento = Rendimento.objects.get(investimento__investidor=investidor, data=datetime.date(2017, 6, 1))
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_SEM_IMPOSTO})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(data=datetime.date(2018, 3, 13)).exists())
        
        # Editar tipo de imposto para longo prazo
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_LONGO_PRAZO})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(data=datetime.date(2018, 3, 13), impostorendarendimento__tipo=ImpostoRendaRendimento.TIPO_LONGO_PRAZO).exists())
        self.assertTrue(ImpostoRendaRendimento.objects.filter(rendimento=rendimento).exists())
        
        # Editar tipo de imposto para percentual específico
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO,
                                     'percentual_imposto': 8})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(data=datetime.date(2018, 3, 13), impostorendarendimento__tipo=ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO).exists())
        self.assertTrue(ImpostoRendaRendimento.objects.filter(rendimento=rendimento).exists())
        self.assertTrue(ImpostoRendaValorEspecifico.objects.filter(imposto__rendimento=rendimento).exists())
        
    def test_editar_rendimento_form_valido_com_imposto(self):
        """Testa envio de formulário com rendimento válido com IR longo prazo"""
        investidor = Investidor.objects.get(user__username='teste')
        rendimento = Rendimento.objects.get(investimento__investidor=investidor, data=datetime.date(2017, 9, 1))
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_LONGO_PRAZO})
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(data=datetime.date(2018, 3, 13)).exists())
        
        # Editar tipo de imposto
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_SEM_IMPOSTO})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(data=datetime.date(2018, 3, 13)).exists())
        self.assertFalse(Rendimento.objects.filter(impostorendarendimento__tipo=ImpostoRendaRendimento.TIPO_LONGO_PRAZO).exists())
        self.assertFalse(ImpostoRendaRendimento.objects.filter(rendimento=rendimento).exists())
        
    def test_editar_rendimento_form_valido_com_imposto_especifico(self):
        """Testa envio de formulário com rendimento válido com IR específico"""
        investidor = Investidor.objects.get(user__username='teste')
        rendimento = Rendimento.objects.get(investimento__investidor=investidor, data=datetime.date(2017, 12, 1))
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO,
                                     'percentual_imposto': 8})
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(data=datetime.date(2018, 3, 13)).exists())
        
        # Editar tipo de imposto para longo prazo
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_LONGO_PRAZO})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(data=datetime.date(2018, 3, 13), impostorendarendimento__tipo=ImpostoRendaRendimento.TIPO_LONGO_PRAZO).exists())
        self.assertFalse(Rendimento.objects.filter(impostorendarendimento__tipo=ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO).exists())
        self.assertTrue(ImpostoRendaRendimento.objects.filter(rendimento=rendimento).exists())
        self.assertFalse(ImpostoRendaValorEspecifico.objects.filter().exists())
        
        # Editar tipo de imposto para sem imposto
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'save': 1, 'investimento': rendimento.investimento.id, 'data': datetime.date(2018, 3, 13), 'valor': 10, 
                                     'imposto_renda': ImpostoRendaRendimento.TIPO_SEM_IMPOSTO})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Rendimento.objects.filter(data=datetime.date(2018, 3, 13)).exists())
        self.assertFalse(Rendimento.objects.filter(impostorendarendimento__tipo=ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO).exists())
        self.assertFalse(ImpostoRendaRendimento.objects.filter(rendimento=rendimento).exists())
        self.assertFalse(ImpostoRendaValorEspecifico.objects.filter(imposto__rendimento=rendimento).exists())
        
    def test_apagar_rendimento_imposto_especifico(self):
        """Testa apagar rendimento com IR específico"""
        investidor = Investidor.objects.get(user__username='teste')
        rendimento = Rendimento.objects.get(investimento__investidor=investidor, data=datetime.date(2017, 12, 1))
        
        self.client.login(username='teste', password='teste')
        
        # Apagar rendimento
        response = self.client.post(reverse('outros_investimentos:editar_rendimento', kwargs={'id_rendimento': rendimento.id}), 
                                    {'delete': 1})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertFalse(Rendimento.objects.filter(id=rendimento.id).exists())
        self.assertFalse(ImpostoRendaRendimento.objects.filter(rendimento=rendimento).exists())
        self.assertFalse(ImpostoRendaValorEspecifico.objects.filter(imposto__rendimento=rendimento).exists())