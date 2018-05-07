# # -*- coding: utf-8 -*-
# from bagogold.lc.models import OperacaoLetraCambio, \
#     HistoricoPorcentagemLetraCambio, CheckpointLetraCambio, OperacaoVendaLetraCambio
# from bagogold.lc.utils import calcular_valor_operacao_lc_ate_dia
# from django.db.models.signals import post_save, post_delete
# from django.dispatch.dispatcher import receiver
# import datetime
# 
#                 
# # Preparar checkpoints para alterações em operações de CDB/RDB
# @receiver(post_save, sender=OperacaoLetraCambio, dispatch_uid="operacao_lc_compra_criada_alterada")
# @receiver(post_save, sender=OperacaoVendaLetraCambio, dispatch_uid="operacao_lc_venda_criada_alterada")
# def preparar_checkpoint_lc(sender, instance, created, **kwargs):
#     """
#     Verifica ano da operação alterada
#     """
#     ano = instance.data.year
#     """ 
#     Cria novo checkpoint ou altera existente
#     """
#     # Definir operacao
#     if sender == OperacaoLetraCambio:
#         if instance.tipo_operacao == 'C':
#             operacao = instance
#         elif instance.tipo_operacao == 'V' and not created:
#             operacao = instance.operacao_compra_relacionada()
#         else:
#             return
#     elif sender == OperacaoVendaLetraCambio:
#         if created:
#             operacao = instance.operacao_compra
#         else:
#             return
#     gerar_checkpoint_lc(operacao, ano)
#         
#     """
#     Verificar se existem anos posteriores
#     """
#     if ano != datetime.date.today().year:
#         for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#             gerar_checkpoint_lc(operacao, prox_ano)
#             
#     
# @receiver(post_delete, sender=OperacaoVendaLetraCambio, dispatch_uid="operacao_lc_venda_apagada")
# def preparar_checkpoint_lc_delete(sender, instance, **kwargs):
#     """
#     Verifica ano da operação apagada
#     """
#     ano = instance.data.year
#     """ 
#     Altera checkpoint existente
#     """
#     # Definir operacao
#     operacao = instance.operacao_compra
#     
#     gerar_checkpoint_lc(operacao, ano)
# 
#     """
#     Verificar se existem anos posteriores
#     """
#     if ano != datetime.date.today().year:
#         for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#             gerar_checkpoint_lc(operacao, prox_ano)
#             
#         
# # Preparar checkpoints para alterações em histórico de porcentagem
# @receiver(post_save, sender=HistoricoPorcentagemLetraCambio, dispatch_uid="hist_porcent_lc_criado_alterado")
# def preparar_checkpoint_lc_historico(sender, instance, created, **kwargs):
#     """ 
#     Cria novo checkpoint ou altera existente para as operações afetadas
#     """
#     # Todas podem ser afetadas
#     for operacao in OperacaoLetraCambio.objects.filter(lc=instance.lc, tipo_operacao='C'):
#         ano = operacao.data.year
#         gerar_checkpoint_lc(operacao, ano)
# 
#         """
#         Verificar se existem anos posteriores
#         """
#         if ano != datetime.date.today().year:
#             for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#                 gerar_checkpoint_lc(operacao, prox_ano)
#         
#     
# @receiver(post_delete, sender=HistoricoPorcentagemLetraCambio, dispatch_uid="hist_porcent_lc_apagado")
# def preparar_checkpoint_lc_historico_delete(sender, instance, **kwargs):
#     """ 
#     Altera checkpoints para as operações afetadas
#     """
#     # Todas podem ser afetadas
#     for operacao in OperacaoLetraCambio.objects.filter(lc=instance.lc, tipo_operacao='C'):
#         ano = operacao.data.year
#         gerar_checkpoint_lc(operacao, ano)
# 
#         """
#         Verificar se existem anos posteriores
#         """
#         if ano != datetime.date.today().year:
#             for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#                 gerar_checkpoint_lc(operacao, prox_ano)
#                 
#             
# def gerar_checkpoint_lc(operacao, ano):
#     qtd_restante = operacao.qtd_disponivel_venda_na_data(datetime.date(ano, 12, 31))
#     qtd_atualizada = calcular_valor_operacao_lc_ate_dia(operacao, datetime.date(ano, 12, 31), False)
#     if qtd_restante != 0:
#         CheckpointLetraCambio.objects.update_or_create(operacao=operacao, ano=ano, 
#                                            defaults={'qtd_restante': qtd_restante, 'qtd_atualizada': qtd_atualizada})
#     else:
#         # Não existe checkpoint anterior e quantidade atual é 0
#         CheckpointLetraCambio.objects.filter(operacao=operacao, ano=ano).delete()
#     