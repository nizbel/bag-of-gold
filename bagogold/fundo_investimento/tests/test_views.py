# -*- coding: utf-8 -*-
import datetime
from django.test.testcases import TestCase

from django.core.urlresolvers import reverse

from bagogold.fundo_investimento.models import FundoInvestimento, Administrador


class DetalharFundoTestCase(TestCase):
    def test_detalhar_fundo_sem_historico(self):
        """Testa se detalhar fundo sem histórico não causa problema"""
        # Criar fundo
        administrador = Administrador.objects.create(nome='Administrador Teste', cnpj='00.000.0001/0000-91')
        fundo = FundoInvestimento.objects.create(nome='Fundo Teste', administrador=administrador, data_constituicao=datetime.date(2018, 5, 22),
                                                 situacao=FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL, tipo_prazo=FundoInvestimento.PRAZO_LONGO,
                                                 classe=FundoInvestimento.CLASSE_FUNDO_MULTIMERCADO, exclusivo_qualificados=False,
                                                 ultimo_registro=datetime.date.today(), slug='fundo-teste')
        
        response = self.client.get(reverse('fundo_investimento:detalhar_fundo', kwargs={'slug_fundo': fundo.slug}))
        self.assertEqual(response.status_code, 200)
        
    
