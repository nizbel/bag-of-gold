# -*- coding: utf-8 -*-
import datetime
import re
from urllib2 import Request, urlopen

from django.core.management import call_command
from django.test import TestCase

from bagogold.tesouro_direto.models import Titulo, HistoricoTitulo, \
    ValorDiarioTitulo


class ComandoPreencherHistoricoAnoAtualTDTestCase(TestCase):
    def test_comando(self):
        """Testa comando de preencher histórico para ano atual de Tesouro Direto"""

        args = []
        opts = {'test': True}
        # Roda uma vez para preencher a tabela e outra para verificar o que foi inserido
        call_command('preencher_historico_ano_atual_td', *args, **opts)
        call_command('preencher_historico_ano_atual_td', *args, **opts)

        self.assertTrue(Titulo.objects.all().exists())
        self.assertTrue(HistoricoTitulo.objects.all().exists())
        
class ComandoPreencherValoresDiariosTDTestCase(TestCase):
    def setUp(self):
        self.assertTrue(Titulo.objects.all().exists())
    
    @classmethod
    def setUpTestData(cls):
        super(ComandoPreencherValoresDiariosTDTestCase, cls).setUpTestData()
        # Popular títulos
        td_url = 'http://www.tesouro.fazenda.gov.br/tesouro-direto-precos-e-taxas-dos-titulos'
        req = Request(td_url)
        response = urlopen(req)
        data = response.read()
        string_importante = data[data.find('mercadostatus'):
                                 data.find('Descubra o título mais indicado para você')]
        string_compra = string_importante[:string_importante.rfind('mercadostatus')]
        linhas = re.findall('<tr class="[^"]*?camposTesouroDireto[^"]*?">.*?</tr>', string_compra, re.DOTALL)
        contador = 0
        for linha in linhas:
            campos = re.findall('<td.*?>.*?</td>', linha)
            tipo_titulo = ''
#             print campos
            for campo in campos:
                # Parte importante da coluna para o preenchimento dos valores
                dado = re.sub(r'<.*?>', "", campo).strip()
#                 print dado
                if contador == 0:
                    tipo_titulo = re.sub(r'\d', '', dado).strip()
#                     print tipo_titulo
                    tipo_titulo = tipo_titulo.replace('(', '').replace(')', '')
                elif contador == 1:
                    data_formatada = datetime.datetime.strptime(dado, "%d/%m/%Y")
                    Titulo.objects.update_or_create(tipo=Titulo.buscar_vinculo_oficial(tipo_titulo), data_vencimento=data_formatada, 
                                          data_inicio=(data_formatada - datetime.timedelta(days=730)))
                # Garante o posicionamento
                contador += 1
                if contador == 5:
                    contador = 0
                    
        string_venda = string_importante[string_importante.rfind('mercadostatus'):]
        linhas = re.findall('<tr class="[^"]*?camposTesouroDireto[^"]*?">.*?</tr>', string_venda, re.DOTALL)
        contador = 0
        for linha in linhas:
            campos = re.findall('<td.*?>.*?</td>', linha)
            tipo_titulo = ''
            for campo in campos:
                # Parte importante da coluna para o preenchimento dos valores
                dado = re.sub(r'<.*?>', "", campo).strip()
#                 print dado
                if contador == 0:
                    tipo_titulo = re.sub(r'\d', '', dado).strip()
#                     print tipo_titulo
                    tipo_titulo = tipo_titulo.replace('(', '').replace(')', '')
                elif contador == 1:
                    data_formatada = datetime.datetime.strptime(dado, "%d/%m/%Y")
                    Titulo.objects.update_or_create(tipo=Titulo.buscar_vinculo_oficial(tipo_titulo), data_vencimento=data_formatada, 
                                          data_inicio=(data_formatada - datetime.timedelta(days=730)))
                # Garante o posicionamento
                contador += 1
                if contador == 4:
                    contador = 0
        
    def test_comando_sucesso(self):
        """Testa comando de preencher valores diários para Tesouro Direto"""
        
        args = []
        opts = {'test': True}

        self.assertFalse(ValorDiarioTitulo.objects.all().exists())
        
        call_command('preencher_valores_diarios_td', *args, **opts)
        
        self.assertTrue(ValorDiarioTitulo.objects.all().exists())
        
    def test_comando_valores_duplicados(self):
        """Testa comando buscando mesmos valores"""
        
        args = []
        opts = {'test': True}
        self.assertFalse(ValorDiarioTitulo.objects.all().exists())
        
        # Roda 2 vezes para replicar caso de erro em que valores diários são duplicados
        call_command('preencher_valores_diarios_td', *args, **opts)
        call_command('preencher_valores_diarios_td', *args, **opts)
        
        self.assertTrue(ValorDiarioTitulo.objects.all().exists())
    