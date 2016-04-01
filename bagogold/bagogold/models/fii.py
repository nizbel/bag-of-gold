# -*- coding: utf-8 -*-
from django.db import models
 
class FII (models.Model):
    ticker = models.CharField(u'Ticker da ação', max_length=10) 
    
    def __unicode__(self):
        return self.ticker
    
class ProventoFII (models.Model):
    fii = models.ForeignKey('FII')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=13, decimal_places=9)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento')
    
class OperacaoFII (models.Model):
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)  
    quantidade = models.IntegerField(u'Quantidade') 
    data = models.DateField(u'Data', blank=True, null=True)
    corretagem = models.DecimalField(u'Corretagem', max_digits=11, decimal_places=2)
    emolumentos = models.DecimalField(u'Emolumentos', max_digits=11, decimal_places=2)
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    fii = models.ForeignKey('FII')
    consolidada = models.NullBooleanField(u'Consolidada?', blank=True)
     
    def __unicode__(self):
        return '(' + self.tipo_operacao + ') ' + str(self.quantidade) + ' ' + self.fii.ticker + ' a R$' + str(self.preco_unitario)
    
class UsoProventosOperacaoFII (models.Model):
    operacao = models.ForeignKey('OperacaoFII')
    qtd_utilizada = models.DecimalField(u'Quantidade de proventos utilizada', max_digits=11, decimal_places=2, blank=True)

    
class HistoricoFII (models.Model):
    fii = models.ForeignKey('FII', unique_for_date='data')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data de referência')
        
class ValorDiarioFII (models.Model):
    fii = models.ForeignKey('FII')
    data_hora = models.DateTimeField(u'Horário')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    