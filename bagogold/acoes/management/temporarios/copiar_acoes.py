# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoacao
from bagogold.bagogold.models.acao import acao as acao_old, \
    Operacaoacao as Operacaoacao_old, Proventoacao as Proventoacao_old, \
    UsoProventosOperacaoacao as UsoProventosOperacaoacao_old, \
    ValorDiarioacao as ValorDiarioacao_old, \
    EventoIncorporacaoacao as EventoIncorporacaoacao_old, \
    EventoAgrupamentoacao as EventoAgrupamentoacao_old, \
    EventoDesdobramentoacao as EventoDesdobramentoacao_old, \
    Checkpointacao as Checkpointacao_old, Historicoacao as Historicoacao_old, \
    CheckpointProventosacao as CheckpointProventosacao_old
from bagogold.bagogold.signals.divisao_acao import \
    preparar_checkpointproventoacao_delete as divisao_chkp_prov_delete, \
    preparar_checkpointacao as divisao_chkp, \
    preparar_checkpointacao_evento as divisao_chkp_evento, \
    preparar_checkpointproventoacao as divisao_chkp_prov, \
    preparar_checkpointacao_delete as divisao_chkp_delete, \
    preparar_checkpointacao_evento_delete as divisao_chkp_evento_delete
from bagogold.acao.models import acao, Operacaoacao, Proventoacao, \
    UsoProventosOperacaoacao, ValorDiarioacao, EventoIncorporacaoacao, \
    EventoAgrupamentoacao, EventoDesdobramentoacao, Checkpointacao, \
    CheckpointProventosacao, Historicoacao
from bagogold.acao.signals import preparar_checkpointproventoacao_delete, \
    preparar_checkpointacao, preparar_checkpointacao_evento, \
    preparar_checkpointproventoacao, preparar_checkpointacao_delete, \
    preparar_checkpointacao_evento_delete
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.signals import post_save, post_delete


class Command(BaseCommand):
    help = 'TEMPORÁRIO copia os modelos de Ações de dentro do app bagogold para os novos modelos'

    def handle(self, *args, **options):
        # acao
        if not post_save.disconnect(sender=Operacaoacao, dispatch_uid='operacaoacao_criada_alterada'):
            print 'operacaoacao_criada_alterada'
            return
        if not post_save.disconnect(sender=Proventoacao, dispatch_uid='proventoacao_criado_alterado'):
            print 'proventoacao_criado_alterado'
            return
        if not post_save.disconnect(sender=EventoAgrupamentoacao, dispatch_uid='evento_agrupamento_criado_alterado') or\
        not post_save.disconnect(sender=EventoDesdobramentoacao, dispatch_uid='evento_desdobramento_criado_alterado') or\
        not post_save.disconnect(sender=EventoIncorporacaoacao, dispatch_uid='evento_incorporacao_criado_alterado'):
            print 'evento_agrupamento_criado_alterado'
            return
        # Divisão
        if not post_save.disconnect(sender=DivisaoOperacaoacao, dispatch_uid='operacaoacao_divisao_criada_alterada'):
            print 'operacaoacao_divisao_criado_alterado'
            return
        if not post_save.disconnect(sender=Proventoacao, dispatch_uid='proventoacao_divisao_criado_alterado'):
            print 'proventoacao_divisao_criado_alterado'
            return
        if not post_save.disconnect(sender=EventoAgrupamentoacao, dispatch_uid='evento_agrupamento_divisao_criado_alterado') or\
        not post_save.disconnect(sender=EventoDesdobramentoacao, dispatch_uid='evento_desdobramento_divisao_criado_alterado') or\
        not post_save.disconnect(sender=EventoIncorporacaoacao, dispatch_uid='evento_incorporacao_divisao_criado_alterado'):
            print 'evento_agrupamento_divisao_criado_alterado'
            return
        # acao - delete
        if not post_delete.disconnect(sender=Operacaoacao, dispatch_uid='operacaoacao_apagada'):
            print 'operacaoacao_apagada'
            return
        if not post_delete.disconnect(sender=Proventoacao, dispatch_uid='proventoacao_apagado'):
            print 'proventoacao_apagado'
            return
        if not post_delete.disconnect(sender=EventoAgrupamentoacao, dispatch_uid='evento_agrupamento_apagado') or\
        not post_delete.disconnect(sender=EventoDesdobramentoacao, dispatch_uid='evento_desdobramento_apagado') or\
        not post_delete.disconnect(sender=EventoIncorporacaoacao, dispatch_uid='evento_incorporacao_apagado'):
            print 'evento_agrupamento_apagado'
            return
        # Divisão - delete
        if not post_delete.disconnect(sender=DivisaoOperacaoacao, dispatch_uid='operacaoacao_divisao_apagada'):
            print 'operacaoacao_divisao_apagada'
            return
        if not post_delete.disconnect(sender=Proventoacao, dispatch_uid='proventoacao_divisao_apagado'):
            print 'proventoacao_divisao_apagado'
            return
        if not post_delete.disconnect(sender=EventoAgrupamentoacao, dispatch_uid='evento_agrupamento_divisao_apagado') or\
        not post_delete.disconnect(sender=EventoDesdobramentoacao, dispatch_uid='evento_desdobramento_divisao_apagado') or\
        not post_delete.disconnect(sender=EventoIncorporacaoacao, dispatch_uid='evento_incorporacao_divisao_apagado'):
            print 'evento_agrupamento_divisao_apagado'
            return
        
        try:
            with transaction.atomic():
                acao.objects.all().delete()
                Operacaoacao.objects.all().delete()
                Proventoacao.objects.all().delete()
                UsoProventosOperacaoacao.objects.all().delete()
                Historicoacao.objects.all().delete()
                ValorDiarioacao.objects.all().delete()
                EventoIncorporacaoacao.objects.all().delete()
                EventoAgrupamentoacao.objects.all().delete()
                EventoDesdobramentoacao.objects.all().delete()
                Checkpointacao.objects.all().delete()
                CheckpointProventosacao.objects.all().delete()
                   
                for acao in acao_old.objects.all().values():
                    print acao
                    acao.objects.create(**acao)
                       
                for operacao in Operacaoacao_old.objects.all().values():
                    print operacao
                    Operacaoacao.objects.create(**operacao)
                       
                for provento in Proventoacao_old.gerador_objects.all().values():
                    print provento
                    Proventoacao.objects.create(**provento)
                       
                for uso_provento in UsoProventosOperacaoacao_old.objects.all().values():
                    print uso_provento
                    UsoProventosOperacaoacao.objects.create(**uso_provento)
                       
                for historico in Historicoacao_old.objects.all().values():
                    print historico
                    Historicoacao.objects.create(**historico)
                    
                for valor_diario in ValorDiarioacao_old.objects.all().values():
                    print valor_diario
                    ValorDiarioacao.objects.create(**valor_diario)
                
                for incorporacao in EventoIncorporacaoacao_old.objects.all().values():
                    print incorporacao
                    EventoIncorporacaoacao.objects.create(**incorporacao)
                       
                for agrupamento in EventoAgrupamentoacao_old.objects.all().values():
                    print agrupamento
                    EventoAgrupamentoacao.objects.create(**agrupamento)
                       
                for desdobramento in EventoDesdobramentoacao_old.objects.all().values():
                    print desdobramento
                    EventoDesdobramentoacao.objects.create(**desdobramento)
                    
                for chkp in Checkpointacao_old.objects.all().values():
                    print chkp
                    Checkpointacao.objects.create(**chkp)
                      
                for chkp_prov in CheckpointProventosacao_old.objects.all().values():
                    print chkp_prov
                    CheckpointProventosacao.objects.create(**chkp_prov)
                
        except Exception as e:
            print e
        
        # Reconectar signals
        # acao
        post_save.connect(preparar_checkpointacao, sender=Operacaoacao, dispatch_uid='operacaoacao_criada_alterada')
        post_save.connect(preparar_checkpointproventoacao, sender=Proventoacao, dispatch_uid='proventoacao_criado_alterado')
        post_save.connect(preparar_checkpointacao_evento, sender=EventoAgrupamentoacao, dispatch_uid='evento_agrupamento_criado_alterado')
        post_save.connect(preparar_checkpointacao_evento, sender=EventoDesdobramentoacao, dispatch_uid='evento_desdobramento_criado_alterado')
        post_save.connect(preparar_checkpointacao_evento, sender=EventoIncorporacaoacao, dispatch_uid='evento_incorporacao_criado_alterado')
        # Divisão
        post_save.connect(divisao_chkp, sender=DivisaoOperacaoacao, dispatch_uid='operacaoacao_divisao_criada_alterada')
        post_save.connect(divisao_chkp_prov, sender=Proventoacao, dispatch_uid='proventoacao_divisao_criado_alterado')
        post_save.connect(divisao_chkp_evento, sender=EventoAgrupamentoacao, dispatch_uid='evento_agrupamento_divisao_criado_alterado')
        post_save.connect(divisao_chkp_evento, sender=EventoDesdobramentoacao, dispatch_uid='evento_desdobramento_divisao_criado_alterado')
        post_save.connect(divisao_chkp_evento, sender=EventoIncorporacaoacao, dispatch_uid='evento_incorporacao_divisao_criado_alterado')
        # acao - delete
        post_delete.connect(preparar_checkpointacao_delete, sender=Operacaoacao, dispatch_uid='operacaoacao_apagada')
        post_delete.connect(preparar_checkpointproventoacao_delete, sender=Proventoacao, dispatch_uid='proventoacao_apagado')
        post_delete.connect(preparar_checkpointacao_evento_delete, sender=EventoAgrupamentoacao, dispatch_uid='evento_agrupamento_apagado')
        post_delete.connect(preparar_checkpointacao_evento_delete, sender=EventoDesdobramentoacao, dispatch_uid='evento_desdobramento_apagado')
        post_delete.connect(preparar_checkpointacao_evento_delete, sender=EventoIncorporacaoacao, dispatch_uid='evento_incorporacao_apagado')
        # Divisão - delete
        post_delete.connect(divisao_chkp_delete, sender=DivisaoOperacaoacao, dispatch_uid='operacaoacao_divisao_apagada')
        post_delete.connect(divisao_chkp_prov_delete, sender=Proventoacao, dispatch_uid='proventoacao_divisao_apagado')
        post_delete.connect(divisao_chkp_evento_delete, sender=EventoAgrupamentoacao, dispatch_uid='evento_agrupamento_divisao_apagado')
        post_delete.connect(divisao_chkp_evento_delete, sender=EventoDesdobramentoacao, dispatch_uid='evento_desdobramento_divisao_apagado')
        post_delete.connect(divisao_chkp_evento_delete, sender=EventoIncorporacaoacao, dispatch_uid='evento_incorporacao_divisao_apagado')
        