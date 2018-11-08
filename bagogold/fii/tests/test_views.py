# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII
from bagogold.bagogold.models.empresa import Empresa
from bagogold.fii.models import FII, HistoricoFII, ProventoFII, \
    EventoAgrupamentoFII, OperacaoFII, UsoProventosOperacaoFII


class AcompanhamentoFIITestCase (TestCase):
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        
        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
        
        # FII sem histórico sem proventos
        fii_1 = FII.objects.create(ticker='TEST11', empresa=empresa)
        # FII com histórico com proventos
        fii_2 = FII.objects.create(ticker='TSTE11', empresa=empresa)
        # FII sem histórico com proventos
        fii_3 = FII.objects.create(ticker='TSTT11', empresa=empresa)
        # FII com histórico sem proventos
        fii_4 = FII.objects.create(ticker='TSST11', empresa=empresa)
        
        for data in [datetime.date.today() - datetime.timedelta(days=x) for x in range(365)]:
            if data >= datetime.date.today() - datetime.timedelta(days=3):
                HistoricoFII.objects.create(fii=fii_2, preco_unitario=1200, data=data)
                HistoricoFII.objects.create(fii=fii_4, preco_unitario=1200, data=data)
            else:
                HistoricoFII.objects.create(fii=fii_2, preco_unitario=120, data=data)
                HistoricoFII.objects.create(fii=fii_4, preco_unitario=120, data=data)
                
        for data in [datetime.date.today() - datetime.timedelta(days=30*x) for x in range(1, 7)]:
            ProventoFII.objects.create(fii=fii_2, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
                                       oficial_bovespa=True)
            ProventoFII.objects.create(fii=fii_3, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
                                       oficial_bovespa=True)
                                       
    def test_usuario_deslogado(self):
        """Testa o acesso de usuário deslogado"""
        response = self.client.get(reverse('fii:acompanhamento_fii'))
        self.assertEqual(response.status_code, 200)
        
        # TODO testar contexto
        
    def test_usuario_logado(self):
        """Testa o acesso de usuário logado"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('fii:acompanhamento_fii'))
        self.assertEqual(response.status_code, 200)
        
        # TODO testar contexto
        
    def test_filtros(self):
        """Testa os filtros da pesquisa"""
        pass

class DetalharFIITestCase (TestCase):
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        user_vendido = User.objects.create_user('vendido', 'vendido@teste.com', 'vendido')

        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
        
        self.fii_1 = FII.objects.create(ticker='TEST11', empresa=empresa)
        self.fii_2 = FII.objects.create(ticker='TSTE11', empresa=empresa)
        
        for data in [datetime.date.today() - datetime.timedelta(days=x) for x in range(365)]:
            if data >= datetime.date.today() - datetime.timedelta(days=3):
                HistoricoFII.objects.create(fii=self.fii_2, preco_unitario=1200, data=data)
            else:
                HistoricoFII.objects.create(fii=self.fii_2, preco_unitario=120, data=data)
        
        for data in [datetime.date.today() - datetime.timedelta(days=30*x) for x in range(1, 7)]:
            ProventoFII.objects.create(fii=self.fii_2, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
                                       oficial_bovespa=True)
        
        EventoAgrupamentoFII.objects.create(fii=self.fii_2, data=datetime.date.today() - datetime.timedelta(days=3), proporcao=Decimal('0.1'))
        
        OperacaoFII.objects.create(fii=self.fii_2, investidor=nizbel.investidor, data=datetime.date.today() - datetime.timedelta(days=130),
                                   quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
        OperacaoFII.objects.create(fii=self.fii_2, investidor=nizbel.investidor, data=datetime.date.today() - datetime.timedelta(days=80),
                                   quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
        
        OperacaoFII.objects.create(fii=self.fii_2, investidor=user_vendido.investidor, data=datetime.date.today() - datetime.timedelta(days=130),
                                   quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
        OperacaoFII.objects.create(fii=self.fii_2, investidor=user_vendido.investidor, data=datetime.date.today() - datetime.timedelta(days=80),
                                   quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='V')
    
    def test_usuario_deslogado_fii_vazio(self):
        """Testa o acesso a view para um fii sem infos com um usuário deslogado"""
        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TEST11'}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['historico']), 0)
        self.assertEqual(len(response.context_data['proventos']), 0)
        self.assertEqual(response.context_data['fii'], self.fii_1)
        
    def test_usuario_logado_fii_vazio(self):
        """Testa o acesso a view para um fii sem infos com um usuário logado"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': self.fii_1.ticker}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['historico']), 0)
        self.assertEqual(len(response.context_data['proventos']), 0)
        self.assertEqual(response.context_data['fii'], self.fii_1)
        
    def test_usuario_deslogado_fii_com_infos(self):
        """Testa o acesso a view para um fii com infos com um usuário deslogado"""
        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': self.fii_2.ticker}))
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 0)
        self.assertEqual(len(response.context_data['historico']), 365)
        self.assertEqual(len(response.context_data['proventos']), 6)
        self.assertEqual(response.context_data['fii'], self.fii_2)
        
    def test_usuario_logado_fii_com_infos(self):
        """Testa o acesso a view para um fii com infos com um usuário logado"""
        self.client.login(username='nizbel', password='nizbel')

        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': self.fii_2.ticker}))      
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 2)
        self.assertEqual(len(response.context_data['historico']), 365)
        self.assertEqual(len(response.context_data['proventos']), 6)
        self.assertEqual(response.context_data['fii'], self.fii_2)
        # Quantidade de cotas atual é 1 devido ao agrupamento
        self.assertEqual(response.context_data['fii'].qtd_cotas, 1)
        
        
    def test_usuario_logado_fii_com_infos_vendido(self):
        """Testa o acesso a view para um fii com infos com um usuário logado, que já tinha liquidado sua posição"""
        self.client.login(username='vendido', password='vendido')

        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': self.fii_2.ticker}))      
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['operacoes']), 2)
        self.assertEqual(len(response.context_data['historico']), 365)
        self.assertEqual(len(response.context_data['proventos']), 6)
        self.assertEqual(response.context_data['fii'], self.fii_2)
        self.assertEqual(response.context_data['fii'].qtd_cotas, 0)
        
    def test_fii_nao_encontrado(self):
        """Testa o retorno caso o FII não seja encontrado"""
        response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTS11'}))      
        self.assertEqual(response.status_code, 404)
        
class HistoricoFIITestCase (TestCase):
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        self.investidor_nizbel = nizbel.investidor
        user_sem_operacoes = User.objects.create_user('vazio', 'vazio@teste.com', 'vazio')

        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
        
        fii_1 = FII.objects.create(ticker='TEST11', empresa=empresa)
        fii_2 = FII.objects.create(ticker='TSTE11', empresa=empresa)

        for data in [datetime.date.today() - datetime.timedelta(days=x) for x in range(35)]:
            if data >= datetime.date.today() - datetime.timedelta(days=3):
                HistoricoFII.objects.create(fii=fii_2, preco_unitario=1000, data=data)
            else:
                HistoricoFII.objects.create(fii=fii_2, preco_unitario=100, data=data)
        
        ProventoFII.objects.create(fii=fii_2, valor_unitario=Decimal('0.1'), data_ex=datetime.date.today() - datetime.timedelta(days=35), data_pagamento=datetime.date.today() - datetime.timedelta(days=30),
                                   oficial_bovespa=True)
        ProventoFII.objects.create(fii=fii_2, valor_unitario=Decimal('0.1'), data_ex=datetime.date.today() - datetime.timedelta(days=15), data_pagamento=datetime.date.today() - datetime.timedelta(days=5),
                                   oficial_bovespa=True)
        
        EventoAgrupamentoFII.objects.create(fii=fii_2, data=datetime.date.today() - datetime.timedelta(days=3), proporcao=Decimal('0.1'))
        
        OperacaoFII.objects.create(fii=fii_2, investidor=nizbel.investidor, data=datetime.date.today() - datetime.timedelta(days=20),
                                   quantidade=10, preco_unitario=100, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
        operacao_uso_prov = OperacaoFII.objects.create(fii=fii_2, investidor=nizbel.investidor, data=datetime.date.today() - datetime.timedelta(days=10),
                                   quantidade=10, preco_unitario=100, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
        divisao_op_uso_prov = DivisaoOperacaoFII.objects.create(divisao=self.investidor_nizbel.divisaoprincipal.divisao, quantidade=operacao_uso_prov.quantidade, operacao=operacao_uso_prov)
        UsoProventosOperacaoFII.objects.create(operacao=operacao_uso_prov, qtd_utilizada=Decimal(1), divisao_operacao=divisao_op_uso_prov)
        
    
    def test_usuario_logado_sem_operacoes(self):
        """Testa o acesso de um usuário logado sem operações cadastradas"""
        self.client.login(username='vazio', password='vazio')
        
        response = self.client.get(reverse('fii:historico_fii'))      
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['lista_conjunta']), 0)
        self.assertEqual(len(response.context_data['graf_poupanca_proventos']), 0)
        self.assertEqual(len(response.context_data['graf_gasto_total']), 0)
        self.assertEqual(len(response.context_data['graf_patrimonio']), 0)
        self.assertEqual(response.context_data['dados'], {})
        
    def test_usuario_logado_com_operacoes(self):
        """Testa o acesso de um usuário logado com operações cadastradas"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('fii:historico_fii'))      
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertEqual(len(response.context_data['lista_conjunta']), 4)
        #self.assertEqual(len(response.context_data['graf_poupanca_proventos']), 1)
        #self.assertEqual(len(response.context_data['graf_gasto_total']), 1)
        #self.assertEqual(len(response.context_data['graf_patrimonio']), 1)
        dados = response.context_data['dados']
        self.assertEqual(dados['total_proventos'], 0)
        self.assertEqual(dados['total_gasto'], Decimal('2019.2'))
        self.assertEqual(dados['patrimonio'], Decimal(2000))
        self.assertEqual(dados['lucro'], Decimal('-19.2'))
        self.assertEqual(dados['lucro_percentual'], Decimal('-19.2') / dados['total_gasto'] * 100)