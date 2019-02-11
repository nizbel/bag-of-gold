# -*- coding: utf-8 -*-
from bagogold.fundo_investimento.models import FundoInvestimento, Administrador
from bagogold.fundo_investimento.utils import \
    criar_slug_fundo_investimento_valido
from django.test import TestCase
import datetime

class TestSlugTest(TestCase):
    def setUp(self):
        administrador = Administrador.objects.create(nome='Administrador', cnpj='123.123/0004-12')

    def test_gerar_slug_valido(self):
        """Testa se gerando slug válido para todas as ocorrências de nome, não há nenhuma colisão"""
        administrador = Administrador.objects.get(nome='Administrador')
        
        with open('bagogold/fundo_investimento/tests/test_slug.txt', 'r') as lista_nomes:  
            line = lista_nomes.readline()
            cnt = 1
            while line:
                nome = line[line.find('"')+1 : line.rfind('"')]
                cnpj = str(cnt).rjust(10, '0')
                slug = criar_slug_fundo_investimento_valido(nome)
#                 print slug, nome
                FundoInvestimento.objects.create(nome=nome, cnpj=cnpj, administrador=administrador, data_constituicao=datetime.date(2018, 2, 9),
                                                 situacao=FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL, tipo_prazo=FundoInvestimento.PRAZO_LONGO,
                                                 classe=FundoInvestimento.CLASSE_FUNDO_ACOES, exclusivo_qualificados=False, 
                                                 data_registro=datetime.date(2018, 2, 9), slug=slug)
                
                line = lista_nomes.readline()
                cnt += 1
        
        self.assertFalse(FundoInvestimento.objects.filter(slug__startswith='-').exists())
        self.assertFalse(FundoInvestimento.objects.filter(slug__endswith='-').exists())
        self.assertFalse(FundoInvestimento.objects.filter(slug__contains='--').exists())