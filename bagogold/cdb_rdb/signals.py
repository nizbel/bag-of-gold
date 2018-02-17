# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.cdb_rdb.models import OperacaoCDB_RDB, HistoricoPorcentagemCDB_RDB
from bagogold.cdb_rdb.utils import calcular_valor_operacao_cdb_rdb_ate_dia
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
import datetime

                
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
    if instance.tipo_operacao == 'C':
        gerar_checkpoint_cdb_rdb(instance, ano)
    elif instance.tipo_operacao == 'V':
        gerar_checkpoint_cdb_rdb(instance.operacao_compra_relacionada(), ano)
        
    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_cdb_rdb(instance, prox_ano)
            
    
@receiver(post_delete, sender=OperacaoCDB_RDB, dispatch_uid="operacao_cdb_rdb_apagada")
def preparar_checkpoint_cdb_rdb_delete(sender, instance, **kwargs):
    """
    Verifica ano da operação apagada
    """
    ano = instance.data.year
    """ 
    Altera checkpoint existente
    """
    if instance.tipo_operacao == 'C':
        gerar_checkpoint_cdb_rdb(instance, ano)
    elif instance.tipo_operacao == 'V':
        gerar_checkpoint_cdb_rdb(instance.operacao_compra_relacionada(), ano)

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_cdb_rdb(instance, prox_ano)
            
        
# Preparar checkpoints para alterações em histórico de porcentagem
@receiver(post_save, sender=HistoricoPorcentagemCDB_RDB, dispatch_uid="hist_porcent_cdb_rdb_criado_alterado")
def preparar_checkpoint_cdb_rdb_historico(sender, instance, created, **kwargs):
    """ 
    Cria novo checkpoint ou altera existente para as operações afetadas
    """
    # Todas podem ser afetadas
    for operacao in OperacaoCDB_RDB.objects.filter(cdb_rdb=instance.cdb_rdb, tipo_operacao='C'):
        ano = operacao.data.year
        gerar_checkpoint_cdb_rdb(operacao, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_cdb_rdb(operacao, prox_ano)
        
                
    
@receiver(post_delete, sender=HistoricoPorcentagemCDB_RDB, dispatch_uid="hist_porcent_cdb_rdb_apagado")
def preparar_checkpoint_cdb_rdb_historico_delete(sender, instance, **kwargs):
    """ 
    Altera checkpoints para as operações afetadas
    """
    # Todas podem ser afetadas
    for operacao in OperacaoCDB_RDB.objects.filter(cdb_rdb=instance.cdb_rdb, tipo_operacao='C'):
        ano = operacao.data.year
        gerar_checkpoint_cdb_rdb(operacao, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_cdb_rdb(operacao, prox_ano)
                
            
def gerar_checkpoint_cdb_rdb(operacao, ano):
    qtd_restante = operacao.quantidade_disponivel_venda_na_data(datetime.date(ano, 12, 31))
    qtd_atualizada = calcular_valor_operacao_cdb_rdb_ate_dia(operacao, datetime.date(ano, 12, 31))
    if qtd_restante != 0:
        Checkpointcdb_rdb.objects.update_or_create(operacao=operacao, ano=ano, 
                                           defaults={'qtd_restante': qtd_restante, 'qtd_atualizada': qtd_atualizada})
    else:
        # Não existe checkpoint anterior e quantidade atual é 0
        Checkpointcdb_rdb.objects.filter(operacao=operacao, ano=ano).delete()
    