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

# Preparar checkpoints para alterações em operações de FII
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
        for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data_ex).order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
            CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(ano, 12, 31))})
            # Se amortização verificar checkpoint de quantidade
            if instance.tipo_provento == 'A':
                CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=prox_ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(prox_ano, 12, 31))})
                    # Se amortização verificar checkpoint de quantidade
                    if instance.tipo_provento == 'A':
                        CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=prox_ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker)})

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
        for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data).order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
            CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(ano, 12, 31))})
            # Se amortização verificar checkpoint de quantidade
            if instance.tipo_provento == 'A':
                CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=ano, 
                                                       defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 
                                                                 'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})
            
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=prox_ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(prox_ano, 12, 31))})
                    # Se amortização verificar checkpoint de quantidade
                    if instance.tipo_provento == 'A':
                        CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=prox_ano, 
                                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 
                                                                         'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})  
                        
    
            """
            Apagar checkpoints iniciais zerados
            """
            for checkpoint in CheckpointProventosFII.objects.filter(investidor=instance.investidor).order_by('ano'):
                if checkpoint.valor == 0:
                    checkpoint.delete()
                else:
                    break 
                
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
    CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})
    # Alterar checkpoint de poupança de proventos
    CheckpointProventosFII.objects.update_or_create(investidor=instance.investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(instance.investidor, datetime.date(ano, 12, 31))})

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=prox_ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})
            # Alterar checkpoint de poupança de proventos
            CheckpointProventosFII.objects.update_or_create(investidor=instance.investidor, ano=prox_ano, 
                                                       defaults={'valor': calcular_poupanca_prov_fii_ate_dia(instance.investidor, datetime.date(prox_ano, 12, 31))})
    
@receiver(post_delete, sender=OperacaoFII, dispatch_uid="operacaofii_apagada")
def preparar_checkpointfii_delete(sender, instance, **kwargs):
    """
    Verifica ano da operação apagada
    """
    ano = instance.data.year
    """ 
    Altera checkpoint existente
    """
    CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})
    # Alterar checkpoint de poupança de proventos
    CheckpointProventosFII.objects.update_or_create(investidor=instance.investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(instance.investidor, datetime.date(ano, 12, 31))})

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=prox_ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})   
            # Alterar checkpoint de poupança de proventos
            CheckpointProventosFII.objects.update_or_create(investidor=instance.investidor, ano=prox_ano, 
                                                       defaults={'valor': calcular_poupanca_prov_fii_ate_dia(instance.investidor, datetime.date(prox_ano, 12, 31))})

    """
    Apagar checkpoints iniciais zerados
    """
    for checkpoint in CheckpointFII.objects.filter(investidor=instance.investidor, fii=instance.fii).order_by('ano'):
        if checkpoint.quantidade == 0:
            checkpoint.delete()
        else:
            break 
    # Apagar checkpoints de proventos zerados
    for checkpoint in CheckpointProventosFII.objects.filter(investidor=instance.investidor).order_by('ano'):
        if checkpoint.valor == 0:
            checkpoint.delete()
        else:
            break 
        
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
    for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data).order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
        CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.novo_fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.novo_fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.novo_fii.ticker)})
            
        # Alterar checkpoint de poupança de proventos
        CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(ano, 12, 31))})

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 
                                                         'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.novo_fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.novo_fii.ticker), 
                                                         'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.novo_fii.ticker)})
            
            # Alterar checkpoint de poupança de proventos
            CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=prox_ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(prox_ano, 12, 31))})

    
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
    for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data).order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
        CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.novo_fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.novo_fii.ticker), 
                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.novo_fii.ticker)})
        
        # Alterar checkpoint de poupança de proventos
        CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(ano, 12, 31))})

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 
                                                         'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker)})  
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.novo_fii, ano=prox_ano, 
                                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.novo_fii.ticker), 
                                                                     'preco_medio': calcular_preco_medio_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.novo_fii.ticker)})  
                    
            # Alterar checkpoint de poupança de proventos
            CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=prox_ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(prox_ano, 12, 31))})

        """
        Apagar checkpoints iniciais zerados
        """
        for checkpoint in CheckpointFII.objects.filter(investidor=investidor, fii=instance.fii).order_by('ano'):
            if checkpoint.quantidade == 0:
                checkpoint.delete()
            else:
                break 
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            for checkpoint in CheckpointFII.objects.filter(investidor=investidor, fii=instance.novo_fii).order_by('ano'):
                if checkpoint.quantidade == 0:
                    checkpoint.delete()
                else:
                    break 
        
        # Apagar checkpoints de proventos zerados
        for checkpoint in CheckpointProventosFII.objects.filter(investidor=instance.investidor).order_by('ano'):
            if checkpoint.valor == 0:
                checkpoint.delete()
            else:
                break 