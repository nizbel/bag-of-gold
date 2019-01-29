# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls.base import reverse


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
    
    @property
    def link(self):
        return reverse('outros_investimentos:editar_investimento', kwargs={'operacao_id': self.id})
    
class InvestimentoTaxa (models.Model):
    investimento = models.OneToOneField('Investimento')
    valor = models.DecimalField(u'Valor da taxa', max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
class Rendimento (models.Model):
    investimento = models.ForeignKey('Investimento')
    valor = models.DecimalField(u'Valor do rendimento', max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    data = models.DateField(u'Data do rendimento')
    
    def possui_imposto(self):
        return hasattr(self, 'impostorendarendimento')
    
    def valor_liquido(self):
        if hasattr(self, 'impostorendarendimento'):
            return self.valor * (1 - self.impostorendarendimento.percentual_calculo())
        return self.valor
    
    def valor_imposto(self):
        if hasattr(self, 'impostorendarendimento'):
            return self.valor * self.impostorendarendimento.percentual_calculo()
        return 0
        
    
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
    
class ImpostoRendaRendimento (models.Model):
    TIPO_SEM_IMPOSTO = 'S'
    TIPO_LONGO_PRAZO = 'L'
    TIPO_PERC_ESPECIFICO = 'P'
    
    TIPO_SEM_IMPOSTO_DESCRICAO = u'Sem imposto'
    TIPO_LONGO_PRAZO_DESCRICAO = u'Longo prazo'
    TIPO_PERC_ESPECIFICO_DESCRICAO = u'Percentual específico'
    
    TIPOS_IMPOSTO_RENDA = ((TIPO_LONGO_PRAZO, TIPO_LONGO_PRAZO_DESCRICAO),
                           (TIPO_PERC_ESPECIFICO, TIPO_PERC_ESPECIFICO_DESCRICAO))
    
    rendimento = models.OneToOneField('Rendimento')
    tipo = models.CharField(u'Tipo de cálculo', max_length=1, choices=TIPOS_IMPOSTO_RENDA)
    
    def percentual(self):
        if self.tipo == self.TIPO_LONGO_PRAZO:
            qtd_dias = (self.rendimento.data - self.rendimento.investimento.data).days
            if qtd_dias <= 180:
                return Decimal(22.5)
            elif qtd_dias <= 360:
                return Decimal(20)
            elif qtd_dias <= 720:
                return Decimal(17.5)
            else: 
                return Decimal(15)
        elif self.tipo == self.TIPO_PERC_ESPECIFICO:
            return self.impostorendavalorespecifico.percentual
    
    def percentual_calculo(self):
        if self.tipo == self.TIPO_LONGO_PRAZO:
            qtd_dias = (self.rendimento.data - self.rendimento.investimento.data).days
            if qtd_dias <= 180:
                return Decimal(0.225)
            elif qtd_dias <= 360:
                return Decimal(0.2)
            elif qtd_dias <= 720:
                return Decimal(0.175)
            else: 
                return Decimal(0.15)
        elif self.tipo == self.TIPO_PERC_ESPECIFICO:
            return self.impostorendavalorespecifico.percentual / 100
    
class ImpostoRendaValorEspecifico (models.Model):
    imposto = models.OneToOneField('ImpostoRendaRendimento')
    percentual = models.DecimalField(u'Percentual de IR', max_digits=5, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])