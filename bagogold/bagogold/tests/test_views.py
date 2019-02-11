# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls.base import reverse

from bagogold.bagogold.models.acoes import Acao, OperacaoAcao, HistoricoAcao
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLCI_LCA, Divisao, \
    DivisaoOperacaoCDB_RDB, DivisaoOperacaoFII, DivisaoOperacaoCRI_CRA, \
    DivisaoOperacaoLetraCambio, DivisaoOperacaoAcao, DivisaoOperacaoDebenture, \
    DivisaoOperacaoFundoInvestimento, DivisaoOperacaoTD
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.misc import verifica_se_dia_util
from bagogold.cdb_rdb.models import CDB_RDB, HistoricoPorcentagemCDB_RDB, \
    HistoricoCarenciaCDB_RDB, HistoricoVencimentoCDB_RDB, OperacaoCDB_RDB, \
    OperacaoVendaCDB_RDB
from bagogold.cri_cra.models.cri_cra import CRI_CRA, OperacaoCRI_CRA
from bagogold.debentures.models import Debenture, OperacaoDebenture, \
    HistoricoValorDebenture
from bagogold.fii.models import FII, OperacaoFII, HistoricoFII
from bagogold.fundo_investimento.models import FundoInvestimento, \
    OperacaoFundoInvestimento, HistoricoValorCotas
from bagogold.fundo_investimento.utils import criar_slug_fundo_investimento_valido
from bagogold.lc.models import LetraCambio, HistoricoPorcentagemLetraCambio, \
    HistoricoCarenciaLetraCambio, HistoricoVencimentoLetraCambio, \
    OperacaoLetraCambio, OperacaoVendaLetraCambio
from bagogold.lci_lca.models import LetraCredito, \
    HistoricoPorcentagemLetraCredito, HistoricoCarenciaLetraCredito, \
    HistoricoVencimentoLetraCredito, OperacaoLetraCredito, \
    OperacaoVendaLetraCredito
from bagogold.tesouro_direto.models import Titulo, OperacaoTitulo,\
    HistoricoTitulo


class ProxVencimentosPainelGeralTestCase(TestCase):
    def setUp(self):
        HistoricoTaxaDI.objects.create(data=datetime.date.today(), taxa=10)
    
    def test_investidor_deslogado(self):
        """Testa investidor deslogado"""
        response = self.client.get(reverse('inicio:proximos_vencimentos'), {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_investidor_logado_sem_investimentos(self):
        """Testa investidor logado sem investimentos cadastrados"""
        tester = User.objects.create_user('tester', 'tester@teste.com', 'tester')
        self.tester = tester.investidor
        self.client.login(username='tester', password='tester')
        response = self.client.get(reverse('inicio:proximos_vencimentos'), {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        # Contexto
        self.assertIn('prox_vencimentos', response.context)
        self.assertEqual(response.context['prox_vencimentos'], [])
        
    def test_investidor_logado_com_investimentos(self):
        """Testa investidor logado com investimentos cadastrados"""
        nizbel = User.objects.create_user('nizbel', 'nizbel@teste.com', 'nizbel')
        self.nizbel = nizbel.investidor 
        
        # Cadastrar investimentos
        #CDB/RDB
        cdb_rdb_1 = CDB_RDB.objects.create(investidor=self.nizbel, nome='CDB teste 1', tipo='C', tipo_rendimento=2)
        HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, porcentagem=Decimal(100))
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, carencia=Decimal(365))
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, vencimento=Decimal(365))
        
        cdb_rdb_2 = CDB_RDB.objects.create(investidor=self.nizbel, nome='CDB teste 2', tipo='C', tipo_rendimento=2)
        HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, porcentagem=Decimal(100))
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, carencia=Decimal(365))
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, vencimento=Decimal(365))
        
        # CDB 1
        # Vence em 5 dias
        self.operacao_cdb_rdb_1 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=360)), tipo_operacao='C')
        # Vence em 10 dias
        self.operacao_cdb_rdb_2 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=355)), tipo_operacao='C')
        # Vence em 10 dias
#         self.operacao_cdb_rdb_3 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, investidor=self.nizbel, quantidade=Decimal(1000), 
#                                        data=(datetime.date.today() - datetime.timedelta(days=355)), tipo_operacao='C')
        # Vence em 365 dias
        self.operacao_cdb_rdb_4 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=datetime.date.today(), tipo_operacao='C')
        
        # CDB 2
        # Vence em 4 dias
        self.operacao_cdb_rdb_5 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=361)), tipo_operacao='C')
        # Vence em 9 dias
        self.operacao_cdb_rdb_6 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=356)), tipo_operacao='C')
        # Vence em 6 dias
        self.operacao_cdb_rdb_7 = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb_rdb_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=359)), tipo_operacao='C')
        
        # CRI/CRA
        cri_cra_1 = CRI_CRA.objects.create(nome='CRI teste 1', codigo_isin='BRCRITESTE1', tipo=CRI_CRA.TIPO_CRI, tipo_indexacao=CRI_CRA.TIPO_INDEXACAO_DI,
                                           porcentagem=Decimal(98), juros_adicional=0, data_emissao=(datetime.date.today() - datetime.timedelta(days=370)),
                                           valor_emissao=Decimal(1000), data_inicio_rendimento=(datetime.date.today() - datetime.timedelta(days=360)),
                                           data_vencimento=(datetime.date.today() + datetime.timedelta(days=5)), investidor=self.nizbel)
        cri_cra_2 = CRI_CRA.objects.create(nome='CRI teste 3', codigo_isin='BRCRITESTE3', tipo=CRI_CRA.TIPO_CRI, tipo_indexacao=CRI_CRA.TIPO_INDEXACAO_DI,
                                           porcentagem=Decimal(98), juros_adicional=0, data_emissao=(datetime.date.today() - datetime.timedelta(days=20)),
                                           valor_emissao=Decimal(1000), data_inicio_rendimento=(datetime.date.today() - datetime.timedelta(days=10)),
                                           data_vencimento=(datetime.date.today() + datetime.timedelta(days=355)), investidor=self.nizbel)
        
        # CRI 1
        # Vence em 5 dias
        self.operacao_cri_cra_1 = OperacaoCRI_CRA.objects.create(cri_cra=cri_cra_1, preco_unitario=Decimal(1200), quantidade=1, 
                                                                 data=(datetime.date.today() - datetime.timedelta(days=60)), tipo_operacao='C',
                                                                 taxa=0)
        # CRI 2
        # Vence em 355 dias
        self.operacao_cri_cra_2 = OperacaoCRI_CRA.objects.create(cri_cra=cri_cra_2, preco_unitario=Decimal(1050), quantidade=1, 
                                                                 data=(datetime.date.today() - datetime.timedelta(days=1)), tipo_operacao='C',
                                                                 taxa=0)
        
        # Debentures
        debenture_1 = Debenture.objects.create(codigo='TESTE91', indice=Debenture.PREFIXADO, porcentagem=Decimal('6.5'), 
                                               data_emissao=(datetime.date.today() - datetime.timedelta(days=370)), valor_emissao=Decimal(1000),
                                               data_inicio_rendimento=(datetime.date.today() - datetime.timedelta(days=360)), 
                                               data_vencimento=(datetime.date.today() + datetime.timedelta(days=5)), incentivada=True, 
                                               padrao_snd=True)
        HistoricoValorDebenture.objects.create(debenture=debenture_1, valor_nominal=1000, juros=35, premio=0, data=datetime.date.today())
        HistoricoValorDebenture.objects.create(debenture=debenture_1, valor_nominal=1000, juros=Decimal('34.3'), premio=0, 
                                               data=datetime.date.today() - datetime.timedelta(days=1))
        
        debenture_2 = Debenture.objects.create(codigo='TESTE92', indice=Debenture.PREFIXADO, porcentagem=Decimal('6.5'), 
                                               data_emissao=(datetime.date.today() - datetime.timedelta(days=20)), valor_emissao=Decimal(1000),
                                               data_inicio_rendimento=(datetime.date.today() - datetime.timedelta(days=10)), 
                                               data_vencimento=(datetime.date.today() + datetime.timedelta(days=355)), incentivada=True, 
                                               padrao_snd=True)
        HistoricoValorDebenture.objects.create(debenture=debenture_2, valor_nominal=1000, juros=3, premio=0, data=datetime.date.today())
        HistoricoValorDebenture.objects.create(debenture=debenture_2, valor_nominal=1000, juros=Decimal('2.78'), premio=0, 
                                               data=datetime.date.today() - datetime.timedelta(days=1))
        
        # Debenture 1
        # Vence em 5 dias
        self.operacao_deb_1 = OperacaoDebenture.objects.create(investidor=self.nizbel, debenture=debenture_1, preco_unitario=Decimal(1200),
                                                               quantidade=1, data=(datetime.date.today() - datetime.timedelta(days=60)), taxa=0,
                                                               tipo_operacao='C')
        # Debenture 2
        # Vence em 355 dias
        self.operacao_deb_2 = OperacaoDebenture.objects.create(investidor=self.nizbel, debenture=debenture_2, preco_unitario=Decimal(1050),
                                                               quantidade=1, data=(datetime.date.today() - datetime.timedelta(days=1)), taxa=0,
                                                               tipo_operacao='C')
        
        # LC
        lc_1 = LetraCambio.objects.create(investidor=self.nizbel, nome='LC teste 1', tipo_rendimento=2)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc_1, porcentagem=Decimal(100))
        HistoricoCarenciaLetraCambio.objects.create(lc=lc_1, carencia=Decimal(365))
        HistoricoVencimentoLetraCambio.objects.create(lc=lc_1, vencimento=Decimal(365))
        
        lc_2 = LetraCambio.objects.create(investidor=self.nizbel, nome='LC teste 2', tipo_rendimento=2)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc_2, porcentagem=Decimal(100))
        HistoricoCarenciaLetraCambio.objects.create(lc=lc_2, carencia=Decimal(365))
        HistoricoVencimentoLetraCambio.objects.create(lc=lc_2, vencimento=Decimal(365))
        
        # LC 1
        # Vence em 5 dias
        self.operacao_lc_1 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=360)), tipo_operacao='C')
        # Vence em 10 dias
        self.operacao_lc_2 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=355)), tipo_operacao='C')
        # Vence em 10 dias
#         self.operacao_lc_3 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=self.nizbel, quantidade=Decimal(1000), 
#                                        data=(datetime.date.today() - datetime.timedelta(days=355)), tipo_operacao='C')
        # Vence em 365 dias
        self.operacao_lc_4 = OperacaoLetraCambio.objects.create(lc=lc_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=datetime.date.today(), tipo_operacao='C')
        
        # LC 2
        # Vence em 4 dias
        self.operacao_lc_5 = OperacaoLetraCambio.objects.create(lc=lc_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=361)), tipo_operacao='C')
        # Vence em 9 dias
        self.operacao_lc_6 = OperacaoLetraCambio.objects.create(lc=lc_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=356)), tipo_operacao='C')
        
        # LCI/LCA
        lci_lca_1 = LetraCredito.objects.create(investidor=self.nizbel, nome='LCI teste 1', tipo_rendimento=2)
        HistoricoPorcentagemLetraCredito.objects.create(letra_credito=lci_lca_1, porcentagem=Decimal(100))
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci_lca_1, carencia=Decimal(365))
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci_lca_1, vencimento=Decimal(365))
        
        lci_lca_2 = LetraCredito.objects.create(investidor=self.nizbel, nome='LCI teste 2', tipo_rendimento=2)
        HistoricoPorcentagemLetraCredito.objects.create(letra_credito=lci_lca_2, porcentagem=Decimal(100))
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci_lca_2, carencia=Decimal(365))
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci_lca_2, vencimento=Decimal(365))
        
        # LCI 1
        # Vence em 5 dias
        self.operacao_lci_lca_1 = OperacaoLetraCredito.objects.create(letra_credito=lci_lca_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=360)), tipo_operacao='C')
        # Vence em 10 dias
        self.operacao_lci_lca_2 = OperacaoLetraCredito.objects.create(letra_credito=lci_lca_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=355)), tipo_operacao='C')
        # Vence em 10 dias
#         self.operacao_lci_lca_3 = OperacaoLetraCredito.objects.create(letra_credito=lci_lca_1, investidor=self.nizbel, quantidade=Decimal(1000), 
#                                        data=(datetime.date.today() - datetime.timedelta(days=355)), tipo_operacao='C')
        # Vence em 365 dias
        self.operacao_lci_lca_4 = OperacaoLetraCredito.objects.create(letra_credito=lci_lca_1, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=datetime.date.today(), tipo_operacao='C')
        
        # LCI 2
        # Vence em 4 dias
        self.operacao_lci_lca_5 = OperacaoLetraCredito.objects.create(letra_credito=lci_lca_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=361)), tipo_operacao='C')
        # Vence em 9 dias
        self.operacao_lci_lca_6 = OperacaoLetraCredito.objects.create(letra_credito=lci_lca_2, investidor=self.nizbel, quantidade=Decimal(1000), 
                                       data=(datetime.date.today() - datetime.timedelta(days=356)), tipo_operacao='C')
        
        # Tesouro direto
        titulo_1 = Titulo.objects.create(tipo='LTN', data_vencimento=(datetime.date.today() + datetime.timedelta(days=5)), 
                                         data_inicio=(datetime.date.today() - datetime.timedelta(days=725)))
        titulo_2 = Titulo.objects.create(tipo='LTN', data_vencimento=(datetime.date.today() + datetime.timedelta(days=370)), 
                                         data_inicio=(datetime.date.today() - datetime.timedelta(days=725)))
        
        # Título 1
        # Vence em 5 dias
        self.operacao_titulo_1 = OperacaoTitulo.objects.create(investidor=self.nizbel, preco_unitario=Decimal(700), quantidade=1, 
                                                               data=(datetime.date.today() - datetime.timedelta(days=50)), taxa_bvmf=0,
                                                               taxa_custodia=0, tipo_operacao='C', titulo=titulo_1, consolidada=True)
        
        # Título 2
        # Vence em 370 dias
        self.operacao_titulo_2 = OperacaoTitulo.objects.create(investidor=self.nizbel, preco_unitario=Decimal(700), quantidade=1, 
                                                               data=(datetime.date.today() - datetime.timedelta(days=50)), taxa_bvmf=0,
                                                               taxa_custodia=0, tipo_operacao='C', titulo=titulo_2, consolidada=True)
        
        self.client.login(username='nizbel', password='nizbel')
        response = self.client.get(reverse('inicio:proximos_vencimentos'), {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        # Contexto
        self.assertIn('prox_vencimentos', response.context)
        self.assertEqual(len(response.context['prox_vencimentos']), 10)
        # Apenas os com vencimento mais recente deve estar na lista
        self.assertIn(self.operacao_cdb_rdb_1, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_cdb_rdb_5, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_cdb_rdb_7, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_cri_cra_1, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_deb_1, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_lc_1, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_lc_5, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_lci_lca_1, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_lci_lca_5, response.context['prox_vencimentos'])
        self.assertIn(self.operacao_titulo_1, response.context['prox_vencimentos'])
        
        
    def test_investidor_logado_com_investimentos_vencidos(self):
        """Testa investidor logado com investimentos vencidos"""
        vencido = User.objects.create_user('vencido', 'vencido@teste.com', 'vencido')
        self.vencido = vencido.investidor 
        
        # Cadastrar investimentos
        # CRI/CRA
        cri_cra_1 = CRI_CRA.objects.create(nome='CRI teste 1', codigo_isin='BRCRITESTE1', tipo=CRI_CRA.TIPO_CRI, tipo_indexacao=CRI_CRA.TIPO_INDEXACAO_DI,
                                           porcentagem=Decimal(98), juros_adicional=0, data_emissao=(datetime.date.today() - datetime.timedelta(days=470)),
                                           valor_emissao=Decimal(1000), data_inicio_rendimento=(datetime.date.today() - datetime.timedelta(days=460)),
                                           data_vencimento=(datetime.date.today() - datetime.timedelta(days=95)), investidor=self.vencido)
        
        # CRI 1
        self.operacao_cri_cra_1 = OperacaoCRI_CRA.objects.create(cri_cra=cri_cra_1, preco_unitario=Decimal(1200), quantidade=1, 
                                                                 data=(datetime.date.today() - datetime.timedelta(days=160)), tipo_operacao='C',
                                                                 taxa=0)
        
        # Debentures
        debenture_1 = Debenture.objects.create(codigo='TESTE91', indice=Debenture.PREFIXADO, porcentagem=Decimal('6.5'), 
                                               data_emissao=(datetime.date.today() - datetime.timedelta(days=470)), valor_emissao=Decimal(1000),
                                               data_inicio_rendimento=(datetime.date.today() - datetime.timedelta(days=460)), 
                                               data_vencimento=(datetime.date.today() - datetime.timedelta(days=95)), incentivada=True, 
                                               padrao_snd=True)
        
        # Debenture 1
        self.operacao_deb_1 = OperacaoDebenture.objects.create(investidor=self.vencido, debenture=debenture_1, preco_unitario=Decimal(1200),
                                                               quantidade=1, data=(datetime.date.today() - datetime.timedelta(days=160)), taxa=0,
                                                               tipo_operacao='C')
        
        # Tesouro direto
        titulo_1 = Titulo.objects.create(tipo='LTN', data_vencimento=(datetime.date.today() - datetime.timedelta(days=95)), 
                                         data_inicio=(datetime.date.today() - datetime.timedelta(days=725)))
        
        # Título 1
        self.operacao_titulo_1 = OperacaoTitulo.objects.create(investidor=self.vencido, preco_unitario=Decimal(700), quantidade=1, 
                                                               data=(datetime.date.today() - datetime.timedelta(days=150)), taxa_bvmf=0,
                                                               taxa_custodia=0, tipo_operacao='C', titulo=titulo_1, consolidada=True)
        
        
        self.client.login(username='vencido', password='vencido')
        response = self.client.get(reverse('inicio:proximos_vencimentos'), {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        # Contexto
        self.assertIn('prox_vencimentos', response.context)
        self.assertEqual(response.context['prox_vencimentos'], [])

class ListarDivisoesTestCase(TestCase):
    
    def test_investidor_deslogado(self):
        """Testa acesso de usuário deslogado"""
        # Acessar
        response = self.client.get(reverse('divisoes:listar_divisoes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar dados
        self.assertEqual(response.context['divisoes'], [])
        
    def test_investidor_logado_sem_investimentos(self):
        """Testa acesso de usuário logado sem nenhum investimento registrado"""
        # Preparar usuário
        usuario_sem_investimentos = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        usuario_sem_investimentos = usuario_sem_investimentos.investidor 
        
        # Acessar
        self.client.login(username='teste', password='teste')
        response = self.client.get(reverse('divisoes:listar_divisoes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar dados
        self.assertEqual(len(response.context['divisoes']), 1)
        self.assertEqual(response.context['divisoes'][0].valor_atual, 0)
        
    def test_investidor_logado_com_investimentos(self):
        """Testa acesso de usuário logado com investimentos registrados"""
        # Preparar usuário
        usuario_sem_investimentos = User.objects.create_user('teste', 'teste@teste.com', 'teste')
        usuario_sem_investimentos = usuario_sem_investimentos.investidor 
        divisao = Divisao.objects.get(investidor=usuario_sem_investimentos)
        
        data_30_dias_atras = datetime.date.today() - datetime.timedelta(days=30)
        data_10_dias_atras = datetime.date.today() - datetime.timedelta(days=10)
        data_100_dias_apos = datetime.date.today() + datetime.timedelta(days=100)
        # Ações
        empresa = Empresa.objects.create(nome='Empresa teste', nome_pregao='BBAS')
        acao = Acao.objects.create(ticker='BBAS3', empresa=empresa)
        HistoricoAcao.objects.create(acao=acao, data=data_30_dias_atras, preco_unitario=10)
        HistoricoAcao.objects.create(acao=acao, data=data_10_dias_atras, preco_unitario=10)
        HistoricoAcao.objects.create(acao=acao, data=datetime.date.today(), preco_unitario=10)
        
        compra = OperacaoAcao.objects.create(acao=acao, quantidade=100, preco_unitario=Decimal(10), data=data_30_dias_atras, tipo_operacao='C', 
                                    consolidada=True, investidor=usuario_sem_investimentos, destinacao='B', corretagem=10, emolumentos=Decimal('0.5'))
        DivisaoOperacaoAcao.objects.create(divisao=divisao, operacao=compra, quantidade=compra.quantidade)
        venda = OperacaoAcao.objects.create(acao=acao, quantidade=50, preco_unitario=Decimal(10), data=data_10_dias_atras, tipo_operacao='V', 
                                    consolidada=True, investidor=usuario_sem_investimentos, destinacao='B', corretagem=10, emolumentos=Decimal('0.5'))
        DivisaoOperacaoAcao.objects.create(divisao=divisao, operacao=venda, quantidade=venda.quantidade)
        
        # CDB/RDB
        cdb = CDB_RDB.objects.create(nome='CDB teste', investidor=usuario_sem_investimentos, tipo='C', tipo_rendimento=CDB_RDB.CDB_RDB_DI)
        HistoricoCarenciaCDB_RDB.objects.create(cdb_rdb=cdb, carencia=365)
        HistoricoVencimentoCDB_RDB.objects.create(cdb_rdb=cdb, vencimento=365)
        HistoricoPorcentagemCDB_RDB.objects.create(cdb_rdb=cdb, porcentagem=120)
        
        compra = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb, quantidade=1000, data=data_30_dias_atras, tipo_operacao='C', investidor=usuario_sem_investimentos)
        DivisaoOperacaoCDB_RDB.objects.create(operacao=compra, quantidade=compra.quantidade, divisao=divisao)
        venda = OperacaoCDB_RDB.objects.create(cdb_rdb=cdb, quantidade=500, data=data_10_dias_atras, tipo_operacao='V', 
                                            investidor=usuario_sem_investimentos)
        OperacaoVendaCDB_RDB.objects.create(operacao_compra=compra, operacao_venda=venda)
        DivisaoOperacaoCDB_RDB.objects.create(operacao=venda, quantidade=venda.quantidade, divisao=divisao)
        
        # CRI/CRA
        cri = CRI_CRA.objects.create(nome='CRI teste', codigo_isin='BRZAPSO0393', tipo=CRI_CRA.TIPO_CRI, tipo_indexacao=CRI_CRA.TIPO_INDEXACAO_DI,
                                     porcentagem=100, juros_adicional=Decimal('0.5'), data_emissao=data_30_dias_atras, valor_emissao=1000,
                                     data_inicio_rendimento=data_30_dias_atras, data_vencimento=data_100_dias_apos, 
                                     investidor=usuario_sem_investimentos)
        
        compra = OperacaoCRI_CRA.objects.create(cri_cra=cri, preco_unitario=1000, quantidade=2, taxa=0, data=data_30_dias_atras, tipo_operacao='C')
        DivisaoOperacaoCRI_CRA.objects.create(operacao=compra, quantidade=compra.quantidade, divisao=divisao)
        venda = OperacaoCRI_CRA.objects.create(cri_cra=cri, preco_unitario=1000, quantidade=1, taxa=0, data=data_10_dias_atras, tipo_operacao='V')
        DivisaoOperacaoCRI_CRA.objects.create(operacao=venda, quantidade=venda.quantidade, divisao=divisao)
        
        # Criptomoedas
        
        # Debêntures
        debenture = Debenture.objects.create(codigo='BBAS63', indice=Debenture.DI, porcentagem=100, data_emissao=data_30_dias_atras, valor_emissao=1000,
                                 data_inicio_rendimento=data_30_dias_atras, data_vencimento=data_100_dias_apos, incentivada=True, padrao_snd=True)
        HistoricoValorDebenture.objects.create(debenture=debenture, juros=0, valor_nominal=1000, premio=0, data=data_30_dias_atras)
        HistoricoValorDebenture.objects.create(debenture=debenture, juros=4, valor_nominal=1000, premio=0, data=data_10_dias_atras)
        HistoricoValorDebenture.objects.create(debenture=debenture, juros=7, valor_nominal=1000, premio=0, data=datetime.date.today())
        
        compra = OperacaoDebenture.objects.create(investidor=usuario_sem_investimentos, debenture=debenture, preco_unitario=1000, quantidade=2,
                                         data=data_30_dias_atras, tipo_operacao='C', taxa=0)
        DivisaoOperacaoDebenture.objects.create(divisao=divisao, operacao=compra, quantidade=compra.quantidade)
        venda = OperacaoDebenture.objects.create(investidor=usuario_sem_investimentos, debenture=debenture, preco_unitario=1000, quantidade=1,
                                         data=data_10_dias_atras, tipo_operacao='V', taxa=0)
        DivisaoOperacaoDebenture.objects.create(divisao=divisao, operacao=venda, quantidade=venda.quantidade)
        
        # Fundos de Investimento
        fundo = FundoInvestimento.objects.create(nome='Fundo teste', cnpj='000.000.000/0001-91', data_constituicao=data_30_dias_atras, 
                                         data_registro=data_30_dias_atras, situacao=FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL,
                                         tipo_prazo=FundoInvestimento.PRAZO_LONGO, classe=FundoInvestimento.CLASSE_FUNDO_MULTIMERCADO,
                                         exclusivo_qualificados=False, slug=criar_slug_fundo_investimento_valido('Fundo teste'))
        HistoricoValorCotas.objects.create(fundo_investimento=fundo, valor_cotas=5, data=data_30_dias_atras)
        HistoricoValorCotas.objects.create(fundo_investimento=fundo, valor_cotas=6, data=data_10_dias_atras)
        HistoricoValorCotas.objects.create(fundo_investimento=fundo, valor_cotas=7, data=datetime.date.today())
        
        compra = OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo, investidor=usuario_sem_investimentos, quantidade=200,
                                                 valor=1000, data=data_30_dias_atras, tipo_operacao='C')
        DivisaoOperacaoFundoInvestimento.objects.create(divisao=divisao, operacao=compra, quantidade=compra.quantidade)
        venda = OperacaoFundoInvestimento.objects.create(fundo_investimento=fundo, investidor=usuario_sem_investimentos, quantidade=100,
                                                 valor=700, data=data_10_dias_atras, tipo_operacao='V')
        DivisaoOperacaoFundoInvestimento.objects.create(divisao=divisao, operacao=venda, quantidade=venda.quantidade)
        
        # FIIs
        fii = FII.objects.create(empresa=empresa, ticker='BBAS11')
        HistoricoFII.objects.create(fii=fii, data=data_30_dias_atras, preco_unitario=10)
        HistoricoFII.objects.create(fii=fii, data=data_10_dias_atras, preco_unitario=10)
        HistoricoFII.objects.create(fii=fii, data=datetime.date.today(), preco_unitario=10)
        
        compra = OperacaoFII.objects.create(fii=fii, quantidade=10, preco_unitario=Decimal(100), data=data_30_dias_atras, tipo_operacao='C',
                                   consolidada=True, investidor=usuario_sem_investimentos, corretagem=10, emolumentos=Decimal('0.5'))
        DivisaoOperacaoFII.objects.create(operacao=compra, divisao=divisao, quantidade=compra.quantidade)
        venda = OperacaoFII.objects.create(fii=fii, quantidade=5, preco_unitario=Decimal(100), data=data_10_dias_atras, tipo_operacao='V',
                                   consolidada=True, investidor=usuario_sem_investimentos, corretagem=10, emolumentos=Decimal('0.5'))
        DivisaoOperacaoFII.objects.create(operacao=venda, divisao=divisao, quantidade=venda.quantidade)
        
        # LCI/LCA
        lci = LetraCredito.objects.create(nome='LCA teste', investidor=usuario_sem_investimentos, tipo_rendimento=LetraCredito.LCI_LCA_DI)
        HistoricoCarenciaLetraCredito.objects.create(letra_credito=lci, carencia=365)
        HistoricoVencimentoLetraCredito.objects.create(letra_credito=lci, vencimento=365)
        HistoricoPorcentagemLetraCredito.objects.create(letra_credito=lci, porcentagem=92)
        
        compra = OperacaoLetraCredito.objects.create(letra_credito=lci, quantidade=1000, data=data_30_dias_atras, tipo_operacao='C', 
                                            investidor=usuario_sem_investimentos)
        DivisaoOperacaoLCI_LCA.objects.create(operacao=compra, quantidade=compra.quantidade, divisao=divisao)
        venda = OperacaoLetraCredito.objects.create(letra_credito=lci, quantidade=500, data=data_10_dias_atras, tipo_operacao='V', 
                                            investidor=usuario_sem_investimentos)
        OperacaoVendaLetraCredito.objects.create(operacao_compra=compra, operacao_venda=venda)
        DivisaoOperacaoLCI_LCA.objects.create(operacao=venda, quantidade=venda.quantidade, divisao=divisao)
        
        
        # Letra de Câmbio
        lc = LetraCambio.objects.create(nome='LC teste', investidor=usuario_sem_investimentos, tipo_rendimento=LetraCambio.LC_DI)
        HistoricoCarenciaLetraCambio.objects.create(lc=lc, carencia=365)
        HistoricoVencimentoLetraCambio.objects.create(lc=lc, vencimento=365)
        HistoricoPorcentagemLetraCambio.objects.create(lc=lc, porcentagem=120)
        
        compra = OperacaoLetraCambio.objects.create(lc=lc, quantidade=1000, data=data_30_dias_atras, tipo_operacao='C', investidor=usuario_sem_investimentos)
        DivisaoOperacaoLetraCambio.objects.create(operacao=compra, quantidade=compra.quantidade, divisao=divisao)
        venda = OperacaoLetraCambio.objects.create(lc=lc, quantidade=500, data=data_10_dias_atras, tipo_operacao='V', 
                                            investidor=usuario_sem_investimentos)
        OperacaoVendaLetraCambio.objects.create(operacao_compra=compra, operacao_venda=venda)
        DivisaoOperacaoLetraCambio.objects.create(operacao=venda, quantidade=venda.quantidade, divisao=divisao)
        
        # Tesouro Direto
        titulo = Titulo.objects.create(tipo=Titulo.TIPO_OFICIAL_LETRA_TESOURO, data_inicio=data_30_dias_atras, data_vencimento=data_100_dias_apos)
        HistoricoTitulo.objects.create(titulo=titulo, data=data_30_dias_atras, preco_compra=700, preco_venda=680, taxa_compra=Decimal(10), taxa_venda=Decimal('9.8'))
        HistoricoTitulo.objects.create(titulo=titulo, data=data_10_dias_atras, preco_compra=710, preco_venda=690, taxa_compra=Decimal(10), taxa_venda=Decimal('9.8'))
        HistoricoTitulo.objects.create(titulo=titulo, data=datetime.date.today(), preco_compra=720, preco_venda=700, taxa_compra=Decimal(10), taxa_venda=Decimal('9.8'))
        
        compra = OperacaoTitulo.objects.create(investidor=usuario_sem_investimentos, quantidade=1, preco_unitario=700, data=data_30_dias_atras,
                                      taxa_bvmf=0, taxa_custodia=0, tipo_operacao='C', titulo=titulo, consolidada=True)
        DivisaoOperacaoTD.objects.create(divisao=divisao, operacao=compra, quantidade=compra.quantidade)
        venda = OperacaoTitulo.objects.create(investidor=usuario_sem_investimentos, quantidade=Decimal('0.5'), preco_unitario=700, data=data_10_dias_atras,
                                      taxa_bvmf=0, taxa_custodia=0, tipo_operacao='V', titulo=titulo, consolidada=True)
        DivisaoOperacaoTD.objects.create(divisao=divisao, operacao=venda, quantidade=venda.quantidade)
        
        # Preparar histórico DI
        data = data_30_dias_atras
        while data <= datetime.date.today():
            if verifica_se_dia_util(data):
                HistoricoTaxaDI.objects.create(data=data, taxa=Decimal('6.5'))
            data = data + datetime.timedelta(days=1)
        
        # Acessar
        self.client.login(username='teste', password='teste')
        response = self.client.get(reverse('divisoes:listar_divisoes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar dados
        self.assertEqual(len(response.context['divisoes']), 1)
        self.assertNotEqual(response.context['divisoes'][0].valor_atual, 0)
        