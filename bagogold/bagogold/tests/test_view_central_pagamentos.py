# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import InvestidorLeituraDocumento, \
    DocumentoProventoBovespa


# class UsuarioDeslogadoTestCase (TestCase):
#     """Caso de teste para usuário deslogado"""
#     def test_usuario_deslogado(self):
#         """Testa o acesso de usuário deslogado"""
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': 1}))
#         self.assertEqual(response.status_code, 302)
#         self.assertTrue('/login/' in response.url)
# 
# class UsuarioInexistenteTestCase (TestCase):
#     """Caso de teste para acesso a usuário inexistente"""
#     def setUp(self):
#         self.user_test = User.objects.create_user('teste', 'teste@teste.com', 'teste')
#         
#         equipe_leitura = Group.objects.create(name='Equipe de leitura')
#         equipe_leitura.user_set.add(self.user_test)
#         
#         permissao = Permission.objects.create(codename='bagogold.pode_gerar_proventos')
#         self.user_test.user_permissions.add(permissao)
#         
#     def test_usuario_inexistente(self):
#         """Testa o acesso a usuário inexistente"""
#         self.client.login(username='teste', password='teste')
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': self.user_test.id+1}))
#         self.assertEqual(response.status_code, 404)
# 
# class UsuarioSemPermissaoTestCase (TestCase):
#     """Caso de teste para acesso de usuários sem as permissões necessárias"""
#     def setUp(self):
#         self.user_test = User.objects.create_user('teste', 'teste@teste.com', 'teste')
#     
#     def test_usuario_sem_permissao_gerar_proventos(self):
#         """Testa situação de usuário que não possui permissão para gerar proventos"""
#         equipe_leitura = Group.objects.create(name='Equipe de leitura')
#         equipe_leitura.user_set.add(self.user_test)
#         
#         self.client.login(username='teste', password='teste')
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': self.user_test.id}))
#         self.assertEqual(response.status_code, 403)
#     
#     def test_usuario_sem_grupo_equipe_leitura(self):
#         """Testa situação de usuário que não está no grupo Equipe de leitura"""
#         permissao = Permission.objects.create(codename='bagogold.pode_gerar_proventos')
#         self.user_test.user_permissions.add(permissao)
#         
#         self.client.login(username='teste', password='teste')
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': self.user_test.id}))
#         self.assertEqual(response.status_code, 403)
#     
# class UsuarioSuperUserTestCase (TestCase):
#     """Testa situações de visualização de super usuário"""
#     def setUp(self):
#         self.nizbel = User.objects.create_superuser('nizbel', 'nizbel@teste.com', 'nizbel')
#         
#         # Criar dados outro usuário
#         self.user_test = User.objects.create_user('teste', 'teste@teste.com', 'teste')
#         
#         equipe_leitura = Group.objects.create(name='Equipe de leitura')
#         equipe_leitura.user_set.add(self.user_test)
#         
#         permissao = Permission.objects.create(codename='bagogold.pode_gerar_proventos')
#         self.user_test.user_permissions.add(permissao)
#     
#     def test_acessar_propria_central(self):
#         """Testa super usuário acessando própria página"""
#         self.client.login(username='nizbel', password='nizbel')
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': self.nizbel.id}))
#         self.assertEqual(response.status_code, 404)
#         
#     def test_acessar_central_de_outro_usuario(self):
#         """Testa super usuário acessando página de outro usuário"""
#         self.client.login(username='nizbel', password='nizbel')
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': self.user_test.id}))
#         self.assertEqual(response.status_code, 200)
#         
# class UsuarioSemLeiturasTestCase (TestCase):
#     """Testa situações de usuários sem leituras cadastradas"""
#     def setUp(self):
#         self.user_test = User.objects.create_user('teste', 'teste@teste.com', 'teste')
#         
#         equipe_leitura = Group.objects.create(name='Equipe de leitura')
#         equipe_leitura.user_set.add(self.user_test)
#         
#         permissao = Permission.objects.create(codename='bagogold.pode_gerar_proventos')
#         self.user_test.user_permissions.add(permissao)
#     
#     def test_usuario_sem_leituras(self):
#         """Testa o acesso de usuário sem leituras"""
#         self.client.login(username='teste', password='teste')
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': self.user_test.id}))
#         self.assertEqual(response.status_code, 200)
#         
#     def test_usuario_fez_1_leitura(self):
#         """Testa o acesso de usuário sem leituras"""
#         self.client.login(username='teste', password='teste')
#         
#         # Adicionar leitura
#         empresa = Empresa.objects.create()
#         documento = DocumentoProventoBovespa.objects.create()
#         InvestidorLeituraDocumento.objects.create(documento=documento, investidor=self.user_test.investidor, data_leitura=datetime.date.today(), decisao='E')
#         
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': self.user_test.id}))
#         self.assertEqual(response.status_code, 200)
#         
# class UsuarioComLeiturasTestCase (TestCase):
#     """Testa situações de usuários com leituras cadastradas"""
#     def setUp(self):
#         self.user_test = User.objects.create_user('teste', 'teste@teste.com', 'teste')
#         
#         equipe_leitura = Group.objects.create(name='Equipe de leitura')
#         equipe_leitura.user_set.add(self.user_test)
#         
#         permissao = Permission.objects.create(codename='bagogold.pode_gerar_proventos')
#         self.user_test.user_permissions.add(permissao)
#         
#     def test_usuario_com_leituras(self):
#         """Testa o acesso de usuário com leituras"""
#         self.client.login(username='teste', password='teste')
#         response = self.client.get(reverse('gerador_proventos:central_pagamentos', kwargs={'id_usuario': self.user_test.id}))
#         self.assertEqual(response.status_code, 200)

# class AcompanhamentoFIITestCase (TestCase):
#     def setUp(self):
#         nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
#         
#         empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
#         
#         # FII sem histórico sem proventos
#         fii_1 = FII.objects.create(ticker='TEST11', empresa=empresa)
#         # FII com histórico com proventos
#         fii_2 = FII.objects.create(ticker='TSTE11', empresa=empresa)
#         # FII sem histórico com proventos
#         fii_3 = FII.objects.create(ticker='TSTT11', empresa=empresa)
#         # FII com histórico sem proventos
#         fii_4 = FII.objects.create(ticker='TSST11', empresa=empresa)
#         
#         for data in [datetime.date.today() - datetime.timedelta(days=x) for x in range(365)]:
#             if data >= datetime.date.today() - datetime.timedelta(days=3):
#                 HistoricoFII.objects.create(fii=fii_2, preco_unitario=1200, data=data)
#                 HistoricoFII.objects.create(fii=fii_4, preco_unitario=1200, data=data)
#             else:
#                 HistoricoFII.objects.create(fii=fii_2, preco_unitario=120, data=data)
#                 HistoricoFII.objects.create(fii=fii_4, preco_unitario=120, data=data)
#                 
#         for data in [datetime.date.today() - datetime.timedelta(days=30*x) for x in range(1, 7)]:
#             ProventoFII.objects.create(fii=fii_2, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
#                                        oficial_bovespa=True)
#             ProventoFII.objects.create(fii=fii_3, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
#                                        oficial_bovespa=True)
#                                        
#     def test_usuario_deslogado(self):
#         """Testa o acesso de usuário deslogado"""
#         response = self.client.get(reverse('fii:acompanhamento_fii'))
#         self.assertEqual(response.status_code, 200)
#         
#         # TODO testar contexto
#         
#     def test_usuario_logado(self):
#         """Testa o acesso de usuário logado"""
#         self.client.login(username='nizbel', password='nizbel')
#         
#         response = self.client.get(reverse('fii:acompanhamento_fii'))
#         self.assertEqual(response.status_code, 200)
#         
#         # TODO testar contexto
#         
#     def test_filtros(self):
#         """Testa os filtros da pesquisa"""
#         pass
# 
# class DetalharFIITestCase (TestCase):
#     def setUp(self):
#         nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
#         user_vendido = User.objects.create_user('vendido', 'vendido@teste.com', 'vendido')
# 
#         empresa = Empresa.objects.create(nome='Teste', nome_pregao='TEST')
#         
#         fii_1 = FII.objects.create(ticker='TEST11', empresa=empresa)
#         fii_2 = FII.objects.create(ticker='TSTE11', empresa=empresa)
#         
#         for data in [datetime.date.today() - datetime.timedelta(days=x) for x in range(365)]:
#             if data >= datetime.date.today() - datetime.timedelta(days=3):
#                 HistoricoFII.objects.create(fii=fii_2, preco_unitario=1200, data=data)
#             else:
#                 HistoricoFII.objects.create(fii=fii_2, preco_unitario=120, data=data)
#         
#         for data in [datetime.date.today() - datetime.timedelta(days=30*x) for x in range(1, 7)]:
#             ProventoFII.objects.create(fii=fii_2, valor_unitario=Decimal('0.9'), data_ex=data, data_pagamento=data+datetime.timedelta(days=7),
#                                        oficial_bovespa=True)
#         
#         EventoAgrupamentoFII.objects.create(fii=fii_2, data=datetime.date.today() - datetime.timedelta(days=3), proporcao=Decimal('0.1'))
#         
#         OperacaoFII.objects.create(fii=fii_2, investidor=nizbel.investidor, data=datetime.date.today() - datetime.timedelta(days=130),
#                                    quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
#         OperacaoFII.objects.create(fii=fii_2, investidor=nizbel.investidor, data=datetime.date.today() - datetime.timedelta(days=80),
#                                    quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
#         
#         OperacaoFII.objects.create(fii=fii_2, investidor=user_vendido.investidor, data=datetime.date.today() - datetime.timedelta(days=130),
#                                    quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='C')
#         OperacaoFII.objects.create(fii=fii_2, investidor=user_vendido.investidor, data=datetime.date.today() - datetime.timedelta(days=80),
#                                    quantidade=5, preco_unitario=120, corretagem=10, emolumentos=Decimal('0.1'), tipo_operacao='V')
#     
#     def test_usuario_deslogado_fii_vazio(self):
#         """Testa o acesso a view para um fii sem infos com um usuário deslogado"""
#         response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TEST11'}))
#         self.assertEqual(response.status_code, 200)
#         
#         # Verificar contexto
#         self.assertEqual(len(response.context_data['operacoes']), 0)
#         self.assertEqual(len(response.context_data['historico']), 0)
#         self.assertEqual(len(response.context_data['proventos']), 0)
#         self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TEST11'))
#         
#     def test_usuario_logado_fii_vazio(self):
#         """Testa o acesso a view para um fii sem infos com um usuário logado"""
#         self.client.login(username='nizbel', password='nizbel')
#         
#         response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TEST11'}))
#         self.assertEqual(response.status_code, 200)
#         
#         # Verificar contexto
#         self.assertEqual(len(response.context_data['operacoes']), 0)
#         self.assertEqual(len(response.context_data['historico']), 0)
#         self.assertEqual(len(response.context_data['proventos']), 0)
#         self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TEST11'))
#         
#     def test_usuario_deslogado_fii_com_infos(self):
#         """Testa o acesso a view para um fii com infos com um usuário deslogado"""
#         response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTE11'}))
#         
#         self.assertEqual(response.status_code, 200)
#         
#         # Verificar contexto
#         self.assertEqual(len(response.context_data['operacoes']), 0)
#         self.assertEqual(len(response.context_data['historico']), 365)
#         self.assertEqual(len(response.context_data['proventos']), 6)
#         self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TSTE11'))
#         
#     def test_usuario_logado_fii_com_infos(self):
#         """Testa o acesso a view para um fii com infos com um usuário logado"""
#         self.client.login(username='nizbel', password='nizbel')
# 
#         response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTE11'}))      
#         self.assertEqual(response.status_code, 200)
#         
#         # Verificar contexto
#         self.assertEqual(len(response.context_data['operacoes']), 2)
#         self.assertEqual(len(response.context_data['historico']), 365)
#         self.assertEqual(len(response.context_data['proventos']), 6)
#         self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TSTE11'))
#         # Quantidade de cotas atual é 1 devido ao agrupamento
#         self.assertEqual(response.context_data['fii'].qtd_cotas, 1)
#         
#         
#     def test_usuario_logado_fii_com_infos_vendido(self):
#         """Testa o acesso a view para um fii com infos com um usuário logado, que já tinha liquidado sua posição"""
#         self.client.login(username='vendido', password='vendido')
# 
#         response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTE11'}))      
#         self.assertEqual(response.status_code, 200)
#         
#         # Verificar contexto
#         self.assertEqual(len(response.context_data['operacoes']), 2)
#         self.assertEqual(len(response.context_data['historico']), 365)
#         self.assertEqual(len(response.context_data['proventos']), 6)
#         self.assertEqual(response.context_data['fii'], FII.objects.get(ticker='TSTE11'))
#         self.assertEqual(response.context_data['fii'].qtd_cotas, 0)
#         
#     def test_fii_nao_encontrado(self):
#         """Testa o retorno caso o FII não seja encontrado"""
#         response = self.client.get(reverse('fii:detalhar_fii', kwargs={'fii_ticker': 'TSTS11'}))      
#         self.assertEqual(response.status_code, 404)
        