# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.acoes import verificar_tipo_acao
from django.test import TestCase

class VerificarTipoAcaoTestCase(TestCase):
    def test_verificar_tipo_acao(self):
        """Testar se os tipos de ações estão sendo convertidos corretamente"""
        self.assertEqual(verificar_tipo_acao('CMIG3'), 'ON')
        self.assertEqual(verificar_tipo_acao('CMIG4'), 'PN')
        self.assertEqual(verificar_tipo_acao('CMIG5'), 'PNA')
        self.assertEqual(verificar_tipo_acao('CMIG6'), 'PNB')
        self.assertEqual(verificar_tipo_acao('CMIG7'), 'PNC')
        self.assertEqual(verificar_tipo_acao('CMIG8'), 'PND')
