# -*- coding: utf-8 -*-
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
import datetime

class Investimento (models.Model):
    nome = models.CharField(u'Nome', max_length=30)
    descricao = models.CharField(u'Descrição', max_length=100, blank=True, null=True)
    investidor = models.ForeignKey('bagogold.Investidor', related_name='outros_investimentos')
    data_encerramento = models.DateField(u'Data de encerramento', blank=True, null=True)
    quantidade = models.DecimalField(u'Quantidade', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data = models.DateField(u'Data do investimento')
    
    class Meta:
        unique_together=('nome', 'investidor',)
    
    def __unicode__(self):
        return self.nome
    
    def total_amortizado(self):
        return sum(Amortizacao.objects.filter(investimento=self).values_list('valor', flat=True))
    
    def eh_encerrado(self):
        return self.data_encerramento and self.data_encerramento < datetime.date.today()
    
    @property
    def taxa(self):
        if hasattr(self, 'investimentotaxa'):
            return self.investimentotaxa.valor
        return Decimal(0)
    
class InvestimentoTaxa (models.Model):
    investimento = models.OneToOneField('Investimento')
    valor = models.DecimalField(u'Valor da taxa', max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
class Rendimento (models.Model):
    investimento = models.ForeignKey('Investimento')
    valor = models.DecimalField(u'Valor do rendimento', max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data = models.DateField(u'Data do rendimento')
    
class PeriodoRendimentos (models.Model):
    investimento = models.ForeignKey('Investimento')
    tipo_periodo = models.CharField(u'Tipo de período', max_length=1)
    qtd_periodo = models.IntegerField(u'Quantidade do período')
    valor_rendimento = models.DecimalField(u'Valor do rendimento', max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    inicio_vigencia = models.DateField(u'Início da vigência')
    fim_vigencia = models.DateField(u'Fim da vigência')

class Amortizacao (models.Model):
    investimento = models.ForeignKey('Investimento')
    valor = models.DecimalField(u'Valor da amortização', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data = models.DateField(u'Data da amortização')
    