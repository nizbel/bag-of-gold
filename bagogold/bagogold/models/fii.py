# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa
from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
from math import floor
import datetime
 
class FII (models.Model):
    ticker = models.CharField(u'Ticker do FII', max_length=10, unique=True) 
    empresa = models.ForeignKey('Empresa', blank=True, null=True) 
    encerrado = models.BooleanField(u'FII encerrado?', default=False)
    
    class Meta:
        ordering = ['ticker']
        
    def __unicode__(self):
        return self.ticker
    
    def valor_no_dia(self, dia):
        if dia == datetime.date.today():
            try:
                return ValorDiarioFII.objects.filter(fii__ticker=self.ticker, data_hora__day=dia.day, data_hora__month=dia.month).order_by('-data_hora')[0].preco_unitario
            except:
                pass
        return HistoricoFII.objects.filter(fii__ticker=self.ticker, data__lte=dia).order_by('-data')[0].preco_unitario

class ProventoFIIOficialManager(models.Manager):
    def get_queryset(self):
        return super(ProventoFIIOficialManager, self).get_queryset().filter(oficial_bovespa=True)

class ProventoFII (models.Model):
    TIPO_PROVENTO_AMORTIZACAO = 'A'
    TIPO_PROVENTO_RENDIMENTO = 'R'
    ESCOLHAS_TIPO_PROVENTO_FII=((TIPO_PROVENTO_RENDIMENTO, "Rendimento"),
                        (TIPO_PROVENTO_AMORTIZACAO, "Amortização"),)
    
    fii = models.ForeignKey('FII')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=20, decimal_places=16)
    """
    A = amortização, R = rendimentos
    """
    tipo_provento = models.CharField(u'Tipo de provento', max_length=1)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento')
    oficial_bovespa = models.BooleanField(u'Oficial Bovespa?', default=False)
    
    class Meta:
        unique_together=('data_ex', 'data_pagamento', 'fii', 'valor_unitario', 'oficial_bovespa')
        
    def __unicode__(self):
        return 'R$ %s de %s em %s com data EX %s' % (str(self.valor_unitario), self.fii.ticker, str(self.data_pagamento), str(self.data_ex))
    
    def descricao_tipo_provento(self):
        if self.tipo_provento == self.TIPO_PROVENTO_AMORTIZACAO:
            return u'Amortização'
        elif self.tipo_provento == self.TIPO_PROVENTO_RENDIMENTO:
            return u'Rendimento'
    
    @property    
    def add_pelo_sistema(self):
        return all([(provento_documento.documento.tipo_documento == DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO) \
                                     for provento_documento in self.proventofiidocumento_set.all()])
        
    objects = ProventoFIIOficialManager()
    gerador_objects = models.Manager()

# Preparar checkpoints para alterações em operações de FII
@receiver(post_save, sender=ProventoFII, dispatch_uid="proventofii_criado_alterado")
def preparar_checkpointproventofii(sender, instance, created, **kwargs):
    from bagogold.bagogold.models.investidores import Investidor
    from bagogold.bagogold.utils.fii import calcular_poupanca_prov_fii_ate_dia
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
    
            """
            Verificar se existem anos posteriores
            """
            if ano != datetime.date.today().year:
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointProventosFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=prox_ano, 
                                                   defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(prox_ano, 12, 31))})

# @receiver(post_delete, sender=ProventoFII, dispatch_uid="proventofii_apagado")
# def preparar_checkpointproventofii_delete(sender, instance, **kwargs):
#     from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_ticker
#     """
#     Verifica ano da data de pagamento do provento apagado
#     """
#     ano = instance.data.year
#     """ 
#     Altera checkpoint existente
#     """
#     CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=ano, 
#                                            defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})
#     """
#     Verificar se existem anos posteriores
#     """
#     if ano != datetime.date.today().year:
#         for prox_ano in range(ano + 1, datetime.date.today().year + 1):
#             CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=prox_ano, 
#                                            defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})   
#     """
#     Apagar checkpoints iniciais zerados
#     """
#     for checkpoint in CheckpointFII.objects.filter(investidor=instance.investidor, fii=instance.fii).order_by('ano'):
#         if checkpoint.quantidade == 0:
#             checkpoint.delete()
#         else:
#             break 
    
class OperacaoFII (models.Model):
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)  
    quantidade = models.IntegerField(u'Quantidade') 
    data = models.DateField(u'Data', blank=True, null=True)
    corretagem = models.DecimalField(u'Corretagem', max_digits=11, decimal_places=2)
    emolumentos = models.DecimalField(u'Emolumentos', max_digits=11, decimal_places=2)
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    fii = models.ForeignKey('FII')
    consolidada = models.NullBooleanField(u'Consolidada?', blank=True)
    investidor = models.ForeignKey('Investidor')
     
    def __unicode__(self):
        return '(' + self.tipo_operacao + ') ' + str(self.quantidade) + ' ' + self.fii.ticker + ' a R$' + str(self.preco_unitario) + ' em ' + str(self.data.strftime('%d/%m/%Y'))
    
    def qtd_proventos_utilizada(self):
        qtd_total = UsoProventosOperacaoFII.objects.filter(operacao=self).aggregate(qtd_total=Sum('qtd_utilizada'))['qtd_total'] or 0
        return qtd_total
        
    def utilizou_proventos(self):
        return UsoProventosOperacaoFII.objects.filter(operacao=self).exists()

# Preparar checkpoints para alterações em operações de FII
@receiver(post_save, sender=OperacaoFII, dispatch_uid="operacaofii_criada_alterada")
def preparar_checkpointfii(sender, instance, created, **kwargs):
    from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_ticker, \
        calcular_poupanca_prov_fii_ate_dia
    """
    Verifica ano da operação alterada
    """
    ano = instance.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})
    # Alterar checkpoint de poupança de proventos
    CheckpointProventosFII.objects.update_or_create(investidor=instance.investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(instance.investidor, datetime.date(ano, 12, 31))})

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=prox_ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})
            # Alterar checkpoint de poupança de proventos
            CheckpointProventosFII.objects.update_or_create(investidor=instance.investidor, ano=prox_ano, 
                                                       defaults={'valor': calcular_poupanca_prov_fii_ate_dia(instance.investidor, datetime.date(prox_ano, 12, 31))})
    
@receiver(post_delete, sender=OperacaoFII, dispatch_uid="operacaofii_apagada")
def preparar_checkpointfii_delete(sender, instance, **kwargs):
    from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_ticker, \
        calcular_poupanca_prov_fii_ate_dia
    """
    Verifica ano da operação apagada
    """
    ano = instance.data.year
    """ 
    Altera checkpoint existente
    """
    CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})
    # Alterar checkpoint de poupança de proventos
    CheckpointProventosFII.objects.update_or_create(investidor=instance.investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(instance.investidor, datetime.date(ano, 12, 31))})

    """
    Verificar se existem anos posteriores
    """
    if ano != datetime.date.today().year:
        for prox_ano in range(ano + 1, datetime.date.today().year + 1):
            CheckpointFII.objects.update_or_create(investidor=instance.investidor, fii=instance.fii, ano=prox_ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(instance.investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})   
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
    
class UsoProventosOperacaoFII (models.Model):
    operacao = models.ForeignKey('OperacaoFII')
    qtd_utilizada = models.DecimalField(u'Quantidade de proventos utilizada', max_digits=11, decimal_places=2, blank=True)
    divisao_operacao = models.OneToOneField('DivisaoOperacaoFII')

    def __unicode__(self):
        return 'R$ ' + str(self.qtd_utilizada) + ' em ' + self.divisao_operacao.divisao.nome + ' para ' + unicode(self.divisao_operacao.operacao)
    
class HistoricoFII (models.Model):
    fii = models.ForeignKey('FII', unique_for_date='data')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data de referência')
    oficial_bovespa = models.BooleanField(u'Oficial Bovespa?', default=False)
    
    class Meta:
        unique_together = ('fii', 'data')
        
class ValorDiarioFII (models.Model):
    fii = models.ForeignKey('FII')
    data_hora = models.DateTimeField(u'Horário')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    
# Eventos
class EventoFII (models.Model):
    fii = models.ForeignKey('FII')
    data = models.DateField(u'Data')
    
    class Meta():
        abstract = True
        
class EventoIncorporacaoFII (EventoFII):
    novo_fii = models.ForeignKey('FII', related_name='incorporacao')
    
    class Meta:
        unique_together=('fii', 'data')
    
class EventoAgrupamentoFII (EventoFII):
    proporcao = models.DecimalField(u'Proporção de agrupamento', max_digits=13, decimal_places=12, validators=[MaxValueValidator(Decimal('0.999999999999'))])
    valor_fracao = models.DecimalField(u'Valor para as frações', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        unique_together=('fii', 'data')
        
    def qtd_apos(self, qtd_inicial):
        return Decimal(floor(qtd_inicial * self.proporcao))
    
class EventoDesdobramentoFII (EventoFII):
    proporcao = models.DecimalField(u'Proporção de desdobramento', max_digits=16, decimal_places=12, validators=[MinValueValidator(Decimal('1.000000000001'))])
    valor_fracao = models.DecimalField(u'Valor para as frações', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        unique_together=('fii', 'data')
        
    def qtd_apos(self, qtd_inicial):
        return Decimal(floor(qtd_inicial * self.proporcao))
    
# Preparar checkpoints para alterações em eventos de FII
@receiver(post_save, sender=EventoAgrupamentoFII, dispatch_uid="evento_agrupamento_criado_alterado")
@receiver(post_save, sender=EventoDesdobramentoFII, dispatch_uid="evento_desdobramento_criado_alterado")
@receiver(post_save, sender=EventoIncorporacaoFII, dispatch_uid="evento_incorporacao_criado_alterado")
def preparar_checkpointfii_evento(sender, instance, created, **kwargs):
    from bagogold.bagogold.models.investidores import Investidor
    from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_ticker, \
        calcular_poupanca_prov_fii_ate_dia
    """
    Verifica ano da operação alterada
    """
    ano = instance.data.year
    """ 
    Cria novo checkpoint ou altera existente
    """
    for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data).order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
        CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.novo_fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.novo_fii.ticker), 'preco_medio': 0})
            
        # Alterar checkpoint de poupança de proventos
        CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(ano, 12, 31))})

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.novo_fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.novo_fii.ticker), 'preco_medio': 0})
            
            # Alterar checkpoint de poupança de proventos
            CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=prox_ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(prox_ano, 12, 31))})

    
@receiver(post_delete, sender=EventoAgrupamentoFII, dispatch_uid="evento_agrupamento_apagado")
@receiver(post_delete, sender=EventoDesdobramentoFII, dispatch_uid="evento_desdobramento_apagado")
@receiver(post_delete, sender=EventoIncorporacaoFII, dispatch_uid="evento_incorporacao_apagado")
def preparar_checkpointfii_evento_delete(sender, instance, **kwargs):
    from bagogold.bagogold.models.investidores import Investidor
    from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_ticker, \
        calcular_poupanca_prov_fii_ate_dia
    """
    Verifica ano do evento apagado
    """
    ano = instance.data.year
    """ 
    Altera checkpoints existentes
    """
    for investidor in Investidor.objects.filter(id__in=OperacaoFII.objects.filter(fii=instance.fii, data__lt=instance.data).order_by('investidor').distinct('investidor').values_list('investidor', flat=True)):
        CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})
        # Se incorporação
        if isinstance(instance, EventoIncorporacaoFII):
            CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.novo_fii, ano=ano, 
                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(ano, 12, 31), instance.novo_fii.ticker), 'preco_medio': 0})
        
        # Alterar checkpoint de poupança de proventos
        CheckpointProventosFII.objects.update_or_create(investidor=investidor, ano=ano, 
                                               defaults={'valor': calcular_poupanca_prov_fii_ate_dia(investidor, datetime.date(ano, 12, 31))})

        """
        Verificar se existem anos posteriores
        """
        if ano != datetime.date.today().year:
            for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.fii, ano=prox_ano, 
                                               defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.fii.ticker), 'preco_medio': 0})  
            # Se incorporação
            if isinstance(instance, EventoIncorporacaoFII):
                for prox_ano in range(ano + 1, datetime.date.today().year + 1):
                    CheckpointFII.objects.update_or_create(investidor=investidor, fii=instance.novo_fii, ano=prox_ano, 
                                                           defaults={'quantidade': calcular_qtd_fiis_ate_dia_por_ticker(investidor, datetime.date(prox_ano, 12, 31), instance.novo_fii.ticker), 
                                                                     'preco_medio': 0})  
                    
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

    
class CheckpointFII(models.Model):
    ano = models.SmallIntegerField(u'Ano')
    fii = models.ForeignKey('FII')
    investidor = models.ForeignKey('Investidor')
    quantidade = models.IntegerField(u'Quantidade no ano', validators=[MinValueValidator(0)])
    preco_medio = models.DecimalField(u'Preço médio', max_digits=11, decimal_places=4)
    
    class Meta:
        unique_together=('fii', 'ano', 'investidor')
        
class CheckpointProventosFII(models.Model):
    ano = models.SmallIntegerField(u'Ano')
    investidor = models.ForeignKey('Investidor')
    valor = models.DecimalField(u'Valor da poupança de proventos', max_digits=22, decimal_places=16)
        
    class Meta:
        unique_together=('ano', 'investidor')