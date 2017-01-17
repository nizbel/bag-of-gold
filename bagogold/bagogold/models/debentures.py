# -*- coding: utf-8 -*-
from django.db import models

class Debenture (models.Model):
    codigo = models.CharField(u'Código', max_length=10)
    """
    1 = Prefixado, 2 = IPCA, 3 = DI
    """
    tipo_indexacao = models.PositiveSmallIntegerField(u'Tipo de indexação')
    porcentagem = models.DecimalField(u'Porcentagem sobre indexação', decimal_places=3, max_digits=6)
    juros_adicional = models.DecimalField(u'Juros adicional', decimal_places=3, max_digits=6)
    data_emissao = models.DateField(u'Data de emissão')
    valor_emissao = models.DecimalField(u'Valor nominal na emissão', max_digits=15, decimal_places=8)
    data_inicio_rendimento = models.DateField(u'Data de início do rendimento')
    data_vencimento = models.DateField(u'Data de vencimento', null=True, blank=True)
    data_fim = models.DateField(u'Data de fim', null=True, blank=True)
    incentivada = models.BooleanField(u'É incentivada?')
    
    class Meta:
        unique_together=('codigo', )
    
    def __unicode__(self):
        return self.nome
    
class OperacaoDebenture (models.Model):
    debenture = models.ForeignKey('Debenture')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=15, decimal_places=8)  
    quantidade = models.IntegerField(u'Quantidade') 
    data = models.DateField(u'Data', blank=True, null=True)
    taxa = models.DecimalField(u'Taxa', max_digits=11, decimal_places=2)
    
class HistoricoValorDebenture (models.Model):
    debenture = models.ForeignKey('Debenture')
    valor_nominal = models.DecimalField(u'Valor nominal', max_digits=15, decimal_places=6)
    juros = models.DecimalField(u'Juros', max_digits=15, decimal_places=6)
    premio = models.DecimalField(u'Prêmio', max_digits=15, decimal_places=6)
    data = models.DateField(u'Data')