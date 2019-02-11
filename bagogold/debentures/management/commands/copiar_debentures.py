# -*- coding: utf-8 -*-
from bagogold.bagogold.models.debentures import Debenture as Debenture_old, \
    AmortizacaoDebenture as AmortizacaoDebenture_old, \
    JurosDebenture as JurosDebenture_old, PremioDebenture as PremioDebenture_old, \
    OperacaoDebenture as OperacaoDebenture_old, HistoricoValorDebenture as HistoricoValorDebenture_old
from bagogold.debentures.models  import Debenture, AmortizacaoDebenture, \
    JurosDebenture, PremioDebenture, OperacaoDebenture, HistoricoValorDebenture
from django.core.management.base import BaseCommand
from django.db import transaction
  
  
class Command(BaseCommand):
    help = 'TEMPORÁRIO copia os modelos de Debentures de dentro do app bagogold para os novos modelos'
  
    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                Debenture.objects.all().delete()
                AmortizacaoDebenture.objects.all().delete()
                JurosDebenture.objects.all().delete()
                PremioDebenture.objects.all().delete()
                OperacaoDebenture.objects.all().delete()
                HistoricoValorDebenture.objects.all().delete()
                  
                for debenture in Debenture_old.objects.all().values():
                    print debenture
                    Debenture.objects.create(**debenture)
                      
                for operacao in OperacaoDebenture_old.objects.all().values():
                    print operacao
                    OperacaoDebenture.objects.create(**operacao)
                      
                for amortizacao in AmortizacaoDebenture_old.objects.all().values():
                    print amortizacao
                    AmortizacaoDebenture.objects.create(**amortizacao)
                      
                for juros in JurosDebenture_old.objects.all().values():
                    print juros
                    JurosDebenture.objects.create(**juros)
                      
                for premio in PremioDebenture_old.objects.all().values():
                    print premio
                    PremioDebenture.objects.create(**premio)
                
                data = datetime.date.today()
                while HistoricoValorDebenture.objects.all().count() < HistoricoValorDebenture_old.objects.all().count():
                    for historico in HistoricoValorDebenture_old.objects.filter(data=data).values():
                        print historico
                        HistoricoValorDebenture.objects.create(**historico)
                    data = data - datetime.timedelta(days=1)
                    
#                 for historico in HistoricoValorDebenture_old.objects.all().values():
#                     print historico
#                     HistoricoValorDebenture.objects.create(**historico)
        except Exception as e:
            print e
