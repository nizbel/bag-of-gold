# -*- coding: utf-8 -*-
from bagogold.fii.models import FII, OperacaoFII, ProventoFII,\
    UsoProventosOperacaoFII, ValorDiarioFII, EventoFII,\
    EventoIncorporacaoFII, EventoAgrupamentoFII,\
    EventoDesdobramentoFII, CheckpointFII, CheckpointProventosFII
from bagogold.bagogold.models.fii import FII as FII_old,\
    OperacaoFII as OperacaoFII_old, ProventoFII as ProventoFII_old,\
    UsoProventosOperacaoFII as UsoProventosOperacaoFII_old,\
    ValorDiarioFII as ValorDiarioFII_old, EventoFII as EventoFII_old,\
    EventoIncorporacaoFII as EventoIncorporacaoFII_old,\
    EventoAgrupamentoFII as EventoAgrupamentoFII_old,\
    EventoDesdobramentoFII as EventoDesdobramentoFII_old,\
    CheckpointFII as CheckpointFII_old,\
    CheckpointProventosFII as CheckpointProventosFII_old
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'TEMPORÁRIO copia os modelos de FII de dentro do app bagogold para os novos modelos'

    def handle(self, *args, **options):
        FII.objects.all().delete()
        OperacaoFII.objects.all().delete()
        ProventoFII.objects.all().delete()
        UsoProventosOperacaoFII.objects.all().delete()
        ValorDiarioFII.objects.all().delete()
#         EventoFII.objects.all().delete()
        EventoIncorporacaoFII.objects.all().delete()
        EventoAgrupamentoFII.objects.all().delete()
        EventoDesdobramentoFII.objects.all().delete()
        CheckpointFII.objects.all().delete()
        CheckpointProventosFII.objects.all().delete()
           
        for fii in FII_old.objects.all().values():
            print fii
            FII.objects.create(**fii)
               
#         for evento in EventoFII_old.objects.all().values():
#             print evento
#             EventoFII.objects.create(**evento)
               
        for incorporacao in EventoIncorporacaoFII_old.objects.all().values():
            print incorporacao
            EventoIncorporacaoFII.objects.create(**incorporacao)
               
        for agrupamento in EventoAgrupamentoFII_old.objects.all().values():
            print agrupamento
            EventoAgrupamentoFII.objects.create(**agrupamento)
               
        for desdobramento in EventoDesdobramentoFII_old.objects.all().values():
            print desdobramento
            EventoDesdobramentoFII.objects.create(**desdobramento)
               
        for operacao in OperacaoFII_old.objects.all().values():
            print operacao
            OperacaoFII.objects.create(**operacao)
               
        for provento in ProventoFII_old.objects.all().values():
            print provento
            ProventoFII.objects.create(**provento)
               
        for uso_provento in UsoProventosOperacaoFII_old.objects.all().values():
            print uso_provento
            UsoProventosOperacaoFII.objects.create(**uso_provento)
               
        for valor_diario in ValorDiarioFII_old.objects.all().values():
            print valor_diario
            ValorDiarioFII.objects.create(**valor_diario)
            
        for chkp in CheckpointFII_old.objects.all().values():
            print chkp
            CheckpointFII.objects.create(**chkp)
             
        for chkp_prov in CheckpointProventosFII_old.objects.all().values():
            print chkp_prov
            CheckpointProventosFII.objects.create(**chkp_prov)

        for chkp in CheckpointFII_old.objects.all():
            print 'antigo', chkp.ano, chkp.investidor, chkp.quantidade, chkp.fii, CheckpointFII.objects.filter(investidor=chkp.investidor, ano=chkp.ano, 
                                                     quantidade=chkp.quantidade, preco_medio=chkp.preco_medio, fii__id=chkp.fii.id).exists()
                                                     
        for chkp in CheckpointFII.objects.all():
            print 'novo', chkp.ano, chkp.investidor, chkp.quantidade, chkp.fii, CheckpointFII_old.objects.filter(investidor=chkp.investidor, ano=chkp.ano, 
                                                     quantidade=chkp.quantidade, preco_medio=chkp.preco_medio, fii__id=chkp.fii.id).exists()
        