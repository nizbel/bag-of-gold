# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoLetraCambio, \
    CheckpointDivisaoLetraCambio
from bagogold.lc.models import HistoricoPorcentagemLetraCambio
from bagogold.lc.utils import calcular_valor_op_lc_ate_dia_por_divisao
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
import datetime

# Preparar checkpoints para alterações em operações de Letra de Câmbio
@receiver(post_save, sender=DivisaoOperacaoLetraCambio, dispatch_uid="operacao_lc_divisao_criada_alterada")
def preparar_checkpointlc(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.operacao.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    # Definir operacao
    if instance.operacao.tipo_operacao == 'C':
        divisao_operacao = instance
    elif instance.operacao.tipo_operacao == 'V':
        divisao_operacao = instance.divisao_operacao_compra_relacionada()
    gerar_checkpoint_divisao_lc(divisao_operacao, ano)
        
    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_divisao_lc(divisao_operacao, prox_ano)
            
    
@receiver(post_delete, sender=DivisaoOperacaoLetraCambio, dispatch_uid="operacao_lc_divisao_apagada")
def preparar_checkpointlc_delete(sender, instance, **kwargs):
    """
    Verifica ano da operação apagada
    """
    ano = instance.operacao.data.year
    """ 
    Altera checkpoint existente
    """
    # Definir operacao
    if instance.operacao.tipo_operacao == 'C':
        return
    elif instance.operacao.tipo_operacao == 'V':
        divisao_operacao = instance.divisao_operacao_compra_relacionada()
    gerar_checkpoint_divisao_lc(divisao_operacao, ano)
  
    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_divisao_lc(divisao_operacao, prox_ano)
            

# Preparar checkpoints para alterações em histórico de porcentagem
@receiver(post_save, sender=HistoricoPorcentagemLetraCambio, dispatch_uid="hist_porcent_lc_divisao_criado_alterado")
def preparar_checkpoint_lc_historico(sender, instance, created, **kwargs):
    """
    Altera checkpoints para as operações afetadas
    """
    # Todas podem ser afetadas
    for divisao_operacao in DivisaoOperacaoLetraCambio.objects.filter(operacao__lc=instance.lc, operacao__tipo_operacao='C'):
        ano = divisao_operacao.operacao.data.year
        gerar_checkpoint_divisao_lc(divisao_operacao, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_divisao_lc(divisao_operacao, prox_ano)
                
        # TESTE
#         ano = operacao.data.year
#         gerar_checkpoint_lc(operacao, ano)
# 
#         """
#         Verificar se existem anos posteriores
#         """
#         if ano != datetime.date.today().year:
#             for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#                 gerar_checkpoint_lc(operacao, prox_ano)
                
    
@receiver(post_save, sender=HistoricoPorcentagemLetraCambio, dispatch_uid="hist_porcent_lc_divisao_apagado")
def preparar_checkpoint_lc_historico_delete(sender, instance, **kwargs):
    """
    Verifica ano do evento apagado
    """
    # Todas podem ser afetadas
    for divisao_operacao in DivisaoOperacaoLetraCambio.objects.filter(operacao__lc=instance.lc, operacao__tipo_operacao='C'):
        ano = divisao_operacao.operacao.data.year
        gerar_checkpoint_divisao_lc(divisao_operacao, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_divisao_lc(divisao_operacao, prox_ano)
                
            
def gerar_checkpoint_divisao_lc(divisao_operacao, ano):
    qtd_restante = divisao_operacao.qtd_disponivel_venda_na_data(datetime.date(ano, 12, 31))
    qtd_atualizada = calcular_valor_op_lc_ate_dia_por_divisao(divisao_operacao, datetime.date(ano, 12, 31), False)
    if qtd_restante != 0:
        CheckpointDivisaoLetraCambio.objects.update_or_create(divisao_operacao=divisao_operacao, ano=ano, 
                                               defaults={'qtd_restante': qtd_restante, 'qtd_atualizada': qtd_atualizada})
    else:
        # Não existe checkpoint anterior e quantidade atual é igual a 0
        CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao=divisao_operacao, ano=ano).delete()
    
