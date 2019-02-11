# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII
from bagogold.bagogold.models.fii import FII as FII_old, \
    OperacaoFII as OperacaoFII_old, ProventoFII as ProventoFII_old, \
    UsoProventosOperacaoFII as UsoProventosOperacaoFII_old, \
    ValorDiarioFII as ValorDiarioFII_old, \
    EventoIncorporacaoFII as EventoIncorporacaoFII_old, \
    EventoAgrupamentoFII as EventoAgrupamentoFII_old, \
    EventoDesdobramentoFII as EventoDesdobramentoFII_old, \
    CheckpointFII as CheckpointFII_old, HistoricoFII as HistoricoFII_old, \
    CheckpointProventosFII as CheckpointProventosFII_old
from bagogold.bagogold.signals.divisao_fii import \
    preparar_checkpointproventofii_delete as divisao_chkp_prov_delete, \
    preparar_checkpointfii as divisao_chkp, \
    preparar_checkpointfii_evento as divisao_chkp_evento, \
    preparar_checkpointproventofii as divisao_chkp_prov, \
    preparar_checkpointfii_delete as divisao_chkp_delete, \
    preparar_checkpointfii_evento_delete as divisao_chkp_evento_delete
from bagogold.fii.models import FII, OperacaoFII, ProventoFII, \
    UsoProventosOperacaoFII, ValorDiarioFII, EventoIncorporacaoFII, \
    EventoAgrupamentoFII, EventoDesdobramentoFII, CheckpointFII, \
    CheckpointProventosFII, HistoricoFII
from bagogold.fii.signals import preparar_checkpointproventofii_delete, \
    preparar_checkpointfii, preparar_checkpointfii_evento, \
    preparar_checkpointproventofii, preparar_checkpointfii_delete, \
    preparar_checkpointfii_evento_delete
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save, post_delete


class Command(BaseCommand):
    help = 'TEMPORÁRIO copia os modelos de Ações de dentro do app bagogold para os novos modelos'

    def handle(self, *args, **options):
        # FII
        if not post_save.disconnect(sender=OperacaoFII, dispatch_uid='operacaofii_criada_alterada'):
            print 'operacaofii_criada_alterada'
            return
        if not post_save.disconnect(sender=ProventoFII, dispatch_uid='proventofii_criado_alterado'):
            print 'proventofii_criado_alterado'
            return
        if not post_save.disconnect(sender=EventoAgrupamentoFII, dispatch_uid='evento_agrupamento_criado_alterado') or\
        not post_save.disconnect(sender=EventoDesdobramentoFII, dispatch_uid='evento_desdobramento_criado_alterado') or\
        not post_save.disconnect(sender=EventoIncorporacaoFII, dispatch_uid='evento_incorporacao_criado_alterado'):
            print 'evento_agrupamento_criado_alterado'
            return
        # Divisão
        if not post_save.disconnect(sender=DivisaoOperacaoFII, dispatch_uid='operacaofii_divisao_criada_alterada'):
            print 'operacaofii_divisao_criado_alterado'
            return
        if not post_save.disconnect(sender=ProventoFII, dispatch_uid='proventofii_divisao_criado_alterado'):
            print 'proventofii_divisao_criado_alterado'
            return
        if not post_save.disconnect(sender=EventoAgrupamentoFII, dispatch_uid='evento_agrupamento_divisao_criado_alterado') or\
        not post_save.disconnect(sender=EventoDesdobramentoFII, dispatch_uid='evento_desdobramento_divisao_criado_alterado') or\
        not post_save.disconnect(sender=EventoIncorporacaoFII, dispatch_uid='evento_incorporacao_divisao_criado_alterado'):
            print 'evento_agrupamento_divisao_criado_alterado'
            return
        # FII - delete
        if not post_delete.disconnect(sender=OperacaoFII, dispatch_uid='operacaofii_apagada'):
            print 'operacaofii_apagada'
            return
        if not post_delete.disconnect(sender=ProventoFII, dispatch_uid='proventofii_apagado'):
            print 'proventofii_apagado'
            return
        if not post_delete.disconnect(sender=EventoAgrupamentoFII, dispatch_uid='evento_agrupamento_apagado') or\
        not post_delete.disconnect(sender=EventoDesdobramentoFII, dispatch_uid='evento_desdobramento_apagado') or\
        not post_delete.disconnect(sender=EventoIncorporacaoFII, dispatch_uid='evento_incorporacao_apagado'):
            print 'evento_agrupamento_apagado'
            return
        # Divisão - delete
        if not post_delete.disconnect(sender=DivisaoOperacaoFII, dispatch_uid='operacaofii_divisao_apagada'):
            print 'operacaofii_divisao_apagada'
            return
        if not post_delete.disconnect(sender=ProventoFII, dispatch_uid='proventofii_divisao_apagado'):
            print 'proventofii_divisao_apagado'
            return
        if not post_delete.disconnect(sender=EventoAgrupamentoFII, dispatch_uid='evento_agrupamento_divisao_apagado') or\
        not post_delete.disconnect(sender=EventoDesdobramentoFII, dispatch_uid='evento_desdobramento_divisao_apagado') or\
        not post_delete.disconnect(sender=EventoIncorporacaoFII, dispatch_uid='evento_incorporacao_divisao_apagado'):
            print 'evento_agrupamento_divisao_apagado'
            return
        
        try:
            with transaction.atomic():
                FII.objects.all().delete()
                OperacaoFII.objects.all().delete()
                ProventoFII.objects.all().delete()
                UsoProventosOperacaoFII.objects.all().delete()
                HistoricoFII.objects.all().delete()
                ValorDiarioFII.objects.all().delete()
                EventoIncorporacaoFII.objects.all().delete()
                EventoAgrupamentoFII.objects.all().delete()
                EventoDesdobramentoFII.objects.all().delete()
                CheckpointFII.objects.all().delete()
                CheckpointProventosFII.objects.all().delete()
                   
                for fii in FII_old.objects.all().values():
                    print fii
                    FII.objects.create(**fii)
                       
                for operacao in OperacaoFII_old.objects.all().values():
                    print operacao
                    OperacaoFII.objects.create(**operacao)
                       
                for provento in ProventoFII_old.gerador_objects.all().values():
                    print provento
                    ProventoFII.objects.create(**provento)
                       
                for uso_provento in UsoProventosOperacaoFII_old.objects.all().values():
                    print uso_provento
                    UsoProventosOperacaoFII.objects.create(**uso_provento)
                       
                for historico in HistoricoFII_old.objects.all().values():
                    print historico
                    HistoricoFII.objects.create(**historico)
                    
                for valor_diario in ValorDiarioFII_old.objects.all().values():
                    print valor_diario
                    ValorDiarioFII.objects.create(**valor_diario)
                
                for incorporacao in EventoIncorporacaoFII_old.objects.all().values():
                    print incorporacao
                    EventoIncorporacaoFII.objects.create(**incorporacao)
                       
                for agrupamento in EventoAgrupamentoFII_old.objects.all().values():
                    print agrupamento
                    EventoAgrupamentoFII.objects.create(**agrupamento)
                       
                for desdobramento in EventoDesdobramentoFII_old.objects.all().values():
                    print desdobramento
                    EventoDesdobramentoFII.objects.create(**desdobramento)
                    
                for chkp in CheckpointFII_old.objects.all().values():
                    print chkp
                    CheckpointFII.objects.create(**chkp)
                      
                for chkp_prov in CheckpointProventosFII_old.objects.all().values():
                    print chkp_prov
                    CheckpointProventosFII.objects.create(**chkp_prov)
                
        except Exception as e:
            print e
        
        # Reconectar signals
        # FII
        post_save.connect(preparar_checkpointfii, sender=OperacaoFII, dispatch_uid='operacaofii_criada_alterada')
        post_save.connect(preparar_checkpointproventofii, sender=ProventoFII, dispatch_uid='proventofii_criado_alterado')
        post_save.connect(preparar_checkpointfii_evento, sender=EventoAgrupamentoFII, dispatch_uid='evento_agrupamento_criado_alterado')
        post_save.connect(preparar_checkpointfii_evento, sender=EventoDesdobramentoFII, dispatch_uid='evento_desdobramento_criado_alterado')
        post_save.connect(preparar_checkpointfii_evento, sender=EventoIncorporacaoFII, dispatch_uid='evento_incorporacao_criado_alterado')
        # Divisão
        post_save.connect(divisao_chkp, sender=DivisaoOperacaoFII, dispatch_uid='operacaofii_divisao_criada_alterada')
        post_save.connect(divisao_chkp_prov, sender=ProventoFII, dispatch_uid='proventofii_divisao_criado_alterado')
        post_save.connect(divisao_chkp_evento, sender=EventoAgrupamentoFII, dispatch_uid='evento_agrupamento_divisao_criado_alterado')
        post_save.connect(divisao_chkp_evento, sender=EventoDesdobramentoFII, dispatch_uid='evento_desdobramento_divisao_criado_alterado')
        post_save.connect(divisao_chkp_evento, sender=EventoIncorporacaoFII, dispatch_uid='evento_incorporacao_divisao_criado_alterado')
        # FII - delete
        post_delete.connect(preparar_checkpointfii_delete, sender=OperacaoFII, dispatch_uid='operacaofii_apagada')
        post_delete.connect(preparar_checkpointproventofii_delete, sender=ProventoFII, dispatch_uid='proventofii_apagado')
        post_delete.connect(preparar_checkpointfii_evento_delete, sender=EventoAgrupamentoFII, dispatch_uid='evento_agrupamento_apagado')
        post_delete.connect(preparar_checkpointfii_evento_delete, sender=EventoDesdobramentoFII, dispatch_uid='evento_desdobramento_apagado')
        post_delete.connect(preparar_checkpointfii_evento_delete, sender=EventoIncorporacaoFII, dispatch_uid='evento_incorporacao_apagado')
        # Divisão - delete
        post_delete.connect(divisao_chkp_delete, sender=DivisaoOperacaoFII, dispatch_uid='operacaofii_divisao_apagada')
        post_delete.connect(divisao_chkp_prov_delete, sender=ProventoFII, dispatch_uid='proventofii_divisao_apagado')
        post_delete.connect(divisao_chkp_evento_delete, sender=EventoAgrupamentoFII, dispatch_uid='evento_agrupamento_divisao_apagado')
        post_delete.connect(divisao_chkp_evento_delete, sender=EventoDesdobramentoFII, dispatch_uid='evento_desdobramento_divisao_apagado')
        post_delete.connect(divisao_chkp_evento_delete, sender=EventoIncorporacaoFII, dispatch_uid='evento_incorporacao_divisao_apagado')
        