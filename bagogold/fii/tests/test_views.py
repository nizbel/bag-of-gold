# -*- coding: utf-8 -*-
import calendar
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII, Divisao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.fii.models import FII, HistoricoFII, ProventoFII, \
    EventoAgrupamentoFII, OperacaoFII, UsoProventosOperacaoFII
from django.test.utils import freeze_time


class AcompanhamentoFIITestCase (TestCase):
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        
        empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
        
        # FII sem histórico sem proventos
        self.fii_1 = FII.objects.create(ticker='TEST11', empresa=empresa)
        # FII com histórico com proventos
        self.fii_2 = FII.objects.create(ticker='TSTE11', empresa=empresa)
        # FII sem histórico com proventos
        self.fii_3 = FII.objects.create(ticker='TSTT11', empresa=empresa)
        # FII com histórico sem proventos
        self.fii_4 = FII.objects.create(ticker='TSST11', empresa=empresa)
        
        for data in [datetime.date.today() - datetime.timedelta(days=x) for x in range(365)]:
            if data >= datetime.date.today() - datetime.timedelta(days=3):
                HistoricoFII.objects.create(fii=self.fii_2, preco_unitario=1200, data=data)
                HistoricoFII.objects.create(fii=self.fii_4, preco_unitario=1200, data=data)
            else:
                HistoricoFII.objects.create(fii=self.fii_2, preco_unitario=120, data=data)
                HistoricoFII.objects.create(fii=self.fii_4, preco_unitario=120, data=data)
                
        for data in [datetime.date.today() - datetime.timedelta(days=30*x) for x in range(1, 7)]:
            ProventoFII.objects.create(fii=self.fii_2, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
                                       oficial_bovespa=True, tipo_provento=ProventoFII.TIPO_PROVENTO_RENDIMENTO)
            ProventoFII.objects.create(fii=self.fii_3, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
                                       oficial_bovespa=True, tipo_provento=ProventoFII.TIPO_PROVENTO_RENDIMENTO)
                                       
    def test_usuario_deslogado(self):
        """Testa o acesso de usuário deslogado"""
        response = self.client.get(reverse('fii:acompanhamento_fii'))
        self.assertEqual(response.status_code, 200)
        
        # TODO testar contexto
        # Testar filtros
        self.assertIn('filtros', response.context_data.keys())
        self.assertTrue(response.context_data['filtros']['ignorar_indisponiveis'])
        ultimo_dia_mes = calendar.monthrange(datetime.date.today().year, datetime.date.today().month)[1]
        self.assertEqual(response.context_data['filtros']['mes_inicial'], datetime.date.today().replace(day=ultimo_dia_mes) \
                         .replace(year=datetime.date.today().year-1) + datetime.timedelta(days=1))
        
        # Quantidade de meses verificado
        qtd_meses =  1 + datetime.date.today().month - response.context_data['filtros']['mes_inicial'].month \
        + (datetime.date.today().year - response.context_data['filtros']['mes_inicial'].year) * 12
        
        # Testar fiis
        self.assertEqual(len(response.context_data['fiis']), 2)
        self.assertIn(self.fii_2.ticker, [fii.ticker for fii in response.context_data['fiis']])
        self.assertIn(self.fii_4.ticker, [fii.ticker for fii in response.context_data['fiis']])
        
        fii_2 = [fii for fii in response.context_data['fiis'] if fii.ticker == self.fii_2.ticker][0]
        self.assertEqual(fii_2.valor_atual, 1200)
        self.assertEqual(fii_2.data, datetime.date.today())
        self.assertEqual(fii_2.total_amortizacoes, 0)
        self.assertEqual(fii_2.total_rendimentos, Decimal('5.40'))
        self.assertEqual(fii_2.percentual_retorno, fii_2.total_rendimentos / fii_2.valor_atual * 100)
#         self.assertEqual(fii_2.percentual_retorno_mensal, )
#         self.assertEqual(fii_2.percentual_retorno_anual, )
        self.assertEqual(fii_2.total_proventos, fii_2.total_amortizacoes + fii_2.total_rendimentos)
        
        fii_4 = [fii for fii in response.context_data['fiis'] if fii.ticker == self.fii_4.ticker][0]
        self.assertEqual(fii_4.valor_atual, 1200)
        self.assertEqual(fii_4.data, datetime.date.today())
        self.assertEqual(fii_4.total_amortizacoes, 0)
        self.assertEqual(fii_4.total_rendimentos, 0)
        self.assertEqual(fii_4.percentual_retorno, fii_4.total_rendimentos / fii_4.valor_atual * 100)
#         self.assertEqual(fii_4.percentual_retorno_mensal, )
#         self.assertEqual(fii_4.percentual_retorno_anual, )
        self.assertEqual(fii_4.total_proventos, fii_4.total_amortizacoes + fii_4.total_rendimentos)
        
        # Testar alterar filtros
        response = self.client.post(reverse('fii:acompanhamento_fii'), {'mes_inicial': '%s/%s' % ((datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).month, 
            datetime.date.today().year)})
        
        # TODO Testar contexto
        # Testar filtros
        self.assertIn('filtros', response.context_data.keys())
        self.assertFalse(response.context_data['filtros']['ignorar_indisponiveis'])
        self.assertEqual(response.context_data['filtros']['mes_inicial'], (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1))
                         
        # Quantidade de meses verificado
        qtd_meses =  2
        
        # Testar fiis
        self.assertEqual(len(response.context_data['fiis']), 4)
        self.assertIn(self.fii_1.ticker, [fii.ticker for fii in response.context_data['fiis']])
        self.assertIn(self.fii_2.ticker, [fii.ticker for fii in response.context_data['fiis']])
        self.assertIn(self.fii_3.ticker, [fii.ticker for fii in response.context_data['fiis']])
        self.assertIn(self.fii_4.ticker, [fii.ticker for fii in response.context_data['fiis']])
        
    def test_usuario_logado(self):
        """Testa o acesso de usuário logado"""
        self.client.login(username='nizbel', password='nizbel')
        
        response = self.client.get(reverse('fii:acompanhamento_fii'))
        self.assertEqual(response.status_code, 200)
        
        # TODO testar contexto
        
    def test_filtros(self):
        """Testa os filtros da pesquisa"""
        pass
    
    def test_acessar_em_dezembro(self):
        """Testa o acesso no mês de Dezembro, erro encontrado em 01/12/2018, tentava criar data com mês 13"""
        with freeze_time(float(1543699932)):
            response = self.client.get(reverse('fii:acompanhamento_fii'))
            self.assertEqual(response.status_code, 200)

            response = self.client.post(reverse('fii:acompanhamento_fii'), {'mes_inicial': '13/2018'})
            self.assertEqual(response.status_code, 200)
        

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
        
class ViewInserirOperacaoTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        self.investidor = user.investidor
        
        empresa = Empresa.objects.create(nome='BB Progressivo', nome_pregao='BBPO')
        self.fii = FII.objects.create(ticker='BBPO11', empresa=empresa)
        
        self.divisao_geral = Divisao.objects.get(investidor=self.investidor)
        
    def test_acesso(self):
        """Testa acesso a tela de inserir rendimentos"""
        #investidor = Investidor.objects.get(user__username='teste')
        #investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        
        # Sem logar resposta deve ser redirecionamento para login
        response = self.client.get(reverse('fii:inserir_operacao_fii'))
        self.assertEquals(response.status_code, 302)
        
        self.client.login(username='teste', password='teste')
        response = self.client.get(reverse('fii:inserir_operacao_fii'))
        self.assertEquals(response.status_code, 200)
        
    def test_inserir_operacao_uma_divisao(self):
        """Testa inserir operação com apenas com uma divisão cadastrada"""
        #investidor = Investidor.objects.get(user__username='teste')
        #investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        self.assertEquals(OperacaoFII.objects.filter(investidor=self.investidor).count(), 0)
        self.assertEquals(DivisaoOperacaoFII.objects.filter(divisao=self.divisao_geral).count(), 0)
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('fii:inserir_operacao_fii'),
                                    {'preco_unitario': 100, 'quantidade': 10, 'data': datetime.date(2018, 11, 9), 'corretagem': 10, 
                                     'emolumentos': Decimal('0.1'), 'tipo_operacao': 'C', 'fii': self.fii.id, 'consolidada': True})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertEquals(OperacaoFII.objects.filter(investidor=self.investidor).count(), 1)
        self.assertEquals(DivisaoOperacaoFII.objects.filter(divisao=self.divisao_geral).count(), 1)
        
    def test_inserir_operacao_multi_divisao_1_div(self):
        """Testa inserir operação com mais de uma divisão cadastrada, mas usando apenas 1"""
        #investidor = Investidor.objects.get(user__username='teste')
        #investimento = Investimento.objects.get(nome='Investimento 1', investidor=investidor)
        nova_divisao = Divisao.objects.create(investidor=self.investidor, nome='Teste')
        
        self.assertEquals(OperacaoFII.objects.filter(investidor=self.investidor).count(), 0)
        self.assertEquals(DivisaoOperacaoFII.objects.filter(divisao=self.divisao_geral).count(), 0)
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('fii:inserir_operacao_fii'),
                                    {'preco_unitario': 100, 'quantidade': 10, 'data': datetime.date(2018, 11, 9), 'corretagem': 10, 
                                     'emolumentos': Decimal('0.1'), 'tipo_operacao': 'C', 'fii': self.fii.id, 'consolidada': True,
                                     'divisaooperacaofii_set-INITIAL_FORMS': '0', 'divisaooperacaofii_set-TOTAL_FORMS': '1',
                                     'divisaooperacaofii_set-0-divisao': self.divisao_geral.id, 'divisaooperacaofii_set-0-quantidade': 10,
                                     'divisaooperacaofii_set-0-qtd_proventos_utilizada': Decimal(0)})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertEquals(OperacaoFII.objects.filter(investidor=self.investidor).count(), 1)
        self.assertEquals(DivisaoOperacaoFII.objects.filter(divisao=self.divisao_geral).count(), 1)
        self.assertEquals(UsoProventosOperacaoFII.objects.filter(divisao_operacao__divisao=self.divisao_geral).count(), 0)
        
    def test_inserir_operacao_multi_divisao_2_div(self):
        """Testa inserir operação com mais de uma divisão cadastrada, usando 2 divisões"""
        nova_divisao = Divisao.objects.create(investidor=self.investidor, nome='Teste')
        
        self.assertEquals(OperacaoFII.objects.filter(investidor=self.investidor).count(), 0)
        self.assertEquals(DivisaoOperacaoFII.objects.filter(divisao=self.divisao_geral).count(), 0)
        
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('fii:inserir_operacao_fii'), 
                                    {'preco_unitario': 100, 'quantidade': 10, 'data': datetime.date(2018, 11, 9), 'corretagem': 10, 
                                     'emolumentos': Decimal('0.1'), 'tipo_operacao': 'C', 'fii': self.fii.id, 'consolidada': True,
                                     'divisaooperacaofii_set-INITIAL_FORMS': '0', 'divisaooperacaofii_set-TOTAL_FORMS': '2',
                                     'divisaooperacaofii_set-0-divisao': self.divisao_geral.id, 'divisaooperacaofii_set-0-quantidade': 5,
                                     'divisaooperacaofii_set-0-qtd_proventos_utilizada': Decimal(0),
                                     'divisaooperacaofii_set-1-divisao': nova_divisao.id, 'divisaooperacaofii_set-1-quantidade': 5,
                                     'divisaooperacaofii_set-1-qtd_proventos_utilizada': Decimal(40)})
        
        # Testar que houve redirecionamento
        self.assertEquals(response.status_code, 302)
        self.assertEquals(OperacaoFII.objects.filter(investidor=self.investidor).count(), 1)
        self.assertEquals(DivisaoOperacaoFII.objects.filter(divisao=self.divisao_geral).count(), 1)
        self.assertEquals(DivisaoOperacaoFII.objects.filter(divisao=nova_divisao).count(), 1)
        self.assertEquals(UsoProventosOperacaoFII.objects.filter(divisao_operacao__divisao=self.divisao_geral).count(), 0)
        self.assertEquals(UsoProventosOperacaoFII.objects.filter(divisao_operacao__divisao=nova_divisao).count(), 1)
        self.assertEquals(UsoProventosOperacaoFII.objects.get(divisao_operacao__divisao=nova_divisao).qtd_utilizada, 40)
        
    def test_inserir_operacao_form_invalido_qtd_div_diferente(self):
        """Testa envio de formulário com mais de uma divisão cadastrada e quantidade das divisões diferente da operação"""
        nova_divisao = Divisao.objects.create(investidor=self.investidor, nome='Teste')
        
        # 2 divisões, quantidade abaixo
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('fii:inserir_operacao_fii'), 
                                    {'preco_unitario': 100, 'quantidade': 10, 'data': datetime.date(2018, 11, 9), 'corretagem': 10, 
                                     'emolumentos': Decimal('0.1'), 'tipo_operacao': 'C', 'fii': self.fii.id, 'consolidada': True,
                                     'divisaooperacaofii_set-INITIAL_FORMS': '0', 'divisaooperacaofii_set-TOTAL_FORMS': '2',
                                     'divisaooperacaofii_set-0-divisao': self.divisao_geral.id, 'divisaooperacaofii_set-0-quantidade': 5,
                                     'divisaooperacaofii_set-0-qtd_proventos_utilizada': Decimal(0),
                                     'divisaooperacaofii_set-1-divisao': nova_divisao.id, 'divisaooperacaofii_set-1-quantidade': 4,
                                     'divisaooperacaofii_set-1-qtd_proventos_utilizada': Decimal(40)})
        
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(response.context_data['formset_divisao'].errors) > 0)
        
        # 2 divisões, quantidade acima
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('fii:inserir_operacao_fii'), 
                                    {'preco_unitario': 100, 'quantidade': 10, 'data': datetime.date(2018, 11, 9), 'corretagem': 10, 
                                     'emolumentos': Decimal('0.1'), 'tipo_operacao': 'C', 'fii': self.fii.id, 'consolidada': True,
                                     'divisaooperacaofii_set-INITIAL_FORMS': '0', 'divisaooperacaofii_set-TOTAL_FORMS': '2',
                                     'divisaooperacaofii_set-0-divisao': self.divisao_geral.id, 'divisaooperacaofii_set-0-quantidade': 5,
                                     'divisaooperacaofii_set-0-qtd_proventos_utilizada': Decimal(0),
                                     'divisaooperacaofii_set-1-divisao': nova_divisao.id, 'divisaooperacaofii_set-1-quantidade': 14,
                                     'divisaooperacaofii_set-1-qtd_proventos_utilizada': Decimal(40)})
        
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(response.context_data['formset_divisao'].errors) > 0)
        
        # 1 divisão, quantidade abaixo
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('fii:inserir_operacao_fii'), 
                                    {'preco_unitario': 100, 'quantidade': 10, 'data': datetime.date(2018, 11, 9), 'corretagem': 10, 
                                     'emolumentos': Decimal('0.1'), 'tipo_operacao': 'C', 'fii': self.fii.id, 'consolidada': True,
                                     'divisaooperacaofii_set-INITIAL_FORMS': '0', 'divisaooperacaofii_set-TOTAL_FORMS': '1',
                                     'divisaooperacaofii_set-0-divisao': self.divisao_geral.id, 'divisaooperacaofii_set-0-quantidade': 4,
                                     'divisaooperacaofii_set-0-qtd_proventos_utilizada': Decimal(0)})
        
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(response.context_data['formset_divisao'].errors) > 0)
        
        # 1 divisão, quantidade acima
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse('fii:inserir_operacao_fii'), 
                                    {'preco_unitario': 100, 'quantidade': 10, 'data': datetime.date(2018, 11, 9), 'corretagem': 10, 
                                     'emolumentos': Decimal('0.1'), 'tipo_operacao': 'C', 'fii': self.fii.id, 'consolidada': True,
                                     'divisaooperacaofii_set-INITIAL_FORMS': '0', 'divisaooperacaofii_set-TOTAL_FORMS': '1',
                                     'divisaooperacaofii_set-0-divisao': self.divisao_geral.id, 'divisaooperacaofii_set-0-quantidade': 12,
                                     'divisaooperacaofii_set-0-qtd_proventos_utilizada': Decimal(0)})
        
        # Testar que não houve redirecionamento
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(response.context_data['formset_divisao'].errors) > 0)
        
        