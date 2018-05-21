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
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=21, decimal_places=12, validators=[MinValueValidator(Decimal('0.000000000001'))])
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    criptomoeda = models.ForeignKey('Criptomoeda')
    investidor = models.ForeignKey('bagogold.Investidor', related_name='criptomoeda')
    
    def __unicode__(self):
        return '(%s) %s de %s em %s' % (self.tipo_operacao, self.quantidade, self.criptomoeda, self.data.strftime('%d/%m/%Y'))
    
    def em_real(self):
        return not hasattr(self, 'operacaocriptomoedamoeda')
    
    def moeda_utilizada(self):
        if hasattr(self, 'operacaocriptomoedamoeda'):
            return self.operacaocriptomoedamoeda.criptomoeda.ticker
        return 'BRL'
    
    def taxa(self):
        if hasattr(self, 'operacaocriptomoedataxa'):
            return self.operacaocriptomoedataxa 
        else:
            return None
    
class OperacaoCriptomoedaTaxa (models.Model):
    valor = models.DecimalField(u'Taxa da operação', max_digits=21, decimal_places=12, validators=[MinValueValidator(Decimal('0'))])
    operacao = models.OneToOneField('OperacaoCriptomoeda')
    moeda = models.ForeignKey('Criptomoeda', blank=True, null=True)
    
    def __unicode__(self):
        valor = 'R$ %s' % self.valor if self.moeda == None else '%s %s' % (self.valor, self.moeda.ticker)
        return 'Taxa de %s' % (valor)
    
    def em_real(self):
        return self.moeda is None
    
    def moeda_utilizada(self):
        if self.moeda is not None:
            return self.moeda.ticker
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
    valor = models.DecimalField(u'Valor', max_digits=21, decimal_places=12)

    class Meta:
        unique_together=('criptomoeda', 'data')
        
class ValorDiarioCriptomoeda (models.Model):
    
    MOEDA_REAL = u'BRL'
    MOEDA_DOLAR = u'USD'
    
    criptomoeda = models.ForeignKey('Criptomoeda')
    data_hora = models.DateTimeField(u'Horário')
    valor = models.DecimalField(u'Valor', max_digits=21, decimal_places=12)
    moeda = models.CharField(u'Moeda utilizada', max_length=10)
        
class TransferenciaCriptomoeda (models.Model):
    moeda = models.ForeignKey('Criptomoeda', blank=True, null=True)
    data = models.DateField(u'Data')
    quantidade = models.DecimalField(u'Quantidade transferida', max_digits=21, decimal_places=12, validators=[MinValueValidator(Decimal('0.000000000001'))])
    investidor = models.ForeignKey('bagogold.Investidor')
    origem = models.CharField(u'Local de origem', max_length=50)
    destino = models.CharField(u'Local de destino', max_length=50)
    taxa = models.DecimalField(u'Taxa da transferência', max_digits=21, decimal_places=12, validators=[MinValueValidator(Decimal('0.000000000001'))])

    def __unicode__(self):
        return u'Transferência de %s %s entre %s e %s' % (self.quantidade, self.moeda_utilizada(), self.origem, self.destino)
    
    def em_real(self):
        return self.moeda is None
    
    def moeda_utilizada(self):
        if self.moeda is not None:
            return self.moeda.ticker
        return 'BRL'
        
class Fork (models.Model):
    moeda_origem = models.ForeignKey('Criptomoeda', related_name='moeda_origem_fork')
    moeda_recebida = models.ForeignKey('Criptomoeda', related_name='moeda_recebida_fork')
    data = models.DateField(u'Data')
    quantidade = models.DecimalField(u'Quantidade recebida', max_digits=21, decimal_places=12, validators=[MinValueValidator(Decimal('0.000000000001'))])
    investidor = models.ForeignKey('bagogold.Investidor')
     
    def __unicode__(self):
        return u'Fork de %s em %s %s no dia %s' % (self.moeda_origem, self.quantidade, self.moeda_recebida, self.data.strftime('%d/%m/%Y'))
    
class TelegramInvestidor (models.Model):
    chat_id = models.IntegerField(u'ID do Telegram')
    
class Bot (models.Model):
    ultima_msg_lida = models.IntegerField(u'ID da última mensagem lida')