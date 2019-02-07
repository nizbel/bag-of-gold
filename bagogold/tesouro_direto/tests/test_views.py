# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from bagogold.tesouro_direto.models import Titulo, HistoricoTitulo, \
    OperacaoTitulo
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD


class DetalharTituloTestCase(TestCase):
    def setUp(self):
        # Criar títulos
        criar_titulos_teste()
        
        # Preparar históricos (cada título já é criado com histórico)
        for titulo in Titulo.objects.all():
            HistoricoTitulo.objects.create(titulo=titulo, data=titulo.data_inicio, taxa_compra=10,
                                           taxa_venda=9, preco_compra=700, preco_venda=650)
            HistoricoTitulo.objects.create(titulo=titulo, data=min(datetime.date.today(), titulo.data_vencimento - datetime.timedelta(days=1)), 
                                           taxa_compra=10, taxa_venda=9, preco_compra=800, preco_venda=750)
        
    def test_detalhar_titulo_por_id(self):
        """Testa detalhar título por ID"""
        for titulo in Titulo.objects.all():
            response = self.client.get(reverse('tesouro_direto:detalhar_titulo_td_id', kwargs={'titulo_id': titulo.id}))
            self.assertEqual(response.status_code, 301)
    
    def test_detalhar_titulo_por_slug(self):
        """Testa detalhar título por slug"""
        for titulo in Titulo.objects.all():
            titulo.slug = Titulo.codificar_slug(titulo.tipo)
            response = self.client.get(reverse('tesouro_direto:detalhar_titulo_td', kwargs={'titulo_tipo': titulo.slug,
                                                                                            'titulo_data': titulo.data_vencimento.strftime('%d-%m-%Y')}))
            self.assertEqual(response.status_code, 200, msg=u'Falhou para %s na URL %s' % \
                             (titulo, reverse('tesouro_direto:detalhar_titulo_td', kwargs={'titulo_tipo': titulo.slug,
                                                                                           'titulo_data': titulo.data_vencimento.strftime('%d-%m-%Y')})))
    
def criar_titulos_teste():
    Titulo.objects.create(data_vencimento=datetime.date(2015, 3, 7), tipo=u'LFT', data_inicio=datetime.date(2010, 3, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2017, 3, 7), tipo=u'LFT', data_inicio=datetime.date(2011, 1, 3))
    Titulo.objects.create(data_vencimento=datetime.date(2021, 3, 1), tipo=u'LFT', data_inicio=datetime.date(2015, 3, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2016, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2012, 2, 1))
    Titulo.objects.create(data_vencimento=datetime.date(2017, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2013, 1, 14))
    Titulo.objects.create(data_vencimento=datetime.date(2018, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2014, 1, 27))
    Titulo.objects.create(data_vencimento=datetime.date(2021, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2015, 3, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2017, 7, 1), tipo=u'NTN-C', data_inicio=datetime.date(2002, 5, 2))
    Titulo.objects.create(data_vencimento=datetime.date(2021, 4, 1), tipo=u'NTN-C', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2031, 1, 1), tipo=u'NTN-C', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2015, 5, 15), tipo=u'NTN-B', data_inicio=datetime.date(2003, 10, 21))
    Titulo.objects.create(data_vencimento=datetime.date(2017, 5, 15), tipo=u'NTN-B', data_inicio=datetime.date(2007, 5, 25))
    Titulo.objects.create(data_vencimento=datetime.date(2020, 8, 15), tipo=u'NTN-B', data_inicio=datetime.date(2009, 3, 2))
    Titulo.objects.create(data_vencimento=datetime.date(2024, 8, 15), tipo=u'NTN-B', data_inicio=datetime.date(2003, 10, 21))
    Titulo.objects.create(data_vencimento=datetime.date(2035, 5, 15), tipo=u'NTN-B', data_inicio=datetime.date(2006, 4, 12))
    Titulo.objects.create(data_vencimento=datetime.date(2045, 5, 15), tipo=u'NTN-B', data_inicio=datetime.date(2004, 9, 20))
    Titulo.objects.create(data_vencimento=datetime.date(2050, 8, 15), tipo=u'NTN-B', data_inicio=datetime.date(2012, 6, 1))
    Titulo.objects.create(data_vencimento=datetime.date(2015, 5, 15), tipo=u'NTN-B Principal', data_inicio=datetime.date(2005, 8, 11))
    Titulo.objects.create(data_vencimento=datetime.date(2019, 5, 15), tipo=u'NTN-B Principal', data_inicio=datetime.date(2013, 1, 14))
    Titulo.objects.create(data_vencimento=datetime.date(2024, 8, 15), tipo=u'NTN-B Principal', data_inicio=datetime.date(2005, 8, 11))
    Titulo.objects.create(data_vencimento=datetime.date(2035, 5, 15), tipo=u'NTN-B Principal', data_inicio=datetime.date(2010, 3, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2017, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2007, 2, 16))
    Titulo.objects.create(data_vencimento=datetime.date(2021, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2010, 3, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2023, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2012, 6, 1))
    Titulo.objects.create(data_vencimento=datetime.date(2025, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2014, 1, 27))
    Titulo.objects.create(data_vencimento=datetime.date(2014, 3, 7), tipo=u'LFT', data_inicio=datetime.date(2008, 2, 22))
    Titulo.objects.create(data_vencimento=datetime.date(2015, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2011, 1, 3))
    Titulo.objects.create(data_vencimento=datetime.date(2013, 3, 7), tipo=u'LFT', data_inicio=datetime.date(2007, 8, 3))
    Titulo.objects.create(data_vencimento=datetime.date(2014, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2011, 1, 3))
    Titulo.objects.create(data_vencimento=datetime.date(2013, 5, 15), tipo=u'NTN-B', data_inicio=datetime.date(2008, 1, 30))
    Titulo.objects.create(data_vencimento=datetime.date(2014, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2006, 10, 5))
    Titulo.objects.create(data_vencimento=datetime.date(2012, 3, 7), tipo=u'LFT', data_inicio=datetime.date(2006, 11, 13))
    Titulo.objects.create(data_vencimento=datetime.date(2013, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2010, 1, 4))
    Titulo.objects.create(data_vencimento=datetime.date(2012, 8, 15), tipo=u'NTN-B', data_inicio=datetime.date(2007, 5, 25))
    Titulo.objects.create(data_vencimento=datetime.date(2013, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2007, 7, 13))
    Titulo.objects.create(data_vencimento=datetime.date(2011, 3, 16), tipo=u'LFT', data_inicio=datetime.date(2006, 6, 9))
    Titulo.objects.create(data_vencimento=datetime.date(2011, 7, 1), tipo=u'LTN', data_inicio=datetime.date(2010, 7, 5))
    Titulo.objects.create(data_vencimento=datetime.date(2012, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2009, 3, 2))
    Titulo.objects.create(data_vencimento=datetime.date(2011, 3, 1), tipo=u'NTN-C', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2011, 5, 15), tipo=u'NTN-B', data_inicio=datetime.date(2006, 3, 14))
    Titulo.objects.create(data_vencimento=datetime.date(2012, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2006, 5, 12))
    Titulo.objects.create(data_vencimento=datetime.date(2010, 3, 17), tipo=u'LFT', data_inicio=datetime.date(2005, 11, 16))
    Titulo.objects.create(data_vencimento=datetime.date(2010, 7, 1), tipo=u'LTN', data_inicio=datetime.date(2008, 3, 20))
    Titulo.objects.create(data_vencimento=datetime.date(2011, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2008, 11, 28))
    Titulo.objects.create(data_vencimento=datetime.date(2010, 8, 15), tipo=u'NTN-B', data_inicio=datetime.date(2006, 1, 18))
    Titulo.objects.create(data_vencimento=datetime.date(2010, 7, 1), tipo=u'NTN-F', data_inicio=datetime.date(2007, 2, 16))
    Titulo.objects.create(data_vencimento=datetime.date(2011, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2007, 7, 13))
    Titulo.objects.create(data_vencimento=datetime.date(2009, 3, 18), tipo=u'LFT', data_inicio=datetime.date(2004, 1, 21))
    Titulo.objects.create(data_vencimento=datetime.date(2009, 4, 1), tipo=u'LTN', data_inicio=datetime.date(2008, 3, 20))
    Titulo.objects.create(data_vencimento=datetime.date(2009, 7, 1), tipo=u'LTN', data_inicio=datetime.date(2007, 4, 23))
    Titulo.objects.create(data_vencimento=datetime.date(2009, 10, 1), tipo=u'LTN', data_inicio=datetime.date(2007, 7, 13))
    Titulo.objects.create(data_vencimento=datetime.date(2010, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2007, 10, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2009, 5, 15), tipo=u'NTN-B', data_inicio=datetime.date(2003, 9, 12))
    Titulo.objects.create(data_vencimento=datetime.date(2010, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2005, 11, 1))
    Titulo.objects.create(data_vencimento=datetime.date(2008, 6, 18), tipo=u'LFT', data_inicio=datetime.date(2003, 11, 13))
    Titulo.objects.create(data_vencimento=datetime.date(2008, 4, 1), tipo=u'LTN', data_inicio=datetime.date(2006, 8, 11))
    Titulo.objects.create(data_vencimento=datetime.date(2008, 7, 1), tipo=u'LTN', data_inicio=datetime.date(2005, 12, 15))
    Titulo.objects.create(data_vencimento=datetime.date(2008, 10, 1), tipo=u'LTN', data_inicio=datetime.date(2007, 6, 14))
    Titulo.objects.create(data_vencimento=datetime.date(2009, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2006, 5, 12))
    Titulo.objects.create(data_vencimento=datetime.date(2008, 4, 1), tipo=u'NTN-C', data_inicio=datetime.date(2002, 4, 1))
    Titulo.objects.create(data_vencimento=datetime.date(2008, 8, 15), tipo=u'NTN-B', data_inicio=datetime.date(2005, 9, 27))
    Titulo.objects.create(data_vencimento=datetime.date(2007, 1, 17), tipo=u'LFT', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2007, 4, 1), tipo=u'LTN', data_inicio=datetime.date(2005, 10, 3))
    Titulo.objects.create(data_vencimento=datetime.date(2007, 7, 1), tipo=u'LTN', data_inicio=datetime.date(2005, 6, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2007, 10, 1), tipo=u'LTN', data_inicio=datetime.date(2006, 2, 22))
    Titulo.objects.create(data_vencimento=datetime.date(2008, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2005, 7, 27))
    Titulo.objects.create(data_vencimento=datetime.date(2007, 5, 15), tipo=u'NTN-B', data_inicio=datetime.date(2005, 7, 1))
    Titulo.objects.create(data_vencimento=datetime.date(2008, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2004, 1, 6))
    Titulo.objects.create(data_vencimento=datetime.date(2006, 1, 18), tipo=u'LFT', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2006, 4, 1), tipo=u'LTN', data_inicio=datetime.date(2005, 2, 21))
    Titulo.objects.create(data_vencimento=datetime.date(2006, 7, 1), tipo=u'LTN', data_inicio=datetime.date(2004, 11, 4))
    Titulo.objects.create(data_vencimento=datetime.date(2006, 10, 1), tipo=u'LTN', data_inicio=datetime.date(2005, 6, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2007, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2005, 2, 21))
    Titulo.objects.create(data_vencimento=datetime.date(2006, 12, 1), tipo=u'NTN-C', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2006, 8, 15), tipo=u'NTN-B', data_inicio=datetime.date(2003, 9, 12))
    Titulo.objects.create(data_vencimento=datetime.date(2005, 2, 16), tipo=u'LFT', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2005, 1, 4), tipo=u'LTN', data_inicio=datetime.date(2003, 8, 22))
    Titulo.objects.create(data_vencimento=datetime.date(2005, 4, 1), tipo=u'LTN', data_inicio=datetime.date(2004, 3, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2005, 7, 1), tipo=u'LTN', data_inicio=datetime.date(2003, 11, 4))
    Titulo.objects.create(data_vencimento=datetime.date(2005, 10, 1), tipo=u'LTN', data_inicio=datetime.date(2004, 11, 4))
    Titulo.objects.create(data_vencimento=datetime.date(2006, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2004, 3, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2005, 7, 1), tipo=u'NTN-C', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2005, 12, 1), tipo=u'NTN-C', data_inicio=datetime.date(2002, 10, 4))
    Titulo.objects.create(data_vencimento=datetime.date(2004, 1, 21), tipo=u'LFT', data_inicio=datetime.date(2002, 1, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2004, 1, 7), tipo=u'LTN', data_inicio=datetime.date(2002, 3, 18))
    Titulo.objects.create(data_vencimento=datetime.date(2004, 4, 1), tipo=u'LTN', data_inicio=datetime.date(2003, 6, 11))
    Titulo.objects.create(data_vencimento=datetime.date(2004, 7, 1), tipo=u'LTN', data_inicio=datetime.date(2003, 4, 10))
    Titulo.objects.create(data_vencimento=datetime.date(2004, 10, 1), tipo=u'LTN', data_inicio=datetime.date(2003, 6, 11))
    Titulo.objects.create(data_vencimento=datetime.date(2003, 10, 1), tipo=u'LTN', data_inicio=datetime.date(2003, 2, 26))
    Titulo.objects.create(data_vencimento=datetime.date(2019, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2016, 1, 26))
    Titulo.objects.create(data_vencimento=datetime.date(2023, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2016, 1, 26))
    Titulo.objects.create(data_vencimento=datetime.date(2026, 8, 15), tipo=u'NTN-B', data_inicio=datetime.date(2016, 1, 26))
    Titulo.objects.create(data_vencimento=datetime.date(2027, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2016, 1, 26))
    Titulo.objects.create(data_vencimento=datetime.date(2025, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2018, 2, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2029, 1, 1), tipo=u'NTN-F', data_inicio=datetime.date(2018, 2, 7))
    Titulo.objects.create(data_vencimento=datetime.date(2023, 3, 1), tipo=u'LFT', data_inicio=datetime.date(2017, 2, 8))
    Titulo.objects.create(data_vencimento=datetime.date(2020, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2017, 2, 8))
    Titulo.objects.create(data_vencimento=datetime.date(2045, 5, 15), tipo=u'NTN-B Principal', data_inicio=datetime.date(2017, 2, 8))
    
class ViewInserirOperacaoTDTestCase(TestCase):
    """Testa a view inserir_operacao_td"""
    def setUp(self):
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        self.investidor = nizbel.investidor
        
        multi_divisoes = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        self.investidor_multi_div = multi_divisoes.investidor
        
        # Criar título
        self.titulo = Titulo.objects.create(data_vencimento=datetime.date(2025, 1, 1), tipo=u'LTN', data_inicio=datetime.date(2018, 2, 7))
        
        self.url_inserir_operacao = 'tesouro_direto:inserir_operacao_td'
    
    def test_acesso_usuario_deslogado(self):
        """Testa redirecionamento para tela de login caso usuário não esteja logado"""
        response = self.client.get(reverse(self.url_inserir_operacao))
        self.assertEquals(response.status_code, 302)
        self.assertTrue('/login/' in response.url)
        
    def test_acesso_usuario_logado_1_div(self):
        """Testa acesso de usuário logado com 1 divisão"""        
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.get(reverse(self.url_inserir_operacao))
        self.assertEquals(response.status_code, 200)
        
    def test_acesso_usuario_logado_multi_div(self):
        """Testa acesso de usuário logado com várias divisões"""        
        self.client.login(username='teste', password='teste')
        response = self.client.get(reverse(self.url_inserir_operacao))
        self.assertEquals(response.status_code, 200)
    
    def test_inserir_operacao_compra_1_div(self):
        """Testa inserir uma operação de compra com sucesso, investidor com 1 divisão"""
        self.client.login(username='nizbel', password='nizbel')
        
        self.assertEquals(OperacaoTitulo.objects.all().count(), 0)
        self.assertEquals(DivisaoOperacaoTD.objects.all().count(), 0)
        
        response = self.client.post(reverse(self.url_inserir_operacao),
                                    {'preco_unitario': 700, 'quantidade': 1, 'data': datetime.date(2018, 11, 9), 'taxa_bvmf': Decimal('0.1'), 
                                     'taxa_custodia': Decimal('0.1'), 'tipo_operacao': 'C', 'titulo': self.titulo.id, 'consolidada': True})
        
        self.assertEquals(response.status_code, 302)
        self.assertEquals(OperacaoTitulo.objects.all().count(), 1)
        
        operacao = OperacaoTitulo.objects.get(investidor=self.investidor)
        self.assertEquals(operacao.preco_unitario, 700)
        self.assertEquals(operacao.quantidade, 1)
        self.assertEquals(operacao.data, datetime.date(2018, 11, 9))
        self.assertEquals(operacao.taxa_bvmf, Decimal('0.1'))
        self.assertEquals(operacao.taxa_custodia, Decimal('0.1'))
        self.assertEquals(operacao.tipo_operacao, 'C')
        self.assertEquals(operacao.titulo, self.titulo)
        self.assertEquals(operacao.consolidada, True)
        
        # TODO testar operacao divisao
        
        
                                     
    
    def test_inserir_operacao_compra_multi_div(self):
        """Testa inserir uma operação de compra com sucesso, investidor com várias divisão"""
        self.client.login(username='teste', password='teste')
        
        self.assertEquals(OperacaoTitulo.objects.all().count(), 0)
        self.assertEquals(DivisaoOperacaoTD.objects.all().count(), 0)
        
        response = self.client.post(reverse(self.url_inserir_operacao),
                                    {'preco_unitario': 700, 'quantidade': 1, 'data': datetime.date(2018, 11, 9), 'taxa_bvmf': Decimal('0.1'), 
                                     'taxa_custodia': Decimal('0.1'), 'tipo_operacao': 'C', 'titulo': self.titulo.id, 'consolidada': True})
        
        self.assertEquals(response.status_code, 302)
        self.assertEquals(OperacaoTitulo.objects.all().count(), 1)
        
        operacao = OperacaoTitulo.objects.get(investidor=self.investidor_multi_div)
        self.assertEquals(operacao.preco_unitario, 700)
        self.assertEquals(operacao.quantidade, 1)
        self.assertEquals(operacao.data, datetime.date(2018, 11, 9))
        self.assertEquals(operacao.taxa_bvmf, Decimal('0.1'))
        self.assertEquals(operacao.taxa_custodia, Decimal('0.1'))
        self.assertEquals(operacao.tipo_operacao, 'C')
        self.assertEquals(operacao.titulo, self.titulo)
        self.assertEquals(operacao.consolidada, True)
    
    def test_inserir_operacao_venda_1_div(self):
        """Testa inserir uma operação de venda com sucesso, investidor com 1 divisões"""
        OperacaoTitulo.objects.create(investidor=self.investidor, preco_unitario=700, quantidade=1, data=datetime.date(2018, 11, 2), taxa_bvmf=Decimal('0.1'), 
                                     taxa_custodia=Decimal('0.1'), tipo_operacao='C', titulo=self.titulo, consolidada=True)
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.post(reverse(self.url_inserir_operacao),
                                    {'preco_unitario': 900, 'quantidade': 1, 'data': datetime.date(2018, 11, 9), 'taxa_bvmf': Decimal('0.1'), 
                                     'taxa_custodia': Decimal('0.1'), 'tipo_operacao': 'V', 'titulo': self.titulo.id, 'consolidada': True})
                                     
        self.assertEquals(response.status_code, 302)
        self.assertEquals(OperacaoTitulo.objects.all().count(), 2)
        
    def test_inserir_operacao_venda_1_sem_compras(self):
        """Testa inserir uma operação de venda com erro, sem quantidade do título comprada anteriormente, investidor com 1 divisões"""
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.post(reverse(self.url_inserir_operacao),
                                    {'preco_unitario': 900, 'quantidade': 1, 'data': datetime.date(2018, 11, 9), 'taxa_bvmf': Decimal('0.1'), 
                                     'taxa_custodia': Decimal('0.1'), 'tipo_operacao': 'V', 'titulo': self.titulo.id, 'consolidada': True})
    
        self.assertEquals(response.status_code, 200)
        self.assertEquals(OperacaoTitulo.objects.all().count(), 0)
        # TODO testar erros
        
    def test_inserir_operacao_venda_multi_div(self):
        """Testa inserir uma operação de venda com sucesso, investidor com várias divisões"""
        OperacaoTitulo.objects.create(investidor=self.investidor_multi_div, preco_unitario=700, quantidade=1, data=datetime.date(2018, 11, 2), taxa_bvmf=Decimal('0.1'), 
                                     taxa_custodia=Decimal('0.1'), tipo_operacao='C', titulo=self.titulo, consolidada=True)
        self.client.login(username='teste', password='teste')
        response = self.client.post(reverse(self.url_inserir_operacao),
                                    {'preco_unitario': 900, 'quantidade': 1, 'data': datetime.date(2018, 11, 9), 'taxa_bvmf': Decimal('0.1'), 
                                     'taxa_custodia': Decimal('0.1'), 'tipo_operacao': 'V', 'titulo': self.titulo.id, 'consolidada': True})
        
        self.assertEquals(response.status_code, 302)
        self.assertEquals(OperacaoTitulo.objects.all().count(), 2)
        