# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls.base import reverse

from bagogold.cdb_rdb.models import CDB_RDB, HistoricoPorcentagemCDB_RDB, \
    HistoricoCarenciaCDB_RDB, HistoricoVencimentoCDB_RDB, OperacaoCDB_RDB
from bagogold.lc.models import LetraCambio, HistoricoPorcentagemLetraCambio, \
    HistoricoCarenciaLetraCambio, HistoricoVencimentoLetraCambio, \
    OperacaoLetraCambio
from bagogold.lci_lca.models import LetraCredito, \
    HistoricoPorcentagemLetraCredito, HistoricoCarenciaLetraCredito, \
    HistoricoVencimentoLetraCredito, OperacaoLetraCredito
from bagogold.tesouro_direto.models import Titulo, OperacaoTitulo
from bagogold.cri_cra.models.cri_cra import CRI_CRA, OperacaoCRI_CRA
from bagogold.debentures.models import Debenture, OperacaoDebenture


class ProxVencimentosPainelGeralTestCase(TestCase):
    def setUp(self):
        pass
        
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
        debenture_2 = Debenture.objects.create(codigo='TESTE92', indice=Debenture.PREFIXADO, porcentagem=Decimal('6.5'), 
                                               data_emissao=(datetime.date.today() - datetime.timedelta(days=20)), valor_emissao=Decimal(1000),
                                               data_inicio_rendimento=(datetime.date.today() - datetime.timedelta(days=10)), 
                                               data_vencimento=(datetime.date.today() + datetime.timedelta(days=355)), incentivada=True, 
                                               padrao_snd=True)
        
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