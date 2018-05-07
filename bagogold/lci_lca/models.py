# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from bagogold.bagogold.utils.misc import verificar_feriado_bovespa


class LetraCredito (models.Model):
    LCI_LCA_PREFIXADO = 1
    LCI_LCA_DI = 2
    LCI_LCA_IPCA = 3
    
    nome = models.CharField(u'Nome', max_length=50)  
    investidor = models.ForeignKey('bagogold.Investidor', related_name='lci_lca_novo')
    """
    Tipo de rendimento, 1 = Prefixado, 2 = Pós-fixado, 3 = IPCA
    """    
    tipo_rendimento = models.PositiveSmallIntegerField(u'Tipo de rendimento')
    
    def __unicode__(self):
        return self.nome
    
    def carencia_atual(self):
        if HistoricoCarenciaLetraCredito.objects.filter(data__isnull=False, letra_credito=self).exists():
            return HistoricoCarenciaLetraCredito.objects.filter(data__isnull=False, letra_credito=self).order_by('-data')[0].carencia
        else:
            return HistoricoCarenciaLetraCredito.objects.get(data__isnull=True, letra_credito=self).carencia
        
    def carencia_na_data(self, data):
        if HistoricoCarenciaLetraCredito.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).exists():
            return HistoricoCarenciaLetraCredito.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).order_by('-data')[0].carencia
        else:
            return HistoricoCarenciaLetraCredito.objects.get(data__isnull=True, letra_credito=self).carencia
    
    def porcentagem_atual(self):
        if HistoricoPorcentagemLetraCredito.objects.filter(data__isnull=False, letra_credito=self).exists():
            return HistoricoPorcentagemLetraCredito.objects.filter(data__isnull=False, letra_credito=self).order_by('-data')[0].porcentagem
        else:
            return HistoricoPorcentagemLetraCredito.objects.get(data__isnull=True, letra_credito=self).porcentagem
        
    def porcentagem_na_data(self, data):
        if HistoricoPorcentagemLetraCredito.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).exists():
            return HistoricoPorcentagemLetraCredito.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).order_by('-data')[0].porcentagem
        else:
            return HistoricoPorcentagemLetraCredito.objects.get(data__isnull=True, letra_credito=self).porcentagem
        
    def valor_minimo_atual(self):
        if HistoricoValorMinimoInvestimento.objects.filter(data__isnull=False, letra_credito=self).exists():
            return HistoricoValorMinimoInvestimento.objects.filter(data__isnull=False, letra_credito=self).order_by('-data')[0].valor_minimo
        else:
            return HistoricoValorMinimoInvestimento.objects.get(data__isnull=True, letra_credito=self).valor_minimo
        
    def valor_minimo_na_data(self, data):
        if HistoricoValorMinimoInvestimento.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).exists():
            return HistoricoValorMinimoInvestimento.objects.filter(data__isnull=False, letra_credito=self, data__lte=data).order_by('-data')[0].valor_minimo
        else:
            return HistoricoValorMinimoInvestimento.objects.get(data__isnull=True, letra_credito=self).valor_minimo
    
    def vencimento_atual(self):
        return self.vencimento_na_data(datetime.date.today())
        
    def vencimento_na_data(self, data):
        if HistoricoVencimentoLetraCredito.objects.filter(data__isnull=False, data__lte=data, letra_credito=self).exists():
            return HistoricoVencimentoLetraCredito.objects.filter(data__isnull=False, data__lte=data, letra_credito=self).order_by('-data')[0].vencimento
        else:
            return HistoricoVencimentoLetraCredito.objects.get(data__isnull=True, letra_credito=self).vencimento
        
class OperacaoLetraCredito (models.Model):
    quantidade = models.DecimalField(u'Quantidade investida/resgatada', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    letra_credito = models.ForeignKey('LetraCredito', verbose_name='Letra de Crédito')
    investidor = models.ForeignKey('bagogold.Investidor', related_name='op_lci_lca_novo')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.letra_credito, self.data.strftime('%d/%m/%Y'))
    
    def save(self, *args, **kw):
        # Apagar operação venda caso operação seja editada para compra
        if OperacaoVendaLetraCredito.objects.filter(operacao_venda=self) and self.tipo_operacao == 'C':
            OperacaoVendaLetraCredito.objects.get(operacao_venda=self).delete()
        super(OperacaoLetraCredito, self).save(*args, **kw)
    
    def carencia(self):
        if not hasattr(self, 'guarda_carencia'):
            if HistoricoCarenciaLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito_id).order_by('-data').exists():
                self.guarda_carencia = HistoricoCarenciaLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito_id).order_by('-data')[0].carencia
            else:
                self.guarda_carencia = HistoricoCarenciaLetraCredito.objects.get(data__isnull=True, letra_credito=self.letra_credito_id).carencia
        return self.guarda_carencia
        
    def data_carencia(self):
        return self.data + datetime.timedelta(days=self.carencia())
    
    def data_inicial(self):
        if self.tipo_operacao == 'V':
            return self.operacao_compra_relacionada().data
        else:
            return self.data
    
    def data_vencimento(self):
        if self.tipo_operacao == 'C':
            data_vencimento = self.data + datetime.timedelta(days=self.vencimento())
        elif self.tipo_operacao == 'V':
            data_vencimento = self.operacao_compra_relacionada().data + datetime.timedelta(days=self.vencimento())
        # Verifica se é fim de semana ou feriado
        while data_vencimento.weekday() > 4 or verificar_feriado_bovespa(data_vencimento):
            data_vencimento += datetime.timedelta(days=1)
        return data_vencimento
        
    def operacao_compra_relacionada(self):
        if self.tipo_operacao == 'V':
            if not hasattr(self, 'guarda_operacao_compra_relacionada'):
                self.guarda_operacao_compra_relacionada = OperacaoVendaLetraCredito.objects.get(operacao_venda=self).operacao_compra
            return self.guarda_operacao_compra_relacionada
        else:
            return None
    
    def porcentagem(self):
        if not hasattr(self, 'guarda_porcentagem'):
            if self.tipo_operacao == 'C':
                if HistoricoPorcentagemLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito_id).order_by('-data').exists():
                    self.guarda_porcentagem = HistoricoPorcentagemLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito_id).order_by('-data')[0].porcentagem
                else:
                    self.guarda_porcentagem = HistoricoPorcentagemLetraCredito.objects.get(data__isnull=True, letra_credito=self.letra_credito_id).porcentagem
            elif self.tipo_operacao == 'V':
                self.guarda_porcentagem = self.operacao_compra_relacionada().porcentagem()
        return self.guarda_porcentagem
    
    def qtd_disponivel_venda(self, desconsiderar_vendas=list()):
        vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra=self).exclude(operacao_venda__in=desconsiderar_vendas).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoLetraCredito.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def qtd_disponivel_venda_na_data(self, data):
        vendas = OperacaoVendaLetraCredito.objects.filter(operacao_compra=self, operacao_venda__data__lte=data).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoLetraCredito.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    @property
    def tipo_rendimento_lci_lca(self):
        if not hasattr(self,'guarda_tipo_rendimento_lci_lca'):
            self.guarda_tipo_rendimento_lci_lca = self.letra_credito.tipo_rendimento
        return self.guarda_tipo_rendimento_lci_lca
    
    def vencimento(self):
        if not hasattr(self, 'guarda_vencimento'):
            if HistoricoVencimentoLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito_id).exists():
                self.guarda_vencimento = HistoricoVencimentoLetraCredito.objects.filter(data__lte=self.data, letra_credito=self.letra_credito_id).order_by('-data')[0].vencimento
            else:
                self.guarda_vencimento = HistoricoVencimentoLetraCredito.objects.get(data__isnull=True, letra_credito=self.letra_credito_id).vencimento
        return self.guarda_vencimento
        
    def venda_permitida(self, data_venda=datetime.date.today()):
        if self.tipo_operacao == 'C':
            if HistoricoCarenciaLetraCredito.objects.filter(letra_credito=self.letra_credito_id, data__lte=data_venda).exists():
                # Verifica o período de carência pegando a data mais recente antes da operação de compra
                historico = HistoricoCarenciaLetraCredito.objects.filter(letra_credito=self.letra_credito_id, data__lte=data_venda).order_by('-data')
                return (historico[0].carencia <= (data_venda - self.data).days)
            else:
                carencia = HistoricoCarenciaLetraCredito.objects.get(letra_credito=self.letra_credito_id, data__isnull=True).carencia
                return (carencia <= (data_venda - self.data).days)
        else:
            return False
    
class OperacaoVendaLetraCredito (models.Model):
    operacao_compra = models.ForeignKey('OperacaoLetraCredito', limit_choices_to={'tipo_operacao': 'C'}, related_name='operacao_compra')
    operacao_venda = models.ForeignKey('OperacaoLetraCredito', limit_choices_to={'tipo_operacao': 'V'}, related_name='operacao_venda')
    
    class Meta:
        unique_together=('operacao_compra', 'operacao_venda')
        
    @property
    def data(self):
        return self.operacao_venda.data
    
class HistoricoPorcentagemLetraCredito (models.Model):
    porcentagem = models.DecimalField(u'Porcentagem de rendimento', max_digits=5, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    letra_credito = models.ForeignKey('LetraCredito')
    
class HistoricoCarenciaLetraCredito (models.Model):
    """
    O período de carência é medido em dias
    """
    carencia = models.IntegerField(u'Período de carência')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    letra_credito = models.ForeignKey('LetraCredito')
    
class HistoricoValorMinimoInvestimento (models.Model):
    valor_minimo = models.DecimalField(u'Valor mínimo para investimento', max_digits=9, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    letra_credito = models.ForeignKey('LetraCredito')

class HistoricoVencimentoLetraCredito (models.Model):
    """
    O período de vencimento é medido em dias
    """
    vencimento = models.IntegerField(u'Período de vencimento')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    letra_credito = models.ForeignKey('LetraCredito')    
    
    
class CheckpointLetraCredito (models.Model):
    ano = models.SmallIntegerField(u'Ano')
    operacao = models.ForeignKey('OperacaoLetraCredito', limit_choices_to={'tipo_operacao': 'C'})
    qtd_restante = models.DecimalField(u'Quantidade restante da operação', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    qtd_atualizada = models.DecimalField(u'Quantidade atualizada da operação', max_digits=17, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    
    class Meta:
        unique_together=('operacao', 'ano')