# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.lc import OperacaoLetraCredito, LetraCredito, \
    HistoricoTaxaDI
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxa_di, \
    calcular_valor_lc_ate_dia
from bagogold.cri_cra.models.cri_cra import CRI_CRA
from bagogold.cri_cra.utils.valorizacao import calcular_valor_um_cri_cra_na_data
from decimal import Decimal, ROUND_DOWN
from django.contrib.auth.models import User
from django.test import TestCase
import datetime
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa

class AtualizarCRI_CRAPorDITestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        CRI_CRA.objects.create(nome="CRI Cyrela teste", investidor=user.investidor, codigo_isin='BRCYRELA', tipo='I', tipo_indexacao=1,
                               porcentagem=Decimal(98), data_emissao=datetime.date(2016, 9, 30), valor_emissao=Decimal(1000), 
                               data_vencimento=datetime.date(2018, 12, 5), data_inicio_rendimento=datetime.date(2016, 10, 27))
        
        data_di = datetime.date(2016, 9, 30)
        while data_di < datetime.date(2017, 3, 14):
            if data_di.weekday() < 5 and not verificar_feriado_bovespa(data_di):
                if data_di < datetime.date(2016, 10, 20):
                    valor = Decimal('14.13')
                elif data_di < datetime.date(2016, 12, 1):
                    valor = Decimal('13.88')
                elif data_di < datetime.date(2017, 1, 12):
                    valor = Decimal('13.63')
                elif data_di < datetime.date(2017, 2, 23):
                    valor = Decimal('12.88')
                else:
                    valor = Decimal('12.13')
                HistoricoTaxaDI.objects.create(data=data_di, taxa=valor)
            data_di = data_di + datetime.timedelta(days=1)
        

    def test_calculo_valor_atualizado_taxa_di(self):
        """Testar de acordo com os valores pegos no extrato, 98% CDI começando em 30 de Setembro"""
        # 20/12/2016    1.018,77
        # 14/03/2017    1.047,21    
        # 22/11/2016    1.008,63
        # 01/12/2016    1.012,21
        
        self.assertAlmostEqual(calcular_valor_um_cri_cra_na_data(CRI_CRA.objects.get(codigo_isin='BRCYRELA'), datetime.date(2016, 12, 20)), Decimal('1018.77'), delta=Decimal('0.01'))
#         self.assertAlmostEqual(calcular_valor_um_cri_cra_na_data(CRI_CRA.objects.get(codigo_isin='BRCYRELA'), datetime.date(2017, 3, 14)), Decimal('1047.21'), delta=Decimal('0.01'))
        self.assertAlmostEqual(calcular_valor_um_cri_cra_na_data(CRI_CRA.objects.get(codigo_isin='BRCYRELA'), datetime.date(2016, 11, 22)), Decimal('1008.63'), delta=Decimal('0.01'))
        self.assertAlmostEqual(calcular_valor_um_cri_cra_na_data(CRI_CRA.objects.get(codigo_isin='BRCYRELA'), datetime.date(2016, 12, 1)), Decimal('1012.21'), delta=Decimal('0.01'))


# "2016-09-30";14.13
# "2016-10-03";14.13
# "2016-10-04";14.13
# "2016-10-05";14.13
# "2016-10-06";14.13
# "2016-10-07";14.13
# "2016-10-10";14.13
# "2016-10-11";14.13
# "2016-10-13";14.13
# "2016-10-14";14.13
# "2016-10-17";14.13
# "2016-10-18";14.13
# "2016-10-19";14.13
# "2016-10-20";13.88
# "2016-10-21";13.88
# "2016-10-24";13.88
# "2016-10-25";13.88
# "2016-10-26";13.88
# "2016-10-27";13.88
# "2016-10-28";13.88
# "2016-10-31";13.88
# "2016-11-01";13.88
# "2016-11-03";13.88
# "2016-11-04";13.88
# "2016-11-07";13.88
# "2016-11-08";13.88
# "2016-11-09";13.88
# "2016-11-10";13.88
# "2016-11-11";13.88
# "2016-11-14";13.88
# "2016-11-16";13.88
# "2016-11-17";13.88
# "2016-11-18";13.88
# "2016-11-21";13.88
# "2016-11-22";13.88
# "2016-11-23";13.88
# "2016-11-24";13.88
# "2016-11-25";13.88
# "2016-11-28";13.88
# "2016-11-29";13.88
# "2016-11-30";13.88
# "2016-12-01";13.63
# "2016-12-02";13.63
# "2016-12-05";13.63
# "2016-12-06";13.63
# "2016-12-07";13.63
# "2016-12-08";13.63
# "2016-12-09";13.63
# "2016-12-12";13.63
# "2016-12-13";13.63
# "2016-12-14";13.63
# "2016-12-15";13.63
# "2016-12-16";13.63
# "2016-12-19";13.63
# "2016-12-20";13.63
# "2016-12-21";13.63
# "2016-12-22";13.63
# "2016-12-23";13.63
# "2016-12-26";13.63
# "2016-12-27";13.63
# "2016-12-28";13.63
# "2016-12-29";13.63
# "2016-12-30";13.63
# "2017-01-02";13.63
# "2017-01-03";13.63
# "2017-01-04";13.63
# "2017-01-05";13.63
# "2017-01-06";13.63
# "2017-01-09";13.63
# "2017-01-10";13.63
# "2017-01-11";13.63
# "2017-01-12";12.88
# "2017-01-13";12.88
# "2017-01-16";12.88
# "2017-01-17";12.88
# "2017-01-18";12.88
# "2017-01-19";12.88
# "2017-01-20";12.88
# "2017-01-23";12.88
# "2017-01-24";12.88
# "2017-01-25";12.88
# "2017-01-26";12.88
# "2017-01-27";12.88
# "2017-01-30";12.88
# "2017-01-31";12.88
# "2017-02-01";12.88
# "2017-02-02";12.88
# "2017-02-03";12.88
# "2017-02-06";12.88
# "2017-02-07";12.88
# "2017-02-08";12.88
# "2017-02-09";12.88
# "2017-02-10";12.88
# "2017-02-13";12.88
# "2017-02-14";12.88
# "2017-02-15";12.88
# "2017-02-16";12.88
# "2017-02-17";12.88
# "2017-02-20";12.88
# "2017-02-21";12.88
# "2017-02-22";12.88
# "2017-02-23";12.13
# "2017-02-24";12.13
# "2017-03-01";12.13
# "2017-03-02";12.13
# "2017-03-03";12.13
# "2017-03-06";12.13
# "2017-03-07";12.13
# "2017-03-08";12.13
