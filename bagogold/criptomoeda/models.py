# -*- coding: utf-8 -*-
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models

class Criptomoeda (models.Model):
    nome = models.CharField(u'Nome', max_length=50)
    ticker = models.CharField(u'Ticker', max_length=10)
    
    class Meta:
        unique_together=('ticker',)
    
    def __unicode__(self):
        return self.nome
    
class OperacaoCriptomoeda (models.Model):
    quantidade = models.DecimalField(u'Quantidade', max_digits=21, decimal_places=12, validators=[MinValueValidator(Decimal('0.000000000001'))])
    valor = models.DecimalField(u'Valor unitário', max_digits=21, decimal_places=12, validators=[MinValueValidator(Decimal('0.000000000001'))])
    taxa = models.DecimalField(u'Taxa da operação', max_digits=21, decimal_places=12)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    criptomoeda = models.ForeignKey('Criptomoeda')
    investidor = models.ForeignKey('bagogold.Investidor', related_name='criptomoeda')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.valor, self.criptomoeda, self.data.strftime('%d/%m/%Y'))
    
    def em_real(self):
        return not hasattr(self, 'operacaocriptomoedamoeda')
    
    def moeda(self):
        if hasattr(self, 'operacaocriptomoedamoeda'):
            return self.operacaocriptomoedamoeda.criptomoeda
        return 'BRL'
    
class OperacaoCriptomoedaMoeda (models.Model):
    """
    Guarda a moeda utilizada para adquirir ou vender uma criptomoeda, caso a operação não possua uma moeda vinculada,
    o padrão é o Real
    """
    operacao = models.OneToOneField('OperacaoCriptomoeda')
    criptomoeda = models.ForeignKey('Criptomoeda')
    
class HistoricoValorCriptomoeda (models.Model):
    criptomoeda = models.ForeignKey('Criptomoeda')
    data = models.DateField(u'Data')
    valor = models.DecimalField(u'Valor', max_digits=24, decimal_places=15)

    class Meta:
        unique_together=('criptomoeda', 'data')