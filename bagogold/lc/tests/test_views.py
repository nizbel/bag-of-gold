# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.contrib.messages.api import get_messages
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from bagogold.lc.models import LetraCambio, OperacaoLetraCambio, \
    HistoricoVencimentoLetraCambio, HistoricoCarenciaLetraCambio, \
    HistoricoPorcentagemLetraCambio


class EditarLetraCambioTestCase (TestCase):
    @classmethod
    def setUpTestData(cls):
        super(EditarLetraCambioTestCase, cls).setUpTestData()
        # Usuário sem letras cadastradas
        User.objects.create_user(username='nizbel', password='nizbel')
        
        # Usuário com letras cadastradas
        cls.tester = User.objects.create_user(username='tester', password='tester')
    
        # Criar letra de câmbio
        cls.lc = LetraCambio.objects.create(nome='LC Teste', investidor=cls.tester.investidor, tipo_rendimento=LetraCambio.LC_PREFIXADO)
        HistoricoVencimentoLetraCambio.objects.create(lc=cls.lc, vencimento=365)
        HistoricoCarenciaLetraCambio.objects.create(lc=cls.lc, carencia=365)
        HistoricoPorcentagemLetraCambio.objects.create(lc=cls.lc, porcentagem=120)
        
    def test_usuario_deslogado(self):
        """Testa acesso de usuário deslogado"""
        response = self.client.get(reverse('lcambio:editar_lc', kwargs={'lc_id': self.lc.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/login/' in response.url)
        
    def test_usuario_logado_sem_lc(self):
        """Testa acesso de usuário logado sem letra câmbio, deve bloquear acesso"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('lcambio:editar_lc', kwargs={'lc_id': self.lc.id}))
        self.assertEqual(response.status_code, 403)
        
    def test_usuario_logado_dono_lc(self):
        """Testa acesso de usuário logado dono da letra câmbio"""
        self.client.login(username='tester', password='tester')
        
        response = self.client.get(reverse('lcambio:editar_lc', kwargs={'lc_id': self.lc.id}))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(reverse('lcambio:editar_lc', kwargs={'lc_id': self.lc.id}), 
                                    {'nome': 'LC de Teste', 'tipo_rendimento': LetraCambio.LC_DI, 'lc': self.lc.id, 'save': 1})
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('lcambio:detalhar_lc', kwargs={'lc_id': self.lc.id}))
        
        self.lc = LetraCambio.objects.get(id=self.lc.id)
        self.assertEqual(self.lc.tipo_rendimento, LetraCambio.LC_DI)
        self.assertEqual(self.lc.nome, 'LC de Teste')
        
    def test_usuario_logado_dono_lc_excluir(self):
        """Testa exclusão de LC pelo dono"""
        self.client.login(username='tester', password='tester')
        
        response = self.client.post(reverse('lcambio:editar_lc', kwargs={'lc_id': self.lc.id}), 
                                    {'delete': 1})
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('lcambio:listar_lc'))
        
        self.assertFalse(LetraCambio.objects.filter(id=self.lc.id).exists())
        
    def test_usuario_logado_dono_lc_nao_excluir_se_operacoes(self):
        """Testa exclusão de LC pelo dono quando há operações, não deve permitir"""
        self.client.login(username='tester', password='tester')
        
        OperacaoLetraCambio.objects.create(investidor=self.tester.investidor, data=datetime.date.today(), tipo_operacao='C', quantidade=1000, lc=self.lc)
        
        response = self.client.post(reverse('lcambio:editar_lc', kwargs={'lc_id': self.lc.id}), 
                                    {'delete': 1})
        
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(messages[0], u'Não é possível excluir %s pois existem operações cadastradas' % (self.lc.nome))
        self.assertEqual(response.url, reverse('lcambio:detalhar_lc', kwargs={'lc_id': self.lc.id}))
        
        self.assertTrue(LetraCambio.objects.filter(id=self.lc.id).exists())
        
