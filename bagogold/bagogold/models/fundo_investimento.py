# -*- coding: utf-8 -*-
from django import forms
from django.db import models
import datetime

class FundoInvestimento (models.Model):
    nome = models.CharField(u'Nome', max_length=50)
    investidor = models.ForeignKey('Investidor')
    descricao = models.CharField(u'Descrição', max_length=200)
    """
    L = longo prazo, C = curto prazo; para fins de IR
    """
    tipo_prazo = models.CharField(u'Tipo de prazo', max_length=1)
    
    
    def __unicode__(self):
        return self.nome
    
    def carencia_atual(self):
        try:
            return HistoricoCarenciaFundoInvestimento.objects.filter(data__isnull=False, fundo_investimento=self).order_by('-data')[0].carencia
        except:
            return HistoricoCarenciaFundoInvestimento.objects.get(data__isnull=True, fundo_investimento=self).carencia
    
    def valor_minimo_atual(self):
        try:
            return HistoricoValorMinimoInvestimentoFundoInvestimento.objects.filter(data__isnull=False, cdb_rdb=self).order_by('-data')[0].valor_minimo
        except:
            return HistoricoValorMinimoInvestimentoFundoInvestimento.objects.get(data__isnull=True, cdb_rdb=self).valor_minimo
    
class OperacaoFundoInvestimento (models.Model):
    quantidade_cotas = models.DecimalField(u'Quantidade de cotas', max_digits=11, decimal_places=2)
    valor = models.DecimalField(u'Valor da operação', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    fundo_investimento = models.ForeignKey('FundoInvestimento')
    investidor = models.ForeignKey('Investidor')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.investimento, self.data)
    
    def carencia(self):
        try:
            return HistoricoCarenciaFundoInvestimento.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).order_by('-data')[0].carencia
        except:
            return HistoricoCarenciaFundoInvestimento.objects.get(data__isnull=True, cdb_rdb=self.investimento).carencia
    
    def venda_permitida(self, data_venda=None):
        if data_venda == None:
            data_venda = datetime.date.today()
        if self.tipo_operacao == 'C':
            historico = HistoricoCarenciaFundoInvestimento.objects.exclude(data=None).filter(data__lte=data_venda).order_by('-data')
            if historico:
                # Verifica o período de carência pegando a data mais recente antes da operação de compra
                return (historico[0].carencia <= (data_venda - self.data).days)
            else:
                carencia = HistoricoCarenciaFundoInvestimento.objects.get(cdb_rdb=self.investimento).carencia
                return (carencia <= (data_venda - self.data).days)
        else:
            return False

class HistoricoValorCotas (models.Model):
    fundo_investimento = models.ForeignKey('FundoInvestimento')
    data = models.DateField(u'Data')
    valor_cota = models.DecimalField(u'Valor da cota', max_digits=11, decimal_places=2)

    def save(self, *args, **kw):
        try:
            historico = HistoricoValorCotas.objects.get(fundo_investimento=self.fundo_investimento, data=self.data)
        except HistoricoValorCotas.DoesNotExist:
            if self.valor_cota <= 0:
                raise forms.ValidationError('Valor da cota deve ser superior a zero')
            super(HistoricoValorCotas, self).save(*args, **kw)

class HistoricoCarenciaFundoInvestimento (models.Model):
    """
    O período de carência é medido em dias
    """
    carencia = models.IntegerField(u'Período de carência')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    fundo_investimento = models.ForeignKey('FundoInvestimento')
    
    def save(self, *args, **kw):
        try:
            historico = HistoricoCarenciaFundoInvestimento.objects.get(fundo_investimento=self.fundo_investimento, data=self.data)
        except HistoricoCarenciaFundoInvestimento.DoesNotExist:
            if self.carencia <= 0:
                raise forms.ValidationError('Carência deve ser de pelo menos 1 dia')
            super(HistoricoCarenciaFundoInvestimento, self).save(*args, **kw)
            
class HistoricoValorMinimoInvestimentoFundoInvestimento (models.Model):
    valor_minimo = models.DecimalField(u'Valor mínimo para investimento', max_digits=9, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    fundo_investimento = models.ForeignKey('FundoInvestimento')
    
    def save(self, *args, **kw):
        try:
            historico = HistoricoValorMinimoInvestimentoFundoInvestimento.objects.get(fundo_investimento=self.fundo_investimento, data=self.data)
        except HistoricoValorMinimoInvestimentoFundoInvestimento.DoesNotExist:
            if self.valor_minimo < 0:
                raise forms.ValidationError('Valor mínimo não pode ser negativo')
            super(HistoricoValorMinimoInvestimentoFundoInvestimento, self).save(*args, **kw)
    
