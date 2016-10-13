# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoPrincipal, Divisao
from bagogold.bagogold.models.investidores import Investidor
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Gera divisões e configura como principal para cada usuario'

    def handle(self, *args, **options):
        for investidor in Investidor.objects.all():
            if not Divisao.objects.filter(investidor=investidor):
                print investidor, 'nao tem divisoes'
                divisao, criado = Divisao.objects.get_or_create(investidor=investidor, nome='Geral')
                DivisaoPrincipal.objects.get_or_create(investidor=investidor, divisao=divisao)
            elif not investidor.divisaoprincipal:
                print investidor, 'tem %s divisoes' % (len(Divisao.objects.filter(investidor=investidor))), 'sem principal'
#                 DivisaoPrincipal.objcts.get_or_create()
            else:
                print investidor, 'tem %s divisoes' % (len(Divisao.objects.filter(investidor=investidor)))
                for divisao in Divisao.objects.filter(investidor=investidor):
                    print divisao, divisao.divisao_principal()



