# # -*- coding: utf-8 -*-
# import datetime
#  
# from django.db.models.signals import post_save, post_delete
# from django.dispatch.dispatcher import receiver
#  
# from bagogold.bagogold.models.divisoes import DivisaoOperacaoAcao
# from bagogold.bagogold.models.investidores import Investidor
# from bagogold.acoes.models import ProventoAcao, OperacaoAcao, CheckpointProventosAcao, \
#     CheckpointAcao, EventoAgrupamentoAcao, EventoDesdobramentoAcao, \
#     EventoIncorporacaoAcao, UsoProventosOperacaoAcao
# from bagogold.acao.utils import calcular_poupanca_prov_acao_ate_dia, \
#     calcular_qtd_acaos_ate_dia_por_ticker, \
#     calcular_preco_medio_acaos_ate_dia_por_ticker
#  
#  
# # Preparar checkpoints para alterações em proventos de ações
# @receiver(post_save, sender=Provento, dispatch_uid="proventoacao_criado_alterado")
# def preparar_checkpointproventoacao(sender, instance, created, **kwargs):
#     if instance.oficial_bovespa:
#         """
#         Verifica ano da data de pagamento
#         """
#         ano = instance.data_pagamento.year
#         """ 
#         Cria novo checkpoint ou altera existente
#         """
#         for investidor in Investidor.objects.filter(id__in=OperacaoAcao.objects.filter(acao=instance.acao, data__lt=instance.data_ex) \
#                                                     .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
#             gerar_checkpoint_proventos_acao(investidor, ano)
#             # Se amortização verificar checkpoint de quantidade
#             if instance.tipo_provento == 'A':
#                 gerar_checkpoint_acao(investidor, instance.acao, ano)
#                  
#                 # Verificar se Acao é incorporado
#                 incorporacao = None if not EventoIncorporacaoAcao.objects.filter(acao=instance.acao).exists() else EventoIncorporacaoAcao.objects.get(acao=instance.acao)
#                 # Se existe incorporação
#                 if incorporacao and incorporacao.data.year == ano:
#                     gerar_checkpoint_acao(investidor, incorporacao.novo_acao, ano)
#      
#             """
#             Verificar se existem anos posteriores
#             """
#             if ano != datetime.date.today().year:
#                 for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#                     gerar_checkpoint_proventos_acao(investidor, prox_ano)
#                     # Se amortização verificar checkpoint de quantidade
#                     if instance.tipo_provento == 'A':
#                         gerar_checkpoint_acao(investidor, instance.acao, prox_ano)
#              
#                         # Se existe incorporação
#                         if incorporacao and incorporacao.data.year <= prox_ano:
#                             gerar_checkpoint_acao(investidor, incorporacao.novo_acao, prox_ano)
#  
# @receiver(post_delete, sender=ProventoAcao, dispatch_uid="proventoacao_apagado")
# def preparar_checkpointproventoacao_delete(sender, instance, **kwargs):
#     if instance.oficial_bovespa:
#         """
#         Verifica ano da data de pagamento do provento apagado
#         """
#         ano = instance.data_pagamento.year
#         """ 
#         Altera checkpoints existentes
#         """
#         for investidor in Investidor.objects.filter(id__in=OperacaoAcao.objects.filter(acao=instance.acao, data__lt=instance.data_ex) \
#                                                     .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
#             gerar_checkpoint_proventos_acao(investidor, ano)
#             # Se amortização verificar checkpoint de quantidade
#             if instance.tipo_provento == 'A':
#                 gerar_checkpoint_acao(investidor, instance.acao, ano)
#                  
#                 # Verificar se Acao é incorporado
#                 incorporacao = None if not EventoIncorporacaoAcao.objects.filter(acao=instance.acao).exists() else EventoIncorporacaoAcao.objects.get(acao=instance.acao)
#                 # Se existe incorporação
#                 if incorporacao and incorporacao.data.year == ano:
#                     gerar_checkpoint_acao(investidor, incorporacao.novo_acao, ano)
#      
#             """
#             Verificar se existem anos posteriores
#             """
#             if ano != datetime.date.today().year:
#                 for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#                     gerar_checkpoint_proventos_acao(investidor, prox_ano)
#                     # Se amortização verificar checkpoint de quantidade
#                     if instance.tipo_provento == 'A':
#                         gerar_checkpoint_acao(investidor, instance.acao, prox_ano)
#              
#                         # Se existe incorporação
#                         if incorporacao and incorporacao.data.year <= prox_ano:
#                             gerar_checkpoint_acao(investidor, incorporacao.novo_acao, prox_ano)
#      
#                  
# # Preparar checkpoints para alterações em operações de Acao
# @receiver(post_save, sender=OperacaoAcao, dispatch_uid="operacaoacao_criada_alterada")
# def preparar_checkpointacao(sender, instance, created, **kwargs):
#     """
#     Verifica ano da operação alterada
#     """
#     ano = instance.data.year
#     """ 
#     Cria novo checkpoint ou altera existente
#     """
#     gerar_checkpoint_acao(instance.investidor, instance.acao, ano)
#     # Verificar se Acao é incorporado
#     incorporacao = None if not EventoIncorporacaoAcao.objects.filter(acao=instance.acao).exists() else EventoIncorporacaoAcao.objects.get(acao=instance.acao)
#     # Se existe incorporação
#     if incorporacao and incorporacao.data.year == ano:
#         gerar_checkpoint_acao(instance.investidor, incorporacao.novo_acao, ano)
#          
#     # Alterar checkpoint de poupança de proventos
#     gerar_checkpoint_proventos_acao(instance.investidor, ano)
#      
#     """
#     Verificar se existem anos posteriores
#     """
#     if ano != datetime.date.today().year:
#         for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#             gerar_checkpoint_acao(instance.investidor, instance.acao, prox_ano)
#              
#             # Se existe incorporação
#             if incorporacao and incorporacao.data.year <= prox_ano:
#                 gerar_checkpoint_acao(instance.investidor, incorporacao.novo_acao, prox_ano)
#                  
#             # Alterar checkpoint de poupança de proventos
#             gerar_checkpoint_proventos_acao(instance.investidor, prox_ano)
#  
#  
# @receiver(post_save, sender=UsoProventosOperacaoAcao, dispatch_uid="usoproventosoperacaoacao_criada_alterada")
# def preparar_checkpointacao_usoproventos(sender, instance, created, **kwargs):
#     post_save.send(OperacaoAcao, instance=instance.operacao, created=created)    
#     post_save.send(DivisaoOperacaoAcao, instance=instance.divisao_operacao, created=created)    
#      
# @receiver(post_delete, sender=OperacaoAcao, dispatch_uid="operacaoacao_apagada")
# def preparar_checkpointacao_delete(sender, instance, **kwargs):
#     """
#     Verifica ano da operação apagada
#     """
#     ano = instance.data.year
#     """ 
#     Altera checkpoint existente
#     """
#     gerar_checkpoint_acao(instance.investidor, instance.acao, ano)
#     # Verificar se Acao é incorporado
#     incorporacao = None if not EventoIncorporacaoAcao.objects.filter(acao=instance.acao).exists() else EventoIncorporacaoAcao.objects.get(acao=instance.acao)
#     # Se existe incorporação
#     if incorporacao and incorporacao.data.year == ano:
#         gerar_checkpoint_acao(instance.investidor, incorporacao.novo_acao, ano)
#          
#     # Alterar checkpoint de poupança de proventos
#     gerar_checkpoint_proventos_acao(instance.investidor, ano)
#  
#     """
#     Verificar se existem anos posteriores
#     """
#     if ano != datetime.date.today().year:
#         for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#             gerar_checkpoint_acao(instance.investidor, instance.acao, prox_ano)
#              
#             # Se existe incorporação
#             if incorporacao and incorporacao.data.year <= prox_ano:
#                 gerar_checkpoint_acao(instance.investidor, incorporacao.novo_acao, prox_ano)
#                  
#             # Alterar checkpoint de poupança de proventos
#             gerar_checkpoint_proventos_acao(instance.investidor, prox_ano)
#  
# # Preparar checkpoints para alterações em eventos de Acao
# @receiver(post_save, sender=EventoAgrupamentoAcao, dispatch_uid="evento_agrupamento_criado_alterado")
# @receiver(post_save, sender=EventoDesdobramentoAcao, dispatch_uid="evento_desdobramento_criado_alterado")
# @receiver(post_save, sender=EventoIncorporacaoAcao, dispatch_uid="evento_incorporacao_criado_alterado")
# def preparar_checkpointacao_evento(sender, instance, created, **kwargs):
#     """
#     Verifica ano da operação alterada
#     """
#     ano = instance.data.year
#     """ 
#     Cria novo checkpoint ou altera existente
#     """
#     # Verificar se Acao é incorporado
#     incorporacao = None if not EventoIncorporacaoAcao.objects.filter(acao=instance.acao).exists() else EventoIncorporacaoAcao.objects.get(acao=instance.acao)
#     for investidor in Investidor.objects.filter(id__in=OperacaoAcao.objects.filter(acao=instance.acao, data__lt=instance.data) \
#                                                 .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
#         gerar_checkpoint_acao(investidor, instance.acao, ano)
#         # Se existe incorporação
#         if incorporacao and incorporacao.data.year == ano:
#             gerar_checkpoint_acao(investidor, incorporacao.novo_acao, ano)
#              
#         # Alterar checkpoint de poupança de proventos
#         gerar_checkpoint_proventos_acao(investidor, ano)
#  
#         """
#         Verificar se existem anos posteriores
#         """
#         if ano != datetime.date.today().year:
#             for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#                 gerar_checkpoint_acao(investidor, instance.acao, prox_ano)
#                  
#                 # Se existe incorporação
#                 if incorporacao and incorporacao.data.year <= prox_ano:
#                     gerar_checkpoint_acao(investidor, incorporacao.novo_acao, prox_ano)
#                  
#                 # Alterar checkpoint de poupança de proventos
#                 gerar_checkpoint_proventos_acao(investidor, prox_ano)
#              
#      
# @receiver(post_delete, sender=EventoAgrupamentoAcao, dispatch_uid="evento_agrupamento_apagado")
# @receiver(post_delete, sender=EventoDesdobramentoAcao, dispatch_uid="evento_desdobramento_apagado")
# @receiver(post_delete, sender=EventoIncorporacaoAcao, dispatch_uid="evento_incorporacao_apagado")
# def preparar_checkpointacao_evento_delete(sender, instance, **kwargs):
#     """
#     Verifica ano do evento apagado
#     """
#     ano = instance.data.year
#     """ 
#     Altera checkpoints existentes
#     """
#     incorporacao = None if not EventoIncorporacaoAcao.objects.filter(acao=instance.acao).exists() else EventoIncorporacaoAcao.objects.get(acao=instance.acao)
#     for investidor in Investidor.objects.filter(id__in=OperacaoAcao.objects.filter(acao=instance.acao, data__lt=instance.data) \
#                                                 .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
#         gerar_checkpoint_acao(investidor, instance.acao, ano)
#         # Se existe incorporação
#         if incorporacao and incorporacao.data.year == ano:
#             gerar_checkpoint_acao(investidor, instance.novo_acao, ano)
#          
#         # Alterar checkpoint de poupança de proventos
#         gerar_checkpoint_proventos_acao(investidor, ano)
#  
#         """
#         Verificar se existem anos posteriores
#         """
#         if ano != datetime.date.today().year:
#             for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#                 gerar_checkpoint_acao(investidor, instance.acao, prox_ano)
#                  
#                 # Se existe incorporação
#                 if incorporacao and incorporacao.data.year <= prox_ano:
#                     gerar_checkpoint_acao(investidor, incorporacao.novo_acao, prox_ano)
#                  
#                 # Alterar checkpoint de poupança de proventos
#                 gerar_checkpoint_proventos_acao(investidor, prox_ano)
#              
#              
# def gerar_checkpoint_acao(investidor, acao, ano):
#     quantidade = calcular_qtd_acaos_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), acao.ticker)
#     preco_medio = calcular_preco_medio_acaos_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), acao.ticker)
#     if CheckpointAcao.objects.filter(investidor=investidor, acao=acao, ano=ano-1).exclude(quantidade=0).exists() or quantidade != 0:
#         CheckpointAcao.objects.update_or_create(investidor=investidor, acao=acao, ano=ano, 
#                                            defaults={'quantidade': quantidade, 'preco_medio': preco_medio})
#     else:
#         # Não existe checkpoint anterior e quantidade atual é 0
#         CheckpointAcao.objects.filter(investidor=investidor, acao=acao, ano=ano).delete()
#      
# def gerar_checkpoint_proventos_acao(investidor, ano):
#     valor = calcular_poupanca_prov_acao_ate_dia(investidor, datetime.date(ano, 12, 31))
#     if CheckpointProventosAcao.objects.filter(investidor=investidor, ano=ano-1).exclude(valor=0).exists() or valor != 0:
#         CheckpointProventosAcao.objects.update_or_create(investidor=investidor, ano=ano, 
#                                                    defaults={'valor': valor})
#     else:
#         # Não existe checkpoint anterior e valor atual é 0
#         CheckpointProventosAcao.objects.filter(investidor=investidor, ano=ano).delete()
