# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
import datetime
from bagogold.cdb_rdb.models import OperacaoCDB_RDB

                
# Preparar checkpoints para alterações em operações de CDB/RDB
@receiver(post_save, sender=OperacaoCDB_RDB, dispatch_uid="operacao_cdb_rdb_criada_alterada")
def preparar_checkpoint_cdb_rdb(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    gerar_checkpoint_cdb_rdb(instance.investidor, instance.cdb_rdb, ano)
    
    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_cdb_rdb(instance.investidor, instance.cdb_rdb, prox_ano)
            
            # Se existe incorporação
            if incorporacao and incorporacao.data.year <= prox_ano:
                gerar_checkpoint_cdb_rdb(instance.investidor, incorporacao.novo_cdb_rdb, prox_ano)
                
            # Alterar checkpoint de poupança de proventos
            gerar_checkpoint_proventos_cdb_rdb(instance.investidor, prox_ano)
            
    
@receiver(post_delete, sender=Operacaocdb_rdb, dispatch_uid="operacao_cdb_rdb_apagada")
def preparar_checkpoint_cdb_rdb_delete(sender, instance, **kwargs):
    """
    Verifica ano da operação apagada
    """
    ano = instance.data.year
    """ 
    Altera checkpoint existente
    """
    gerar_checkpoint_cdb_rdb(instance.investidor, instance.cdb_rdb, ano)
    # Verificar se cdb_rdb é incorporado
    incorporacao = None if not EventoIncorporacaocdb_rdb.objects.filter(cdb_rdb=instance.cdb_rdb).exists() else EventoIncorporacaocdb_rdb.objects.get(cdb_rdb=instance.cdb_rdb)
    # Se existe incorporação
    if incorporacao and incorporacao.data.year == ano:
        gerar_checkpoint_cdb_rdb(instance.investidor, incorporacao.novo_cdb_rdb, ano)
        
    # Alterar checkpoint de poupança de proventos
    gerar_checkpoint_proventos_cdb_rdb(instance.investidor, ano)

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_cdb_rdb(instance.investidor, instance.cdb_rdb, prox_ano)
            
            # Se existe incorporação
            if incorporacao and incorporacao.data.year <= prox_ano:
                gerar_checkpoint_cdb_rdb(instance.investidor, incorporacao.novo_cdb_rdb, prox_ano)
                
            # Alterar checkpoint de poupança de proventos
            gerar_checkpoint_proventos_cdb_rdb(instance.investidor, prox_ano)

        
# Preparar checkpoints para alterações em histórico de porcentagem
@receiver(post_save, sender=EventoAgrupamentocdb_rdb, dispatch_uid="evento_agrupamento_criado_alterado")
def preparar_checkpoint_cdb_rdb_historico(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    # Verificar se cdb_rdb é incorporado
    incorporacao = None if not EventoIncorporacaocdb_rdb.objects.filter(cdb_rdb=instance.cdb_rdb).exists() else EventoIncorporacaocdb_rdb.objects.get(cdb_rdb=instance.cdb_rdb)
    for investidor in Investidor.objects.filter(id__in=Operacaocdb_rdb.objects.filter(cdb_rdb=instance.cdb_rdb, data__lt=instance.data) \
                                                .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
        gerar_checkpoint_cdb_rdb(investidor, instance.cdb_rdb, ano)
        # Se existe incorporação
        if incorporacao and incorporacao.data.year == ano:
            gerar_checkpoint_cdb_rdb(investidor, incorporacao.novo_cdb_rdb, ano)
            
        # Alterar checkpoint de poupança de proventos
        gerar_checkpoint_proventos_cdb_rdb(investidor, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_cdb_rdb(investidor, instance.cdb_rdb, prox_ano)
                
                # Se existe incorporação
                if incorporacao and incorporacao.data.year <= prox_ano:
                    gerar_checkpoint_cdb_rdb(investidor, incorporacao.novo_cdb_rdb, prox_ano)
                
                # Alterar checkpoint de poupança de proventos
                gerar_checkpoint_proventos_cdb_rdb(investidor, prox_ano)
            
    
@receiver(post_delete, sender=EventoAgrupamentocdb_rdb, dispatch_uid="evento_agrupamento_apagado")
def preparar_checkpoint_cdb_rdb_historico_delete(sender, instance, **kwargs):
    """
    Verifica ano do evento apagado
    """
    ano = instance.data.year
    """ 
    Altera checkpoints existentes
    """
    incorporacao = None if not EventoIncorporacaocdb_rdb.objects.filter(cdb_rdb=instance.cdb_rdb).exists() else EventoIncorporacaocdb_rdb.objects.get(cdb_rdb=instance.cdb_rdb)
    for investidor in Investidor.objects.filter(id__in=Operacaocdb_rdb.objects.filter(cdb_rdb=instance.cdb_rdb, data__lt=instance.data) \
                                                .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
        gerar_checkpoint_cdb_rdb(investidor, instance.cdb_rdb, ano)
        # Se existe incorporação
        if incorporacao and incorporacao.data.year == ano:
            gerar_checkpoint_cdb_rdb(investidor, instance.novo_cdb_rdb, ano)
        
        # Alterar checkpoint de poupança de proventos
        gerar_checkpoint_proventos_cdb_rdb(investidor, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_cdb_rdb(investidor, instance.cdb_rdb, prox_ano)
                
                # Se existe incorporação
                if incorporacao and incorporacao.data.year <= prox_ano:
                    gerar_checkpoint_cdb_rdb(investidor, incorporacao.novo_cdb_rdb, prox_ano)
                
                # Alterar checkpoint de poupança de proventos
                gerar_checkpoint_proventos_cdb_rdb(investidor, prox_ano)
            
            
def gerar_checkpoint_cdb_rdb(investidor, cdb_rdb, ano):
    quantidade = calcular_qtd_cdb_rdbs_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), cdb_rdb.ticker)
    preco_medio = calcular_preco_medio_cdb_rdbs_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), cdb_rdb.ticker)
    if Checkpointcdb_rdb.objects.filter(investidor=investidor, cdb_rdb=cdb_rdb, ano=ano-1).exclude(quantidade=0).exists() or quantidade != 0:
        Checkpointcdb_rdb.objects.update_or_create(investidor=investidor, cdb_rdb=cdb_rdb, ano=ano, 
                                           defaults={'quantidade': quantidade, 'preco_medio': preco_medio})
    else:
        # Não existe checkpoint anterior e quantidade atual é 0
        Checkpointcdb_rdb.objects.filter(investidor=investidor, cdb_rdb=cdb_rdb, ano=ano).delete()
    