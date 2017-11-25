# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import ProventoFII, OperacaoFII, \
    CheckpointProventosFII, CheckpointFII, EventoAgrupamentoFII, \
    EventoDesdobramentoFII, EventoIncorporacaoFII
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.utils.fii import calcular_poupanca_prov_fii_ate_dia, \
    calcular_qtd_fiis_ate_dia_por_ticker, \
    calcular_preco_medio_fiis_ate_dia_por_ticker
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
import datetime

# Preparar checkpoints para alterações em proventos de FII
@receiver(post_save, sender=ProventoFII, dispatch_uid="proventofii_criado_alterado")
def preparar_checkpointproventofii(sender, instance, created, **kwargs):
    if instance.oficial_bovespa:
        """
        Verifica ano da data de pagamento
        """
        ano = instance.data_pagamento.year
        """ 
        Cria novo checkpoint ou altera existente
        """
        for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data_ex) \
                                                    .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
            gerar_checkpoint_proventos_fii(investidor, ano)
            # Se amortização verificar checkpoint de quantidade
            if instance.tipo_provento == 'A':
                gerar_checkpoint_fii(investidor, instance.fii, ano)
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    gerar_checkpoint_proventos_fii(investidor, prox_ano)
                    # Se amortização verificar checkpoint de quantidade
                    if instance.tipo_provento == 'A':
                        gerar_checkpoint_fii(investidor, instance.fii, prox_ano)

@receiver(post_delete, sender=ProventoFII, dispatch_uid="proventofii_apagado")
def preparar_checkpointproventofii_delete(sender, instance, **kwargs):
    if instance.oficial_bovespa:
        """
        Verifica ano da data de pagamento do provento apagado
        """
        ano = instance.data.year
        """ 
        Altera checkpoints existentes
        """
        for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data) \
                                                    .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
            gerar_checkpoint_proventos_fii(investidor, ano)
            # Se amortização verificar checkpoint de quantidade
            if instance.tipo_provento == 'A':
                gerar_checkpoint_fii(investidor, instance.fii, ano)
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    gerar_checkpoint_proventos_fii(investidor, prox_ano)
                    # Se amortização verificar checkpoint de quantidade
                    if instance.tipo_provento == 'A':
                        gerar_checkpoint_fii(investidor, instance.fii, prox_ano)
    
            """
            Apagar checkpoints iniciais zerados
            """
            apagar_checkpoint_proventos_fii(investidor)
                
# Preparar checkpoints para alterações em operações de FII
@receiver(post_save, sender=OperacaoFII, dispatch_uid="operacaofii_criada_alterada")
def preparar_checkpointfii(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    gerar_checkpoint_fii(instance.investidor, instance.fii, ano)
    # Alterar checkpoint de poupança de proventos
    gerar_checkpoint_proventos_fii(instance.investidor, ano)

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_fii(instance.investidor, instance.fii, prox_ano)
            # Alterar checkpoint de poupança de proventos
            gerar_checkpoint_proventos_fii(instance.investidor, prox_ano)
    
@receiver(post_delete, sender=OperacaoFII, dispatch_uid="operacaofii_apagada")
def preparar_checkpointfii_delete(sender, instance, **kwargs):
    """
    Verifica ano da operação apagada
    """
    ano = instance.data.year
    """ 
    Altera checkpoint existente
    """
    gerar_checkpoint_fii(instance.investidor, instance.fii, ano)
    # Alterar checkpoint de poupança de proventos
    gerar_checkpoint_proventos_fii(instance.investidor, ano)

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            gerar_checkpoint_fii(instance.investidor, instance.fii, prox_ano)
            # Alterar checkpoint de poupança de proventos
            gerar_checkpoint_proventos_fii(instance.investidor, prox_ano)

    """
    Apagar checkpoints iniciais zerados
    """
    apagar_checkpoint_fii(instance.investidor, instance.fii)
    # Apagar checkpoints de proventos zerados
    apagar_checkpoint_proventos_fii(instance.investidor)
        
# Preparar checkpoints para alterações em eventos de FII
@receiver(post_save, sender=EventoAgrupamentoFII, dispatch_uid="evento_agrupamento_criado_alterado")
@receiver(post_save, sender=EventoDesdobramentoFII, dispatch_uid="evento_desdobramento_criado_alterado")
@receiver(post_save, sender=EventoIncorporacaoFII, dispatch_uid="evento_incorporacao_criado_alterado")
def preparar_checkpointfii_evento(sender, instance, created, **kwargs):
    """
    Verifica ano da operação alterada
    """
    ano = instance.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data) \
                                                .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
        gerar_checkpoint_fii(investidor, instance.fii, ano)
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            gerar_checkpoint_fii(investidor, instance.novo_fii, ano)
            
        # Alterar checkpoint de poupança de proventos
        gerar_checkpoint_proventos_fii(investidor, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_fii(investidor, instance.fii, prox_ano)
                
                # Alterar checkpoint de poupança de proventos
                gerar_checkpoint_proventos_fii(investidor, prox_ano)
            
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    gerar_checkpoint_fii(investidor, instance.novo_fii, prox_ano)

    
@receiver(post_delete, sender=EventoAgrupamentoFII, dispatch_uid="evento_agrupamento_apagado")
@receiver(post_delete, sender=EventoDesdobramentoFII, dispatch_uid="evento_desdobramento_apagado")
@receiver(post_delete, sender=EventoIncorporacaoFII, dispatch_uid="evento_incorporacao_apagado")
def preparar_checkpointfii_evento_delete(sender, instance, **kwargs):
    """
    Verifica ano do evento apagado
    """
    ano = instance.data.year
    """ 
    Altera checkpoints existentes
    """
    for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data) \
                                                .order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
        gerar_checkpoint_fii(investidor, instance.fii, ano)
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            gerar_checkpoint_fii(investidor, instance.novo_fii, ano)
        
        # Alterar checkpoint de poupança de proventos
        gerar_checkpoint_proventos_fii(investidor, ano)

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                gerar_checkpoint_fii(investidor, instance.fii, prox_ano)
                
                # Alterar checkpoint de poupança de proventos
                gerar_checkpoint_proventos_fii(investidor, prox_ano)
            
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    gerar_checkpoint_fii(investidor, instance.novo_fii, prox_ano)

        """
        Apagar checkpoints iniciais zerados
        """
        apagar_checkpoint_fii(investidor, instance.fii)
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            apagar_checkpoint_fii(investidor, instance.novo_fii)
        
        # Apagar checkpoints de proventos zerados
        apagar_checkpoint_proventos_fii(investidor)
            
def gerar_checkpoint_fii(investidor, fii, ano):
    quantidade = calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), fii.ticker)
    preco_medio = calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), fii.ticker)
    if CheckpointFII.objects.filter(investidor=investidor, fii=fii, ano__lte=ano).exists() or (quantidade > 0 or preco_medio != 0):
        CheckpointFII.objects.update_or_create(investidor=investidor, fii=fii, ano=ano, 
                                           defaults={'quantidade': quantidade, 'preco_medio': preco_medio})
    
def gerar_checkpoint_proventos_fii(investidor, ano):
    valor = calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(ano, 12, 31))
    if CheckpointProventosFII.objects.filter(investidor=investidor, ano__lte=ano).exists() or valor > 0:
        CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=ano, 
                                                   defaults={'valor': valor})
    
def apagar_checkpoint_fii(investidor, fii):
    for checkpoint in CheckpointFII.objects.filter(investidor=investidor, fii=fii).order_by('ano'):
        if checkpoint.quantidade == 0 and checkpoint.preco_medio == 0:
            checkpoint.delete()
        else:
            return
    
def apagar_checkpoint_proventos_fii(investidor):
    for checkpoint in CheckpointProventosFII.objects.filter(investidor=investidor).order_by('ano'):
        if checkpoint.valor == 0:
            checkpoint.delete()
        else:
            return 