# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoFII, \
    CheckpointDivisaoProventosFII, CheckpointDivisaoFII
from bagogold.bagogold.models.fii import ProventoFII, OperacaoFII, \
    EventoAgrupamentoFII, EventoDesdobramentoFII, EventoIncorporacaoFII
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.utils.fii import calcular_poupanca_prov_fii_ate_dia, \
    calcular_qtd_fiis_ate_dia_por_ticker, \
    calcular_preco_medio_fiis_ate_dia_por_ticker, \
    calcular_qtd_fiis_ate_dia_por_ticker_por_divisao, \
    calcular_poupanca_prov_fii_ate_dia_por_divisao
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
import datetime

# Preparar checkpoints para alterações em proventos de FII
@receiver(post_save, sender=ProventoFII, dispatch_uid="proventofii_divisao_criado_alterado")
def preparar_checkpointproventofii(sender, instance, created, **kwargs):
    if instance.oficial_bovespa:
        """
        Verifica ano da data de pagamento
        """
        ano = instance.data_pagamento.year
        """ 
        Cria novo checkpoint ou altera existente
        """
        for divisao in Divisao.objects.filter(id__in=DivisaoOperacaoFII.objects.filter(operacao__fii=instance.fii, operacao__data__lt=instance.data_ex) \
                                                    .order_by('divisao').distinct('divisao').values_list('divisao', flat=True)):
            CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(ano, 12, 31), divisao)})
            # Se amortização verificar checkpoint de quantidade
            if instance.tipo_provento == 'A':
                CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), divisao.id, instance.fii.ticker), 
                                                     'preco_medio': 0})
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=prox_ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(prox_ano, 12, 31), divisao)})
                    # Se amortização verificar checkpoint de quantidade
                    if instance.tipo_provento == 'A':
                        CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.fii, ano=prox_ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(prox_ano, 12, 31), divisao.id, instance.fii.ticker), 
                                                     'preco_medio': 0})

@receiver(post_delete, sender=ProventoFII, dispatch_uid="proventofii_divisao_apagado")
def preparar_checkpointproventofii_delete(sender, instance, **kwargs):
    if instance.oficial_bovespa:
        """
        Verifica ano da data de pagamento do provento apagado
        """
        ano = instance.data.year
        """ 
        Altera checkpoints existentes
        """
        for divisao in Divisao.objects.filter(id__in=DivisaoOperacaoFII.objects.filter(operacao__fii=instance.fii, operacao__data__lt=instance.data) \
                                              .order_by('divisao').distinct('divisao').values_list('divisao', flat=True)):
            CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(ano, 12, 31), divisao)})
            # Se amortização verificar checkpoint de quantidade
            if instance.tipo_provento == 'A':
                CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.fii, ano=ano, 
                                                       defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), divisao.id, instance.fii.ticker), 
                                                                 'preco_medio': 0})
            
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=prox_ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(prox_ano, 12, 31), divisao)})
                    # Se amortização verificar checkpoint de quantidade
                    if instance.tipo_provento == 'A':
                        CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.fii, ano=prox_ano, 
                                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(prox_ano, 12, 31), divisao.id, instance.fii.ticker), 
                                                                         'preco_medio': 0})  
                        
    
            """
            Apagar checkpoints iniciais zerados
            """
            for checkpoint in CheckpointDivisaoProventosFII.objects.filter(divisao=divisao).order_by('ano'):
                if checkpoint.valor == 0:
                    checkpoint.delete()
                else:
                    break 
                
# Preparar checkpoints para alterações em operações de FII
@receiver(post_save, sender=DivisaoOperacaoFII, dispatch_uid="operacaofii_divisao_criada_alterada")
def preparar_checkpointfii(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.operacao.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    CheckpointDivisaoFII.objects.update_or_create(divisao=instance.divisao, fii=instance.operacao.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), instance.divisao.id, instance.operacao.fii.ticker), 
                                                     'preco_medio': 0})
    # Alterar checkpoint de poupança de proventos
    CheckpointDivisaoProventosFII.objects.update_or_create(divisao=instance.divisao, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(ano, 12, 31), instance.divisao)})

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            CheckpointDivisaoFII.objects.update_or_create(divisao=instance.divisao, fii=instance.operacao.fii, ano=prox_ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(prox_ano, 12, 31), instance.divisao.id, instance.operacao.fii.ticker), 
                                                     'preco_medio': 0})
            # Alterar checkpoint de poupança de proventos
            CheckpointDivisaoProventosFII.objects.update_or_create(divisao=instance.divisao, ano=prox_ano, 
                                                       defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(prox_ano, 12, 31), instance.divisao)})
    
@receiver(post_delete, sender=DivisaoOperacaoFII, dispatch_uid="operacaofii_divisao_apagada")
def preparar_checkpointfii_delete(sender, instance, **kwargs):
    """
    Verifica ano da operação apagada
    """
    ano = instance.operacao.data.year
    """ 
    Altera checkpoint existente
    """
    CheckpointDivisaoFII.objects.update_or_create(divisao=instance.divisao, fii=instance.operacao.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), instance.divisao.id, instance.operacao.fii.ticker), 
                                                     'preco_medio': 0})
    # Alterar checkpoint de poupança de proventos
    CheckpointDivisaoProventosFII.objects.update_or_create(divisao=instance.divisao, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(ano, 12, 31), instance.divisao)})

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            CheckpointDivisaoFII.objects.update_or_create(divisao=instance.divisao, fii=instance.operacao.fii, ano=prox_ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(prox_ano, 12, 31), instance.divisao.id, instance.operacao.fii.ticker), 
                                                     'preco_medio': 0})   
            # Alterar checkpoint de poupança de proventos
            CheckpointDivisaoProventosFII.objects.update_or_create(divisao=instance.divisao, ano=prox_ano, 
                                                       defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(prox_ano, 12, 31), instance.divisao)})

    """
    Apagar checkpoints iniciais zerados
    """
    for checkpoint in CheckpointDivisaoFII.objects.filter(divisao=instance.divisao, fii=instance.operacao.fii).order_by('ano'):
        if checkpoint.quantidade == 0:
            checkpoint.delete()
        else:
            break 
    # Apagar checkpoints de proventos zerados
    for checkpoint in CheckpointDivisaoProventosFII.objects.filter(divisao=instance.divisao).order_by('ano'):
        if checkpoint.valor == 0:
            checkpoint.delete()
        else:
            break 
        
# Preparar checkpoints para alterações em eventos de FII
@receiver(post_save, sender=EventoAgrupamentoFII, dispatch_uid="evento_agrupamento_divisao_criado_alterado")
@receiver(post_save, sender=EventoDesdobramentoFII, dispatch_uid="evento_desdobramento_divisao_criado_alterado")
@receiver(post_save, sender=EventoIncorporacaoFII, dispatch_uid="evento_incorporacao_divisao_criado_alterado")
def preparar_checkpointfii_evento(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    for divisao in Divisao.objects.filter(id__in=DivisaoOperacaoFII.objects.filter(operacao__fii=instance.fii, operacao__data__lt=instance.data) \
                                                    .order_by('divisao').distinct('divisao').values_list('divisao', flat=True)):
        CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), divisao.id, instance.fii.ticker), 
                                                     'preco_medio': 0})
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.novo_fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), divisao.id, instance.novo_fii.ticker), 
                                                     'preco_medio': 0})
            
        # Alterar checkpoint de poupança de proventos
        CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(ano, 12, 31), divisao)})

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(prox_ano, 12, 31), divisao.id, instance.fii.ticker), 
                                                         'preco_medio': 0})
                
                # Alterar checkpoint de poupança de proventos
                CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=prox_ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(prox_ano, 12, 31), divisao)})
            
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.novo_fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(prox_ano, 12, 31), divisao.id, instance.novo_fii.ticker), 
                                                         'preco_medio': 0})
            

    
@receiver(post_delete, sender=EventoAgrupamentoFII, dispatch_uid="evento_agrupamento_divisao_apagado")
@receiver(post_delete, sender=EventoDesdobramentoFII, dispatch_uid="evento_desdobramento_divisao_apagado")
@receiver(post_delete, sender=EventoIncorporacaoFII, dispatch_uid="evento_incorporacao_divisao_apagado")
def preparar_checkpointfii_evento_delete(sender, instance, **kwargs):
    """
    Verifica ano do evento apagado
    """
    ano = instance.data.year
    """ 
    Altera checkpoints existentes
    """
    for divisao in Divisao.objects.filter(id__in=DivisaoOperacaoFII.objects.filter(operacao__fii=instance.fii, operacao__data__lt=instance.data) \
                                                    .order_by('divisao').distinct('divisao').values_list('divisao', flat=True)):
        CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), divisao.id, instance.fii.ticker), 
                                                     'preco_medio': 0})
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.novo_fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), divisao.id, instance.novo_fii.ticker), 
                                                     'preco_medio': 0})
        
        # Alterar checkpoint de poupança de proventos
        CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(prox_ano, 12, 31), divisao)})

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(prox_ano, 12, 31), divisao.id, instance.fii.ticker), 
                                                         'preco_medio': 0})  
                
                # Alterar checkpoint de poupança de proventos
                CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=prox_ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia_por_divisao(datetime.date(prox_ano, 12, 31), divisao)})
                
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=instance.novo_fii, ano=prox_ano, 
                                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(prox_ano, 12, 31), divisao.id, instance.novo_fii.ticker), 
                                                                     'preco_medio': 0})  
                    

        """
        Apagar checkpoints iniciais zerados
        """
        for checkpoint in CheckpointDivisaoFII.objects.filter(divisao=divisao, fii=instance.fii).order_by('ano'):
            if checkpoint.quantidade == 0:
                checkpoint.delete()
            else:
                break 
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            for checkpoint in CheckpointDivisaoFII.objects.filter(divisao=divisao, fii=instance.novo_fii).order_by('ano'):
                if checkpoint.quantidade == 0:
                    checkpoint.delete()
                else:
                    break 
        
        # Apagar checkpoints de proventos zerados
        for checkpoint in CheckpointDivisaoProventosFII.objects.filter(divisao=divisao).order_by('ano'):
            if checkpoint.valor == 0:
                checkpoint.delete()
            else:
                break 