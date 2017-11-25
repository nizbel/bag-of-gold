# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoFII, \
    CheckpointDivisaoProventosFII, CheckpointDivisaoFII
from bagogold.bagogold.models.fii import ProventoFII, \
    EventoAgrupamentoFII, EventoDesdobramentoFII, EventoIncorporacaoFII
from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_ticker_por_divisao, \
    calcular_poupanca_prov_fii_ate_dia_por_divisao,\
    calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao
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
            gerar_checkpoint_divisao_proventos_fii(divisao, ano)
            # Se amortização verificar checkpoint de quantidade
            if instance.tipo_provento == 'A':
                gerar_checkpoint_divisao_fii(divisao, instance.fii, ano)
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    gerar_checkpoint_divisao_proventos_fii(divisao, prox_ano)
                    # Se amortização verificar checkpoint de quantidade
                    if instance.tipo_provento == 'A':
                        gerar_checkpoint_divisao_fii(divisao, instance.fii, prox_ano)

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
            gerar_checkpoint_divisao_proventos_fii(divisao, ano)
            # Se amortização verificar checkpoint de quantidade
            if instance.tipo_provento == 'A':
                gerar_checkpoint_divisao_fii(divisao, instance.fii, ano)
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    gerar_checkpoint_divisao_proventos_fii(divisao, prox_ano)
                    # Se amortização verificar checkpoint de quantidade
                    if instance.tipo_provento == 'A':
                        gerar_checkpoint_divisao_fii(divisao, instance.fii, prox_ano)
    
            """
            Apagar checkpoints iniciais zerados
            """
            apagar_checkpoint_divisao_proventos_fii(divisao)
                
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
    gerar_checkpoint_divisao_fii(instance.divisao, instance.operacao.fii, ano)
    # Alterar checkpoint de poupança de proventos
    gerar_checkpoint_divisao_proventos_fii(instance.divisao, ano)

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_divisao_fii(instance.divisao, instance.operacao.fii, prox_ano)
            # Alterar checkpoint de poupança de proventos
            gerar_checkpoint_divisao_proventos_fii(instance.divisao, prox_ano)
    
@receiver(post_delete, sender=DivisaoOperacaoFII, dispatch_uid="operacaofii_divisao_apagada")
def preparar_checkpointfii_delete(sender, instance, **kwargs):
    """
    Verifica ano da operação apagada
    """
    ano = instance.operacao.data.year
    """ 
    Altera checkpoint existente
    """
    gerar_checkpoint_divisao_fii(instance.divisao, instance.operacao.fii, ano)
    # Alterar checkpoint de poupança de proventos
    gerar_checkpoint_divisao_proventos_fii(instance.divisao, ano)

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_divisao_fii(instance.divisao, instance.operacao.fii, prox_ano)
            # Alterar checkpoint de poupança de proventos
            gerar_checkpoint_divisao_proventos_fii(instance.divisao, prox_ano)

    """
    Apagar checkpoints iniciais zerados
    """
    apagar_checkpoint_divisao_fii(instance.divisao, instance.operacao.fii)
    # Apagar checkpoints de proventos zerados
    apagar_checkpoint_divisao_proventos_fii(instance.divisao)
        
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
        gerar_checkpoint_divisao_fii(divisao, instance.fii, ano)
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            gerar_checkpoint_divisao_fii(divisao, instance.novo_fii, ano)
            
        # Alterar checkpoint de poupança de proventos
        gerar_checkpoint_divisao_proventos_fii(divisao, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_divisao_fii(divisao, instance.fii, prox_ano)
                
                # Alterar checkpoint de poupança de proventos
                gerar_checkpoint_divisao_proventos_fii(divisao, prox_ano)
            
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    gerar_checkpoint_divisao_fii(divisao, instance.novo_fii, prox_ano)
            
    
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
        gerar_checkpoint_divisao_fii(divisao, instance.fii, ano)
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            gerar_checkpoint_divisao_fii(divisao, instance.novo_fii, ano)
        
        # Alterar checkpoint de poupança de proventos
        gerar_checkpoint_divisao_proventos_fii(divisao, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_divisao_fii(divisao, instance.fii, prox_ano)
                
                # Alterar checkpoint de poupança de proventos
                gerar_checkpoint_divisao_proventos_fii(divisao, prox_ano)
                
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    gerar_checkpoint_divisao_fii(divisao, instance.novo_fii, prox_ano)
                    
        """
        Apagar checkpoints iniciais zerados
        """
        apagar_checkpoint_divisao_fii(divisao, instance.fii)
        
        # Se incorporação
        apagar_checkpoint_divisao_fii(divisao, instance.novo_fii)
        
        # Apagar checkpoints de proventos zerados
        apagar_checkpoint_divisao_proventos_fii(divisao)
            
def gerar_checkpoint_divisao_fii(divisao, fii, ano):
    quantidade = calcular_qtd_fiis_ate_dia_por_ticker_por_divisao(datetime.date(ano, 12, 31), divisao.id, fii.ticker)
    preco_medio = calcular_preco_medio_fiis_ate_dia_por_ticker_por_divisao(divisao, datetime.date(ano, 12, 31), fii.ticker)
    if CheckpointDivisaoFII.objects.filter(divisao=divisao, fii=fii, ano__lte=ano).exists() or (quantidade > 0 or preco_medio != 0):
        CheckpointDivisaoFII.objects.update_or_create(divisao=divisao, fii=fii, ano=ano, 
                                               defaults={'quantidade': quantidade, 'preco_medio': preco_medio})
    
def gerar_checkpoint_divisao_proventos_fii(divisao, ano):
    valor = calcular_poupanca_prov_fii_ate_dia_por_divisao(divisao, datetime.date(ano, 12, 31))
    if CheckpointDivisaoProventosFII.objects.filter(divisao=divisao, ano__lte=ano).exists() or valor > 0:
        CheckpointDivisaoProventosFII.objects.update_or_create(divisao=divisao, ano=ano, 
                                                   defaults={'valor': valor})
    
def apagar_checkpoint_divisao_fii(divisao, fii):
    for checkpoint in CheckpointDivisaoFII.objects.filter(divisao=divisao, fii=fii).order_by('ano'):
        if checkpoint.quantidade == 0 and checkpoint.preco_medio == 0:
            checkpoint.delete()
        else:
            return
    
def apagar_checkpoint_divisao_proventos_fii(divisao):
    for checkpoint in CheckpointDivisaoProventosFII.objects.filter(divisao=divisao).order_by('ano'):
        if checkpoint.valor == 0:
            checkpoint.delete()
        else:
            return