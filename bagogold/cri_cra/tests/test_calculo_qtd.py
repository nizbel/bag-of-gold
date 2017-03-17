# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.cri_cra.models.cri_cra import CRI_CRA, OperacaoCRI_CRA
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.test import TestCase
import datetime
from bagogold.cri_cra.utils.utils import quantidade_cri_cra_na_data_para_certificado

class CalcularQtdCRI_CRATestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        # CRI 1
        cri_cra_1 = CRI_CRA.objects.create(nome="CRI Cyrela teste", investidor=user.investidor, codigo_isin='BRCYRELA', tipo='I', tipo_indexacao=1,
                               porcentagem=Decimal(98), data_emissao=datetime.date(2016, 9, 30), valor_emissao=Decimal(1000), 
                               data_vencimento=datetime.date(2018, 12, 5))
        # CRI 2
        cri_cra_2 = CRI_CRA.objects.create(nome="CRA Fibria teste", investidor=user.investidor, codigo_isin='BRFIBRIA', tipo='A', tipo_indexacao=1,
                               porcentagem=Decimal(98), data_emissao=datetime.date(2015, 9, 30), valor_emissao=Decimal(1000), 
                               data_vencimento=datetime.date(2018, 12, 6))
        # CRI 3
        cri_cra_3 = CRI_CRA.objects.create(nome="CRA BRBR teste", investidor=user.investidor, codigo_isin='BRBR', tipo='I', tipo_indexacao=1,
                               porcentagem=Decimal(98), data_emissao=datetime.date(2015, 8, 30), valor_emissao=Decimal(1000), 
                               data_vencimento=datetime.date(2018, 10, 7))
        
        # Operações CRI 1
        OperacaoCRI_CRA.objects.create(quantidade=1, preco_unitario=1000, data=datetime.date(2016, 12, 1), cri_cra=cri_cra_1,
                                       tipo_operacao='C', taxa=Decimal(0))
        
        # Operações CRI 3
        OperacaoCRI_CRA.objects.create(quantidade=1, preco_unitario=1000, data=datetime.date(2016, 11, 1), cri_cra=cri_cra_3,
                                       tipo_operacao='C', taxa=Decimal(0))
        OperacaoCRI_CRA.objects.create(quantidade=1, preco_unitario=1000, data=datetime.date(2016, 12, 2), cri_cra=cri_cra_3,
                                       tipo_operacao='V', taxa=Decimal(0))

    def test_calculo_quantidade_cri_cra(self):
        """Testar quantidade de CRI/CRA o investidor possui"""
        self.assertEqual(quantidade_cri_cra_na_data_para_certificado(datetime.date(2016, 12, 31), CRI_CRA.objects.get(codigo_isin='BRCYRELA')), 1)
        self.assertEqual(quantidade_cri_cra_na_data_para_certificado(datetime.date(2016, 12, 31), CRI_CRA.objects.get(codigo_isin='BRFIBRIA')), 0)
        self.assertEqual(quantidade_cri_cra_na_data_para_certificado(datetime.date(2016, 12, 31), CRI_CRA.objects.get(codigo_isin='BRBR')), 0)
