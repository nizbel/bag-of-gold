# -*- coding: utf-8 -*-

import datetime

from django.test import TestCase

from bagogold.fundo_investimento.management.commands.buscar_fundos_investimento import buscar_arquivo_csv_cadastro, \
    processar_arquivo_csv
from bagogold.fundo_investimento.models import DocumentoCadastro, \
    FundoInvestimento, Administrador, Auditor, Gestor


class BuscarFundoInvestimentoTestCase(TestCase):
    """
    Testa os utilitários usados na busca de fundos de investimento
    """
    def setUp(self):
        # TODO Definir quais passos todos os utilitários têm em comum 
        pass
        
    def test_buscar_documento_cvm_sucesso(self):
        """Testa busca de documento de cadastro de fundos na CVM, com sucesso"""
        retorno = buscar_arquivo_csv_cadastro(datetime.date(2018, 10, 26))
        self.assertEquals(len(retorno), 3)
        self.assertEquals(retorno[0], 'http://dados.cvm.gov.br/dados/FI/CAD/DADOS/inf_cadastral_fi_20181026.csv')
        self.assertEquals(retorno[1], 'inf_cadastral_fi_20181026.csv')
        self.assertTrue(hasattr(retorno[2], 'read'))
        
    def test_buscar_documento_cvm_data_nao_util(self):
        """Testa busca de documento de cadastro de fundos em data não útil"""
        with self.assertRaises(ValueError):
            buscar_arquivo_csv_cadastro(datetime.date(2018, 10, 27))
            
    def test_processar_documento_cvm_sucesso(self):
        """Testa processar documento de cadastro de fundos, com sucesso"""
        # Gerar fundos pré-existentes para teste
        
        # Abrir arquivo de teste
#         with open('test_documento_cadastro.csv') as f:
#             processar_arquivo_csv(novo_documento, f, data_pesquisa)
                
        # Processar
        pass
    
    def test_processar_registro_fundo_novo(self):
        """Testa processar uma linha no documento que descreve um fundo ainda não existente"""
        #10.705.335/0001-69;CLARITAS INSTITUCIONAL FUNDO DE INVESTIMENTO MULTIMERCADO;2009-06-22;2009-06-22;;EM FUNCIONAMENTO NORMAL;2009-06-22;2009-06-22;2018-07-01;2019-06-30;Fundo Multimercado;2009-06-22;DI de um dia;Aberto;N;N;S;N;20.000000000000;859853807.90;2018-10-24;CARLOS ALBERTO SARAIVA;02.201.501/0001-61;BNY MELLON SERVICOS FINANCEIROS DTVM S.A.;PJ;03.987.891/0001-00;CLARITAS ADMINISTRAÇÃO DE RECURSOS LTDA;57.755.217/0001-29;KPMG AUDITORES INDEPENDENTES
        self.assertTrue(FundoInvestimento.objects.all().count() == 0)
        with open('') as f:
            processar_arquivo_csv(novo_documento, f)
            
        # Verificações
        self.assertTrue(FundoInvestimento.objects.all().count() == 1)
        self.assertTrue(Administrador.objects.all().count() == 1)
        self.assertTrue(Auditor.objects.all().count() == 1)
        self.assertTrue(Gestor.objects.all().count() == 1)

        fundo = FundoInvestimento.objects.filter(cnpj='10.705.335/0001-69').select_related('administrador', 'auditor').prefetch_related('gestor_fundo')[0]
        self.assertEqual(fundo.nome, 'CLARITAS INSTITUCIONAL FUNDO DE INVESTIMENTO MULTIMERCADO')
        self.assertEqual(fundo.data_registro, datetime.date(2009, 6, 22))
        self.assertEqual(fundo.data_constituicao, datetime.date(2009, 6, 22))
        self.assertEqual(fundo.situacao, FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL)
        self.assertEqual(fundo.classe, FundoInvestimento.CLASSE_FUNDO_MULTIMERCADO)
        self.assertEqual(fundo.data_cancelamento, None)
        # Administrador
        self.assertEqual(fundo.administrador.nome, 'BNY MELLON SERVICOS FINANCEIROS DTVM S.A.')
        self.assertEqual(fundo.administrador.cnpj, '02.201.501/0001-61')
        # Auditor
        self.assertEqual(fundo.auditor.nome, 'KPMG AUDITORES INDEPENDENTES')
        self.assertEqual(fundo.auditor.cnpj, '57.755.217/0001-29')
        # TODO Gestor
        
    def test_processar_registro_fundo_novo_sem_admin(self):
        """Testa processar uma linha do documento que descreve um fundo ainda não existente, porém sem administrador"""
        #06.047.283/0001-03;5 ESTRELAS FUNDO DE INVESTIMENTO EM COTAS DE FUNDOS DE INVESTIMENTO MULTIMERCADO;2005-03-24;2003-12-30;2005-07-21;CANCELADA;2005-07-21;2003-12-30;2005-03-14;2005-12-31;Fundo Multimercado;2005-03-14;OUTROS;Aberto;S;N;N;S;;0.00;2005-08-03;;;;;;;;
        self.assertTrue(FundoInvestimento.objects.all().count() == 0)
        with open('') as f:
            processar_arquivo_csv(novo_documento, f, data_pesquisa)
            
        # Verificações
        self.assertTrue(FundoInvestimento.objects.all().count() == 1)
        self.assertTrue(Administrador.objects.all().count() == 1)
        self.assertTrue(Auditor.objects.all().count() == 1)
        self.assertTrue(Gestor.objects.all().count() == 1)

        fundo = FundoInvestimento.objects.filter(cnpj='10.705.335/0001-69').select_related('administrador', 'auditor').prefetch_related('gestor_fundo')[0]
        self.assertEqual(fundo.nome, 'CLARITAS INSTITUCIONAL FUNDO DE INVESTIMENTO MULTIMERCADO')
        self.assertEqual(fundo.data_registro, datetime.date(2009, 6, 22))
        self.assertEqual(fundo.data_constituicao, datetime.date(2009, 6, 22))
        self.assertEqual(fundo.situacao, FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL)
        self.assertEqual(fundo.classe, FundoInvestimento.CLASSE_FUNDO_MULTIMERCADO)
        self.assertEqual(fundo.data_cancelamento, None)
        # Administrador
        self.assertEqual(fundo.administrador, None)
        # Auditor
        self.assertEqual(fundo.auditor.nome, 'KPMG AUDITORES INDEPENDENTES')
        self.assertEqual(fundo.auditor.cnpj, '57.755.217/0001-29')
        # TODO Gestor
    
    def test_processar_registro_fundo_existente(self):
        """Testa processar uma linha no documento que descreve um fundo já existente"""
        #10.705.335/0001-69;CLARITAS INSTITUCIONAL FUNDO DE INVESTIMENTO MULTIMERCADO;2009-06-22;2009-06-22;;EM FUNCIONAMENTO NORMAL;2009-06-22;2009-06-22;2018-07-01;2019-06-30;Fundo Multimercado;2009-06-22;DI de um dia;Aberto;N;N;S;N;20.000000000000;859853807.90;2018-10-24;CARLOS ALBERTO SARAIVA;02.201.501/0001-61;BNY MELLON SERVICOS FINANCEIROS DTVM S.A.;PJ;03.987.891/0001-00;CLARITAS ADMINISTRAÇÃO DE RECURSOS LTDA;57.755.217/0001-29;KPMG AUDITORES INDEPENDENTES
        pass
    
    def test_processar_registros_iguais(self):
        """Testa processar múltiplas linhas no documento exatamente iguais"""
        #27.292.836/0001-63;CIBRIUS FUNDO DE INVESTIMENTO MULTIMERCADO CRÉDITO PRIVADO;2017-06-02;2017-02-21;;EM FUNCIONAMENTO NORMAL;2017-07-11;2017-07-11;2018-08-01;2019-07-31;Fundo Multimercado;2017-02-21;DI de um dia;Aberto;N;S;N;S;0.000000000000;215476462.91;2018-10-24;ERICK WARNER DE CARVALHO;62.318.407/0001-19;SANTANDER SECURITIES SERVICES BRASIL DTVM S.A;PJ;00.531.590/0001-89;CIBRIUS - INSTITUTO CONAB DE SEGURIDADE SOCIAL;57.755.217/0001-29;KPMG AUDITORES INDEPENDENTES
        #27.292.836/0001-63;CIBRIUS FUNDO DE INVESTIMENTO MULTIMERCADO CRÉDITO PRIVADO;2017-06-02;2017-02-21;;EM FUNCIONAMENTO NORMAL;2017-07-11;2017-07-11;2018-08-01;2019-07-31;Fundo Multimercado;2017-02-21;DI de um dia;Aberto;N;S;N;S;0.000000000000;215476462.91;2018-10-24;ERICK WARNER DE CARVALHO;62.318.407/0001-19;SANTANDER SECURITIES SERVICES BRASIL DTVM S.A;PJ;00.531.590/0001-89;CIBRIUS - INSTITUTO CONAB DE SEGURIDADE SOCIAL;57.755.217/0001-29;KPMG AUDITORES INDEPENDENTES
        pass
    
    def test_processar_registros_cancelados_mesmo_fundo(self):
        """Testa processar múltiplos registros de um mesmo fundo, com situações diferentes porém ambos indicando um fundo cancelado"""
        #19.959.754/0001-00;AB CAPITAL II FUNDO DE INVESTIMENTO IMOBILIÁRIO;2014-10-15;2014-10-10;2017-12-29;EM FUNCIONAMENTO NORMAL;2014-10-21;2014-10-21;2018-01-01;2018-12-31;Fundo Multimercado;2014-10-10;DI de um dia;Fechado;N;S;S;S;;37650897.53;2018-01-05;;;;;;;;
        #19.959.754/0001-00;AB CAPITAL II FUNDO DE INVESTIMENTO IMOBILIÁRIO;2014-10-15;2014-10-10;2017-12-29;CANCELADA;2017-12-29;2014-10-21;2018-01-01;2018-12-31;Fundo Multimercado;2014-10-10;DI de um dia;Fechado;N;S;S;S;;37650897.53;2018-01-05;;;;;;;;
        pass
    
    def test_processar_registros_mesmo_fundo_gestor_diferente(self):
        """Testa processar múltiplas linhas para o mesmo fundo, porém com gestores diferentes"""
        #05.526.548/0001-93;OPPORTUNITY SOP FUNDO DE INVESTIMENTO EM COTAS DE FUNDOS DE INVESTIMENTO EM AÇÕES;2005-02-01;2003-02-19;2013-11-18;CANCELADA;2013-11-18;2003-03-21;2013-07-01;2014-06-30;Fundo de Ações;2005-01-31;;Fechado;S;N;;S;20.000000000000;0.00;2013-11-29;MARCUS VINICIUS MATHIAS PEREIRA;02.201.501/0001-61;BNY MELLON SERVICOS FINANCEIROS DTVM S.A.;PJ;01.608.570/0001-21;OPPORTUNITY GESTORA DE RECURSOS LTDA;57.755.217/0001-29;KPMG AUDITORES INDEPENDENTES
        #05.526.548/0001-93;OPPORTUNITY SOP FUNDO DE INVESTIMENTO EM COTAS DE FUNDOS DE INVESTIMENTO EM AÇÕES;2005-02-01;2003-02-19;2013-11-18;CANCELADA;2013-11-18;2003-03-21;2013-07-01;2014-06-30;Fundo de Ações;2005-01-31;;Fechado;S;N;;S;20.000000000000;0.00;2013-11-29;MARCUS VINICIUS MATHIAS PEREIRA;02.201.501/0001-61;BNY MELLON SERVICOS FINANCEIROS DTVM S.A.;PJ;05.395.883/0001-08;OPPORTUNITY ASSET ADMINISTRADORA DE RECURSOS DE TERCEIROS LTDA;57.755.217/0001-29;KPMG AUDITORES INDEPENDENTES
        #05.526.548/0001-93;OPPORTUNITY SOP FUNDO DE INVESTIMENTO EM COTAS DE FUNDOS DE INVESTIMENTO EM AÇÕES;2005-02-01;2003-02-19;2013-11-18;CANCELADA;2013-11-18;2003-03-21;2013-07-01;2014-06-30;Fundo de Ações;2005-01-31;;Fechado;S;N;;S;20.000000000000;0.00;2013-11-29;MARCUS VINICIUS MATHIAS PEREIRA;02.201.501/0001-61;BNY MELLON SERVICOS FINANCEIROS DTVM S.A.;PJ;09.647.907/0001-11;OPPORTUNITY GESTÃO DE INVESTIMENTOS E RECURSOS LTDA;57.755.217/0001-29;KPMG AUDITORES INDEPENDENTES
        pass
    
    def test_processar_registros_fundo_reiniciado(self):
        """Testa processar múltiplas linhas para o mesmo fundo, porém uma indica cancelamento e a outra não (fundo reaberto)"""
        #24.814.904/0001-19;PROSPECT MERCANTIL FUNDO DE INVESTIMENTO MULTIMERCADO CRÉDITO PRIVADO;2016-05-18;2016-05-05;2017-11-21;CANCELADA;2017-11-21;2016-06-16;2018-01-01;2018-12-31;Fundo Multimercado;2016-05-05;OUTROS;Fechado;N;N;S;S;0.000000000000;12931993.07;2018-05-22;;;;;;;;
        #24.814.904/0001-19;PROSPECT MERCANTIL FUNDO DE INVESTIMENTO MULTIMERCADO CRÉDITO PRIVADO;2018-08-31;2016-05-05;;EM FUNCIONAMENTO NORMAL;2018-08-31;2018-08-31;2018-05-01;2019-04-30;Fundo Multimercado;2018-08-31;DI de um dia;Fechado;N;N;S;S;;12131665.81;2018-10-24;FABIO FEOLA;02.671.743/0001-19;CM CAPITAL MARKETS DTVM LTDA;PJ;24.515.907/0001-51;ATRIO GESTORA DE ATIVOS LTDA;42.170.852/0001-77;CROWE HORWATH BENDORAYTES & CIA AUDITORES INDEPENDENTES
        pass
    
    def test_processar_registro_sem_admin_para_fundo_com_admin(self):
        """Testa processar linha do documento que descreva um fundo já existente, porém sem informação sobre administrador"""
        #10.705.335/0001-69;CLARITAS INSTITUCIONAL FUNDO DE INVESTIMENTO MULTIMERCADO;2009-06-22;2009-06-22;;EM FUNCIONAMENTO NORMAL;2009-06-22;2009-06-22;2018-07-01;2019-06-30;Fundo Multimercado;2009-06-22;DI de um dia;Aberto;N;N;S;N;20.000000000000;859853807.90;2018-10-24;CARLOS ALBERTO SARAIVA;;;PJ;03.987.891/0001-00;CLARITAS ADMINISTRAÇÃO DE RECURSOS LTDA;57.755.217/0001-29;KPMG AUDITORES INDEPENDENTES
        pass
    