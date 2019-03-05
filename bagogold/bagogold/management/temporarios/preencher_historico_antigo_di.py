# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
import traceback

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.aggregates import Count

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo
from bagogold.bagogold.utils.taxas_indexacao import calcular_valor_atualizado_com_taxas_di


class Command(BaseCommand):
    help = 'TEMPORÁRIO preencher histórico antigo do DI'


    def handle(self, *args, **options):
#         historico_graf = [(datetime.date(2009, 6, 22), Decimal('1')), (datetime.date(2019, 2, 28), Decimal('2.78'))]
#         taxas_dos_dias = dict(HistoricoTaxaDI.objects.filter(data__range=[historico_graf[0][0], historico_graf[len(historico_graf)-1][0]]) \
#                               .values('taxa').order_by('taxa').annotate(qtd_dias=Count('taxa')).values_list('taxa', 'qtd_dias'))
#          
#         print 'Dias base de dados:', HistoricoTaxaDI.objects.filter(data__range=[historico_graf[0][0], historico_graf[len(historico_graf)-1][0]]).count()
#         print 'Dias no calculo:', sum([qtd for qtd in taxas_dos_dias.values()])
#         print 'Dias uteis:', qtd_dias_uteis_no_periodo(historico_graf[0][0], historico_graf[1][0])
#         print calcular_valor_atualizado_com_taxas_di(taxas_dos_dias, historico_graf[0][1], 100)
#         
        with open('201903042352190.4571192.xls', 'r') as arq_xls:
            i = 0
            try:
                with transaction.atomic():
                    while (True):
                        linha = arq_xls.readline()
                        i += 1
                         
                        if linha == '':
                            break
#                         print i, linha.replace('\r\n', '')
                         
                        try:
                            data = datetime.datetime.strptime(linha[:10], '%d/%m/%Y').date()
                        except:
                            data = None
                         
                        if data != None and data > datetime.date(2000, 1, 1):
                            valor = Decimal(linha.split('\t')[3].replace(',', '.'))
#                             print i, data, valor
                             
                            if not HistoricoTaxaDI.objects.filter(data=data).exists():
                                HistoricoTaxaDI.objects.create(taxa=valor, data=data)
                            else:
                                if HistoricoTaxaDI.objects.get(data=data).taxa != valor:
                                    raise ValueError('Ja existe valor diferente para data %s' % (data.strftime('%d/%m/%Y')))
                             
            except:
                print traceback.format_exc()
                
