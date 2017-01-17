# -*- coding: utf-8 -*-
from decimal import Decimal
from django.db import models

class Debenture (models.Model):
    codigo = models.CharField(u'Código', max_length=10)
    """
    1 = Prefixado, 2 = IPCA, 3 = DI, 4 = IGP-M, 5 = SELIC
    """
    indice = models.PositiveSmallIntegerField(u'Índice')
    porcentagem = models.DecimalField(u'Porcentagem sobre índice', decimal_places=3, max_digits=6, default=Decimal('100'))
    data_emissao = models.DateField(u'Data de emissão')
    valor_emissao = models.DecimalField(u'Valor nominal na emissão', max_digits=17, decimal_places=8)
    data_inicio_rendimento = models.DateField(u'Data de início do rendimento')
    data_vencimento = models.DateField(u'Data de vencimento', null=True, blank=True)
    data_fim = models.DateField(u'Data de fim', null=True, blank=True)
    incentivada = models.BooleanField(u'É incentivada?')
    padrao_snd = models.BooleanField(u'É padrão SND?')
    
    class Meta:
        unique_together=('codigo', )
    
    def __unicode__(self):
        return self.nome
    
class AmortizacaoDebenture (models.Model):
    TIPOS_AMORTIZACAO = ((0, u'Indefinido'),
                         (1, u'Percentual fixo sobre o valor nominal atualizado em períodos não uniformes'),
                         (2, u'Percentual fixo sobre o valor nominal atualizado em períodos uniformes'),
                         (3, u'Percentual fixo sobre o valor nominal de emissão em períodos não uniformes'),
                         (4, u'Percentual fixo sobre o valor nominal de emissão em períodos uniformes'),
                         (5, u'Percentual variável sobre o valor nominal atualizado em períodos não uniformes'),
                         (6, u'Percentual variável sobre o valor nominal atualizado em períodos uniformes'),
                         (7, u'Percentual variável sobre o valor nominal de emissão em períodos não uniformes'),
                         (8, u'Percentual variável sobre o valor nominal de emissão em períodos uniformes'),)
    
    debenture = models.OneToOneField('Debenture', on_delete=models.CASCADE, primary_key=True)
    taxa = models.DecimalField(u'Taxa', max_digits=7, decimal_places=4)
    periodo = models.IntegerField(u'Período')
    unidade_periodo = models.CharField(u'Unidade do período', max_length=10)
    carencia = models.DateField(u'Carência')
    tipo = models.PositiveSmallIntegerField(u'Tipo de amortização')
    data = models.DateField(u'Data')
    
class JurosDebenture (models.Model):
    debenture = models.OneToOneField('Debenture', on_delete=models.CASCADE, primary_key=True)
    taxa = models.DecimalField(u'Taxa', max_digits=7, decimal_places=4)
    periodo = models.IntegerField(u'Período')
    unidade_periodo = models.CharField(u'Unidade do período', max_length=10)
    carencia = models.DateField(u'Carência')
    data = models.DateField(u'Data')
    
class PremioDebenture (models.Model):
    debenture = models.OneToOneField('Debenture', on_delete=models.CASCADE, primary_key=True)
    taxa = models.DecimalField(u'Taxa', max_digits=7, decimal_places=4)
    periodo = models.IntegerField(u'Período')
    unidade_periodo = models.CharField(u'Unidade do período', max_length=10)
    carencia = models.DateField(u'Carência')
    data = models.DateField(u'Data')
    
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