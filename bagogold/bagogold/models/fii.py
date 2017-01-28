# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFII
from django.db import models
import datetime
 
class FII (models.Model):
    ticker = models.CharField(u'Ticker do FII', max_length=10, unique=True) 
    
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
    
class ProventoFII (models.Model):
    fii = models.ForeignKey('FII')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=13, decimal_places=9)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento')
    url_documento = models.CharField(u'URL do documento', blank=True, null=True, max_length=200)
    
    class Meta:
        unique_together=(('data_ex', 'data_pagamento', 'fii',))
        
    def __unicode__(self):
        return 'R$ %s de %s em %s com data EX %s' % (str(self.valor_unitario), self.fii.ticker, str(self.data_pagamento), str(self.data_ex))
        
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
        return '(' + self.tipo_operacao + ') ' + str(self.quantidade) + ' ' + self.fii.ticker + ' a R$' + str(self.preco_unitario)
    
    def qtd_proventos_utilizada(self):
        qtd_total = 0
        for divisao in DivisaoOperacaoFII.objects.filter(operacao=self):
            if hasattr(divisao, 'usoproventosoperacaofii'):
                qtd_total += divisao.usoproventosoperacaofii.qtd_utilizada
        return qtd_total
        
    def utilizou_proventos(self):
        return self.qtd_proventos_utilizada() > 0
    
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
        
class ValorDiarioFII (models.Model):
    fii = models.ForeignKey('FII')
    data_hora = models.DateTimeField(u'Horário')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    