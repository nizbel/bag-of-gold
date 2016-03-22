# -*- coding: utf-8 -*-
from django.db import models

class LetraCredito (models.Model):
    nome = models.CharField(u'Nome', max_length=50)    
    
    def __unicode__(self):
        return self.nome
    
class OperacaoLetraCredito (models.Model):
    quantidade = models.DecimalField(u'Quantidade investida', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    letra_credito = models.ForeignKey('LetraCredito')
    
class HistoricoPorcentagemLetraCredito (models.Model):
    porcentagem_di = models.DecimalField(u'Porcentagem do DI', max_digits=5, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True)
    letra_credito = models.ForeignKey('LetraCredito')
    
    def save(self, *args, **kw):
        try:
            historico = HistoricoPorcentagemLetraCredito.objects.get(letra_credito=self.letra_credito, data=self.data)
        except HistoricoPorcentagemLetraCredito.DoesNotExist:
            super(HistoricoPorcentagemLetraCredito, self).save(*args, **kw)
    
class HistoricoCarenciaLetraCredito (models.Model):
    """
    O período de carência é medido em dias
    """
    carencia = models.IntegerField(u'Período de carência')
    data = models.DateField(u'Data da variação', blank=True)
    letra_credito = models.ForeignKey('LetraCredito')
    
class HistoricoTaxaDI (models.Model):
    data = models.DateField(u'Data')
    taxa = models.DecimalField(u'Rendimento anual', max_digits=5, decimal_places=2, unique_for_date='data')
    
    def save(self, *args, **kw):
        try:
            historico = HistoricoTaxaDI.objects.get(taxa=self.taxa, data=self.data)
        except HistoricoTaxaDI.DoesNotExist:
            super(HistoricoTaxaDI, self).save(*args, **kw)