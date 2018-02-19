# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoCDB_RDB
from bagogold.cdb_rdb.models import HistoricoPorcentagemCDB_RDB
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
import datetime

# Preparar checkpoints para alterações em operações de CDB/RDB
@receiver(post_save, sender=DivisaoOperacaoCDB_RDB, dispatch_uid="operacao_cdb_rdb_divisao_criada_alterada")
def preparar_checkpointcdb_rdb(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.operacao.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    gerar_checkpoint_divisao_cdb_rdb(instance.divisao, instance.operacao.cdb_rdb, ano)
        
    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_divisao_cdb_rdb(instance.divisao, instance.operacao.cdb_rdb, prox_ano)
            
    
@receiver(post_delete, sender=DivisaoOperacaoCDB_RDB, dispatch_uid="operacao_cdb_rdb_divisao_apagada")
def preparar_checkpointcdb_rdb_delete(sender, instance, **kwargs):
    """
    Verifica ano da operação apagada
    """
    ano = instance.operacao.data.year
    """ 
    Altera checkpoint existente
    """
    gerar_checkpoint_divisao_cdb_rdb(instance.divisao, instance.operacao.cdb_rdb, ano)

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_divisao_cdb_rdb(instance.divisao, instance.operacao.cdb_rdb, prox_ano)
            

# Preparar checkpoints para alterações em histórico de porcentagem
@receiver(post_save, sender=HistoricoPorcentagemCDB_RDB, dispatch_uid="hist_porcent_cdb_rdb_divisao_criado_alterado")
def preparar_checkpoint_cdb_rdb_historico(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    for divisao in Divisao.objects.filter(id__in=DivisaoOperacaoCDB_RDB.objects.filter(operacao__cdb_rdb=instance.cdb_rdb, operacao__data__lt=instance.data) \
                                                    .order_by('divisao').distinct('divisao').values_list('divisao', flat=True)):
        gerar_checkpoint_divisao_cdb_rdb(divisao, instance.cdb_rdb, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_divisao_cdb_rdb(divisao, instance.cdb_rdb, prox_ano)
                
    
@receiver(post_save, sender=HistoricoPorcentagemCDB_RDB, dispatch_uid="hist_porcent_cdb_rdb_divisao_apagado")
def preparar_checkpoint_cdb_rdb_historico_delete(sender, instance, **kwargs):
    """
    Verifica ano do evento apagado
    """
    ano = instance.data.year
    """ 
    Altera checkpoints existentes
    """
    for divisao in Divisao.objects.filter(id__in=DivisaoOperacaoCDB_RDB.objects.filter(operacao__cdb_rdb=instance.cdb_rdb, operacao__data__lt=instance.data) \
                                                    .order_by('divisao').distinct('divisao').values_list('divisao', flat=True)):
        gerar_checkpoint_divisao_cdb_rdb(divisao, instance.cdb_rdb, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_divisao_cdb_rdb(divisao, instance.cdb_rdb, prox_ano)
                
                
            
def gerar_checkpoint_divisao_cdb_rdb(divisao, operacao, ano):
    qtd_restante = operacao.qtd_disponivel_venda_na_data(datetime.date(ano, 12, 31))
    qtd_atualizada = calcular_valor_operacao_cdb_rdb_ate_dia(operacao, datetime.date(ano, 12, 31), False)
    if qtd_restante != 0:
        CheckpointDivisaoCDB_RDB.objects.update_or_create(divisao=divisao, operacao=operacao, ano=ano, 
                                               defaults={'qtd_restante': qtd_restante, 'qtd_atualizada': qtd_atualizada})
    else:
        # Não existe checkpoint anterior e quantidade atual é igual a 0
        CheckpointDivisaoCDB_RDB.objects.filter(divisao=divisao, operacao=operacao, ano=ano).delete()
    
