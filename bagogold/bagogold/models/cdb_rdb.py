# -*- coding: utf-8 -*-
from django import forms
from django.db import models
import datetime

class CDB_RDB (models.Model):
    nome = models.CharField(u'Nome', max_length=50)
    investidor = models.ForeignKey('Investidor')
    """
    Tipo de investimento, C = CDB, R = RDB
    """
    tipo = models.CharField(u'Tipo', max_length=1)
    """
    Tipo de rendimento, 1 = Pré-fixado, 2 = Pós-fixado
    """    
    tipo_rendimento = models.PositiveSmallIntegerField(u'Tipo de rendimento')
    
    
    def __unicode__(self):
        return self.nome
    
    def carencia_atual(self):
        try:
            return HistoricoCarenciaCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self).order_by('-data')[0].carencia
        except:
            return HistoricoCarenciaCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self).carencia
    
    def porcentagem_atual(self):
        try:
            return HistoricoPorcentagemCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self).order_by('-data')[0].porcentagem
        except:
            return HistoricoPorcentagemCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self).porcentagem
    
    def valor_minimo_atual(self):
        try:
            return HistoricoValorMinimoInvestimentoCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self).order_by('-data')[0].valor_minimo
        except:
            return HistoricoValorMinimoInvestimentoCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self).valor_minimo
    
class OperacaoCDB_RDB (models.Model):
    quantidade = models.DecimalField(u'Quantidade investida/resgatada', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    investimento = models.ForeignKey('CDB_RDB')
    investidor = models.ForeignKey('Investidor')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.investimento, self.data)
    
    def carencia(self):
        try:
            return HistoricoCarenciaCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).order_by('-data')[0].carencia
        except:
            return HistoricoCarenciaCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self.investimento).carencia
    
    def operacao_compra_relacionada(self):
        if self.tipo_operacao == 'V':
            return OperacaoVendaCDB_RDB.objects.get(operacao_venda=self).operacao_compra
        else:
            return None
    
    def porcentagem(self):
        if self.tipo_operacao == 'C':
            try:
                return HistoricoPorcentagemCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).order_by('-data')[0].porcentagem
            except:
                return HistoricoPorcentagemCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self.investimento).porcentagem
        elif self.tipo_operacao == 'V':
            return self.operacao_compra_relacionada().porcentagem()
    
    def qtd_disponivel_venda(self):
        vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=self).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoCDB_RDB.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def qtd_disponivel_venda_na_data(self, data):
        vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=self).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoVendaCDB_RDB.objects.filter(id__in=vendas, data__lt=data):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def venda_permitida(self, data_venda=None):
        if data_venda == None:
            data_venda = datetime.date.today()
        if self.tipo_operacao == 'C':
            historico = HistoricoCarenciaCDB_RDB.objects.exclude(data=None).filter(data__lte=data_venda).order_by('-data')
            if historico:
                # Verifica o período de carência pegando a data mais recente antes da operação de compra
                return (historico[0].carencia <= (data_venda - self.data).days)
            else:
                carencia = HistoricoCarenciaCDB_RDB.objects.get(cdb_rdb=self.investimento).carencia
                return (carencia <= (data_venda - self.data).days)
        else:
            return False
    
class OperacaoVendaCDB_RDB (models.Model):
    operacao_compra = models.ForeignKey('OperacaoCDB_RDB', limit_choices_to={'tipo_operacao': 'C'}, related_name='operacao_compra')
    operacao_venda = models.ForeignKey('OperacaoCDB_RDB', limit_choices_to={'tipo_operacao': 'V'}, related_name='operacao_venda')
    
    class Meta:
        unique_together=('operacao_compra', 'operacao_venda')
    
class HistoricoPorcentagemCDB_RDB (models.Model):
    porcentagem = models.DecimalField(u'Porcentagem de rendimento', max_digits=5, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    cdb_rdb = models.ForeignKey('CDB_RDB')
    
class HistoricoCarenciaCDB_RDB (models.Model):
    """
    O período de carência é medido em dias
    """
    carencia = models.IntegerField(u'Período de carência')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    cdb_rdb = models.ForeignKey('CDB_RDB')
    
    def save(self, *args, **kw):
        try:
            historico = HistoricoCarenciaCDB_RDB.objects.get(cdb_rdb=self.cdb_rdb, data=self.data)
        except HistoricoCarenciaCDB_RDB.DoesNotExist:
            if self.carencia <= 0:
                raise forms.ValidationError('Carência deve ser de pelo menos 1 dia')
            super(HistoricoCarenciaCDB_RDB, self).save(*args, **kw)
            
class HistoricoValorMinimoInvestimentoCDB_RDB (models.Model):
    valor_minimo = models.DecimalField(u'Valor mínimo para investimento', max_digits=9, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    cdb_rdb = models.ForeignKey('CDB_RDB')
    
    def save(self, *args, **kw):
        try:
            historico = HistoricoValorMinimoInvestimentoCDB_RDB.objects.get(cdb_rdb=self.cdb_rdb, data=self.data)
        except HistoricoValorMinimoInvestimentoCDB_RDB.DoesNotExist:
            if self.valor_minimo < 0:
                raise forms.ValidationError('Valor mínimo não pode ser negativo')
            super(HistoricoValorMinimoInvestimentoCDB_RDB, self).save(*args, **kw)
    
