# -*- coding: utf-8 -*-
from bagogold.lci_lca.forms import HistoricoCarenciaLetraCreditoForm, \
    HistoricoVencimentoLetraCreditoForm
from bagogold.lci_lca.models import LetraCredito, HistoricoCarenciaLetraCredito, \
    HistoricoVencimentoLetraCredito
from django.contrib.auth.models import User
from django.test import TestCase
import datetime


class FormulariosCarenciaVencimentoTestCase(TestCase):
    
    def setUp(self):
        # Usuário
        user = User.objects.create(username='tester')
        
        # LCI
        lci = LetraCredito.objects.create(nome='LCI Teste', investidor=user.investidor, tipo='C', tipo_rendimento=LetraCredito.LetraCredito_DI)
        carencia_inicial = HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, data=None, carencia=361)
        vencimento_inicial = HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, data=None, vencimento=400)
    
    # Forms de carência
    def test_form_carencia_valido(self):
        """Testa se formulário de carencia é válido"""
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        form_carencia = HistoricoCarenciaLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertTrue(form_carencia.is_valid())
        carencia = form_carencia.save()
        self.assertEqual(carencia.letra_credito, lci)
        self.assertEqual(carencia.data, datetime.date(2017, 9, 10))
        self.assertEqual(carencia.carencia, 365)
        
    def test_form_carencia_maior_que_vencimento_vigente(self):
        """Testa formulário de carencia onde o vencimento vigente está maior do que o carencia inserida"""
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        form_carencia = HistoricoCarenciaLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'carencia': 410,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertFalse(form_carencia.is_valid())

    def test_form_carencia_maior_que_vencimento_periodo(self):
        """Testa formulário de carencia onde o vencimento no período fica maior do que o carencia inserida"""
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 12), vencimento=300)
        form_carencia = HistoricoCarenciaLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertFalse(form_carencia.is_valid())
        
    def test_form_carencia_periodo_carencia_valido(self):
        """
        Testa formulário de carencia onde o vencimento é testado no período entre o carencia inserida e uma próxima carencia
        sem vencimento no período menor que carencia
        """
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 20), carencia=300)
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 20), vencimento=300)
        form_carencia = HistoricoCarenciaLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'carencia': 365,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertTrue(form_carencia.is_valid())
        
    def test_form_carencia_periodo_carencia_invalido(self):
        """
        Testa formulário de carencia onde o vencimento é testado no período entre a carencia inserida e uma próxima carencia,
        com vencimento no período menor que carencia
        """
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 15), vencimento=370)
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 20), carencia=360)
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 20), vencimento=720)
        form_carencia = HistoricoCarenciaLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'carencia': 380,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertFalse(form_carencia.is_valid())
    
    # Forms de vencimento
    def test_form_vencimento_valido(self):
        """Testa se formulário de vencimento é válido"""
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        form_vencimento = HistoricoVencimentoLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertTrue(form_vencimento.is_valid())
        vencimento = form_vencimento.save()
        self.assertEqual(vencimento.letra_credito, lci)
        self.assertEqual(vencimento.data, datetime.date(2017, 9, 10))
        self.assertEqual(vencimento.vencimento, 365)
        
    def test_form_vencimento_menor_que_carencia_vigente(self):
        """Testa formulário de vencimento onde a carência vigente está maior do que o vencimento inserido"""
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        form_vencimento = HistoricoVencimentoLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 360,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertFalse(form_vencimento.is_valid())

    def test_form_vencimento_menor_que_carencia_periodo(self):
        """Testa formulário de vencimento onde a carência no período fica maior do que o vencimento inserido"""
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 12), carencia=720)
        form_vencimento = HistoricoVencimentoLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertFalse(form_vencimento.is_valid())
        
    def test_form_vencimento_periodo_carencia_valido(self):
        """
        Testa formulário de vencimento onde a carência é testada no período entre o vencimento inserido e um próximo vencimento
        sem carência no período maior que vencimento
        """
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 20), vencimento=720)
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 20), carencia=720)
        form_vencimento = HistoricoVencimentoLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertTrue(form_vencimento.is_valid())
        
    def test_form_vencimento_periodo_carencia_invalido(self):
        """
        Testa formulário de vencimento onde a carência é testada no período entre o vencimento inserido e um próximo vencimento,
        com carência no período maior que vencimento
        """
        investidor = User.objects.get(username='tester').investidor
        lci = LetraCredito.objects.get(nome='LCI Teste')
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 15), carencia=370)
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 20), vencimento=720)
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, data=datetime.date(2017, 9, 20), carencia=360)
        form_vencimento = HistoricoVencimentoLetraCreditoForm({
            'letra_credito': lci,
            'data': datetime.date(2017, 9, 10),
            'vencimento': 365,
        }, investidor=investidor, letra_credito=lci, initial={'letra_credito': lci.id})
        self.assertFalse(form_vencimento.is_valid())