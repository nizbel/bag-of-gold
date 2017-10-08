# -*- coding: utf-8 -*-
from django.db import models
import datetime

class LetraCredito (models.Model):
    nome = models.CharField(u'Nome', max_length=50)  
    investidor = models.ForeignKey('Investidor')
    
    def __unicode__(self):
        return self.nome
    
    def carencia_atual(self):
        try:
            return HistoricoCarenciaLetraCredito.objects.filter(data__isnull=False, letra_credito=self).order_by('-data')[0].carencia
        except:
            return HistoricoCarenciaLetraCredito.objects.get(data__isnull=True, letra_credito=self).carencia
        
    def carencia_na_data(self, data):
        try:
            return HistoricoCarenciaLetraCredito.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).order_by('-data')[0].carencia
        except:
            return HistoricoCarenciaLetraCredito.objects.get(data__isnull=True, letra_credito=self).carencia
    
    def porcentagem_di_atual(self):
        try:
            return HistoricoPorcentagemLetraCredito.objects.filter(data__isnull=False, letra_credito=self).order_by('-data')[0].porcentagem_di
        except:
            return HistoricoPorcentagemLetraCredito.objects.get(data__isnull=True, letra_credito=self).porcentagem_di
        
    def porcentagem_na_data(self, data):
        try:
            return HistoricoPorcentagemLetraCredito.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).order_by('-data')[0].porcentagem_di
        except:
            return HistoricoPorcentagemLetraCredito.objects.get(data__isnull=True, letra_credito=self).porcentagem_di
        
    def valor_minimo_atual(self):
        try:
            return HistoricoValorMinimoInvestimento.objects.filter(data__isnull=False, letra_credito=self).order_by('-data')[0].valor_minimo
        except:
            return HistoricoValorMinimoInvestimento.objects.get(data__isnull=True, letra_credito=self).valor_minimo
        
    def valor_minimo_na_data(self, data):
        try:
            return HistoricoValorMinimoInvestimento.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).order_by('-data')[0].valor_minimo
        except:
            return HistoricoValorMinimoInvestimento.objects.get(data__isnull=True, letra_credito=self).valor_minimo
    
class OperacaoLetraCredito (models.Model):
    quantidade = models.DecimalField(u'Quantidade investida/resgatada', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    letra_credito = models.ForeignKey('LetraCredito', verbose_name='Letra de Crédito')
    investidor = models.ForeignKey('Investidor')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.letra_credito, self.data.strftime('%d/%m/%Y'))
    
    def save(self, *args, **kw):
        # Apagar operação venda caso operação seja editada para compra
        if OperacaoVendaLetraCredito.objects.filter(operacao_venda=self) and self.tipo_operacao == 'C':
            OperacaoVendaLetraCredito.objects.get(operacao_venda=self).delete()
        super(OperacaoLetraCredito, self).save(*args, **kw)
    
    def carencia(self):
        if HistoricoCarenciaLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito).order_by('-data').exists():
            return HistoricoCarenciaLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito).order_by('-data')[0].carencia
        else:
            return HistoricoCarenciaLetraCredito.objects.get(data__isnull=True, letra_credito=self.letra_credito).carencia
        
    def data_carencia(self):
        return self.data + datetime.timedelta(days=self.carencia())
    
    def operacao_compra_relacionada(self):
        if self.tipo_operacao == 'V':
            return OperacaoVendaLetraCredito.objects.get(operacao_venda=self).operacao_compra
        else:
            return None
    
    def porcentagem_di(self):
        if self.tipo_operacao == 'C':
            if HistoricoPorcentagemLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito).order_by('-data').exists():
                return HistoricoPorcentagemLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito).order_by('-data')[0].porcentagem_di
            else:
                return HistoricoPorcentagemLetraCredito.objects.get(data__isnull=True, letra_credito=self.letra_credito).porcentagem_di
        elif self.tipo_operacao == 'V':
            return self.operacao_compra_relacionada().porcentagem_di()
    
    def qtd_disponivel_venda(self, desconsiderar_vendas=list()):
        vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra=self).exclude(operacao_venda__in=desconsiderar_vendas).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoLetraCredito.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def qtd_disponivel_venda_na_data(self, data):
        vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra=self).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoLetraCredito.objects.filter(id__in=vendas, data__lt=data):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def venda_permitida(self, data_venda=None):
        if data_venda == None:
            data_venda = datetime.date.today()
        if self.tipo_operacao == 'C':
            historico = HistoricoCarenciaLetraCredito.objects.exclude(data=None).filter(data__lte=data_venda).order_by('-data')
            if historico:
                # Verifica o período de carência pegando a data mais recente antes da operação de compra
                return (historico[0].carencia <= (data_venda - self.data).days)
            else:
                carencia = HistoricoCarenciaLetraCredito.objects.get(letra_credito=self.letra_credito).carencia
                return (carencia <= (data_venda - self.data).days)
        else:
            return False
    
class OperacaoVendaLetraCredito (models.Model):
    operacao_compra = models.ForeignKey('OperacaoLetraCredito', limit_choices_to={'tipo_operacao': 'C'}, related_name='operacao_compra')
    operacao_venda = models.ForeignKey('OperacaoLetraCredito', limit_choices_to={'tipo_operacao': 'V'}, related_name='operacao_venda')
    
    class Meta:
        unique_together=('operacao_compra', 'operacao_venda')
    
class HistoricoPorcentagemLetraCredito (models.Model):
    porcentagem_di = models.DecimalField(u'Porcentagem do DI', max_digits=5, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    letra_credito = models.ForeignKey('LetraCredito')
    
#     def save(self, *args, **kw):
#         try:
#             historico = HistoricoPorcentagemLetraCredito.objects.get(letra_credito=self.letra_credito, data=self.data)
#         except HistoricoPorcentagemLetraCredito.DoesNotExist:
#             super(HistoricoPorcentagemLetraCredito, self).save(*args, **kw)
    
class HistoricoCarenciaLetraCredito (models.Model):
    """
    O período de carência é medido em dias
    """
    carencia = models.IntegerField(u'Período de carência')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    letra_credito = models.ForeignKey('LetraCredito')
    
#     def save(self, *args, **kw):
#         try:
#             historico = HistoricoCarenciaLetraCredito.objects.get(letra_credito=self.letra_credito, data=self.data)
#         except HistoricoCarenciaLetraCredito.DoesNotExist:
#             super(HistoricoCarenciaLetraCredito, self).save(*args, **kw)
            
class HistoricoValorMinimoInvestimento (models.Model):
    valor_minimo = models.DecimalField(u'Valor mínimo para investimento', max_digits=9, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    letra_credito = models.ForeignKey('LetraCredito')
    
#     def save(self, *args, **kw):
#         try:
#             historico = HistoricoValorMinimoInvestimento.objects.get(letra_credito=self.letra_credito, data=self.data)
#         except HistoricoValorMinimoInvestimento.DoesNotExist:
#             if self.valor_minimo < 0:
#                 raise forms.ValidationError('Valor mínimo não pode ser negativo')
#             super(HistoricoValorMinimoInvestimento, self).save(*args, **kw)
    
class HistoricoTaxaDI (models.Model):
    data = models.DateField(u'Data')
    taxa = models.DecimalField(u'Rendimento anual', max_digits=5, decimal_places=2, unique_for_date='data')
    
    def save(self, *args, **kw):
        if not HistoricoTaxaDI.objects.filter(taxa=self.taxa, data=self.data).exists():
            super(HistoricoTaxaDI, self).save(*args, **kw)