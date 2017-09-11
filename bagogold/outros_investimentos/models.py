# -*- coding: utf-8 -*-
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models

class Investimento (models.Model):
    nome = models.CharField(u'Nome', max_length=30)
    descricao = models.CharField(u'Descrição', max_length=100, blank=True, null=True)
    investidor = models.ForeignKey('bagogold.Investidor', related_name='outros_investimentos')
    encerrado = models.BooleanField(u'Encerrado?', default=False)
    
    class Meta:
        unique_together=('nome', 'investidor',)
    
    def __unicode__(self):
        return self.nome
    
class OperacaoInvestimento (models.Model):
    quantidade = models.DecimalField(u'Quantidade', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    investimento = models.ForeignKey('Investimento')
    
class OperacaoInvestimentoTaxa (models.Model):
    operacao = models.OneToOneField('OperacaoInvestimento')
    valor = models.DecimalField(u'Valor da taxa', max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
class Rendimento (models.Model):
    investimento = models.ForeignKey('Investimento')
    valor = models.DecimalField(u'Valor do rendimento', max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data = models.DateField(u'Data do rendimento')
    
class PeriodoRendimentos (models.Model):
    investimento = models.ForeignKey('Investimento')
    tipo_periodo = models.CharField(u'Tipo de período')
    qtd_periodo = models.IntegerField(u'Quantidade do período')
    valor_rendimento = models.DecimalField(u'Valor do rendimento', max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    inicio_vigencia = models.DateField(u'Data da operação')
    fim_vigencia = models.DateField(u'Data da operação')
