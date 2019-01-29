# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls.base import reverse

from bagogold.bagogold.utils.misc import verificar_feriado_bovespa


class LetraCambio (models.Model):
    LC_PREFIXADO = 1
    LC_DI = 2
    LC_IPCA = 3
    
    nome = models.CharField(u'Nome', max_length=50)
    investidor = models.ForeignKey('bagogold.Investidor')
    """
    Tipo de rendimento, 1 = Prefixado, 2 = Pós-fixado, 3 = IPCA
    """    
    tipo_rendimento = models.PositiveSmallIntegerField(u'Tipo de rendimento')
    
    
    def __unicode__(self):
        return self.nome
    
    def carencia_atual(self):
        return self.carencia_na_data(datetime.date.today())
        
    def carencia_na_data(self, data):
        if HistoricoCarenciaLetraCambio.objects.filter(data__isnull=False, lc=self, data__lte=data).exists():
            return HistoricoCarenciaLetraCambio.objects.filter(data__isnull=False, lc=self, data__lte=data).order_by('-data')[0].carencia
        else:
            return HistoricoCarenciaLetraCambio.objects.get(data__isnull=True, lc=self).carencia
        
    def eh_prefixado(self):
        return self.tipo_rendimento == LetraCambio.LC_PREFIXADO
    
    def indice(self):
        if self.tipo_rendimento == LetraCambio.LC_DI:
            return 'DI'
        elif self.tipo_rendimento == LetraCambio.LC_IPCA:
            return 'IPCA'
        return 'Prefixado'
    
    def porcentagem_atual(self):
        return self.porcentagem_na_data(datetime.date.today())
        
    def porcentagem_na_data(self, data):
        if HistoricoPorcentagemLetraCambio.objects.filter(data__isnull=False, lc=self, data__lte=data).exists():
            return HistoricoPorcentagemLetraCambio.objects.filter(data__isnull=False, lc=self, data__lte=data).order_by('-data')[0].porcentagem
        else:
            return HistoricoPorcentagemLetraCambio.objects.get(data__isnull=True, lc=self).porcentagem
    
    def valor_minimo_atual(self):
        return self.valor_minimo_na_data(datetime.date.today())
        
    def valor_minimo_na_data(self, data):
        if HistoricoValorMinimoInvestimentoLetraCambio.objects.filter(data__isnull=False, lc=self, data__lte=data).exists():
            return HistoricoValorMinimoInvestimentoLetraCambio.objects.filter(data__isnull=False, lc=self, data__lte=data).order_by('-data')[0].valor_minimo
        else:
            return HistoricoValorMinimoInvestimentoLetraCambio.objects.get(data__isnull=True, lc=self).valor_minimo
        
    def vencimento_atual(self):
        return self.vencimento_na_data(datetime.date.today())
        
    def vencimento_na_data(self, data):
        if HistoricoVencimentoLetraCambio.objects.filter(data__isnull=False, data__lte=data, lc=self).exists():
            return HistoricoVencimentoLetraCambio.objects.filter(data__isnull=False, data__lte=data, lc=self).order_by('-data')[0].vencimento
        else:
            return HistoricoVencimentoLetraCambio.objects.get(data__isnull=True, lc=self).vencimento
        
    
class OperacaoLetraCambio (models.Model):
    quantidade = models.DecimalField(u'Quantidade investida/resgatada', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    lc = models.ForeignKey('LetraCambio')
    investidor = models.ForeignKey('bagogold.Investidor')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.lc, self.data.strftime('%d/%m/%Y'))
    
    def carencia(self):
        if not hasattr(self, 'guarda_carencia'):
            if HistoricoCarenciaLetraCambio.objects.filter(data__lte=self.data, lc=self.lc_id).exists():
                self.guarda_carencia = HistoricoCarenciaLetraCambio.objects.filter(data__lte=self.data, lc=self.lc_id).order_by('-data')[0].carencia
            else:
                self.guarda_carencia = HistoricoCarenciaLetraCambio.objects.get(data__isnull=True, lc=self.lc_id).carencia
        return self.guarda_carencia
        
    def data_carencia(self):
        if self.tipo_operacao == 'C':
            data_carencia = self.data + datetime.timedelta(days=self.carencia())
        elif self.tipo_operacao == 'V':
            data_carencia = self.operacao_compra_relacionada().data + datetime.timedelta(days=self.carencia())
        # Verifica se é fim de semana ou feriado
        while data_carencia.weekday() > 4 or verificar_feriado_bovespa(data_carencia):
            data_carencia += datetime.timedelta(days=1)
        return data_carencia
        
    def data_inicial(self):
        if self.tipo_operacao == 'V':
            if not hasattr(self, 'guarda_data_inicial'):
                self.guarda_data_inicial = self.operacao_compra_relacionada().data
            return self.guarda_data_inicial
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
    
    @property
    def link(self):
        return reverse('lcambio:editar_operacao_lc', kwargs={'id_operacao': self.id})
    
    def operacao_compra_relacionada(self):
        if self.tipo_operacao == 'V':
            if not hasattr(self, 'guarda_operacao_compra_relacionada'):
                self.guarda_operacao_compra_relacionada = OperacaoVendaLetraCambio.objects.filter(operacao_venda=self).select_related('operacao_compra__lc')[0].operacao_compra
            return self.guarda_operacao_compra_relacionada
        else:
            return None
    
    def porcentagem(self):
        if not hasattr(self, 'guarda_porcentagem'):
            if self.tipo_operacao == 'C':
#                 if HistoricoPorcentagemLetraCambio.objects.filter(data__lte=self.data, lc=self.lc_id).exists():
                if len([historico for historico in self.lc.historicoporcentagemletracambio_set.all() if historico.data != None and historico.data <= self.data]) > 0:
#                     self.guarda_porcentagem = self.lc.historicoporcentagemletracambio_set.filter(data__lte=self.data, lc=self.lc_id).order_by('-data')[0].porcentagem
                    self.guarda_porcentagem = sorted([historico for historico in self.lc.historicoporcentagemletracambio_set.all() if historico.data != None and historico.data <= self.data],
                                 key=lambda x: x.data, reverse=True)[0].porcentagem
                else:
#                     self.guarda_porcentagem = HistoricoPorcentagemLetraCambio.objects.get(data__isnull=True, lc=self.lc_id).porcentagem
                    self.guarda_porcentagem = [historico for historico in self.lc.historicoporcentagemletracambio_set.all() if historico.data == None][0].porcentagem
            elif self.tipo_operacao == 'V':
                self.guarda_porcentagem = self.operacao_compra_relacionada().porcentagem()
        return self.guarda_porcentagem
    
    def qtd_disponivel_venda(self, desconsiderar_vendas=list()):
        if self.tipo_operacao != 'C':
            raise ValueError('Operação deve ser de compra')
        vendas = OperacaoVendaLetraCambio.objects.filter(operacao_compra=self).exclude(operacao_venda__in=desconsiderar_vendas).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoLetraCambio.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def qtd_disponivel_venda_na_data(self, data, desconsiderar_operacao=None):
        if self.tipo_operacao != 'C':
            raise ValueError('Operação deve ser de compra')
        vendas = OperacaoVendaLetraCambio.objects.filter(operacao_compra=self, operacao_venda__data__lte=data).exclude(operacao_venda=desconsiderar_operacao).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoLetraCambio.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    @property
    def tipo_rendimento_lc(self):
        if not hasattr(self,'guarda_tipo_rendimento_lc'):
            self.guarda_tipo_rendimento_lc = self.lc.tipo_rendimento
        return self.guarda_tipo_rendimento_lc
    
#     def vencimento(self):
#         if not hasattr(self, 'guarda_vencimento'):
#             if HistoricoVencimentoLetraCambio.objects.filter(data__lte=self.data, lc=self.lc_id).exists():
#                 self.guarda_vencimento = HistoricoVencimentoLetraCambio.objects.filter(data__lte=self.data, lc=self.lc_id).order_by('-data')[0].vencimento
#             else:
#                 self.guarda_vencimento = HistoricoVencimentoLetraCambio.objects.get(data__isnull=True, lc=self.lc_id).vencimento
#         return self.guarda_vencimento
    
    def vencimento(self):
        if not hasattr(self, 'guarda_vencimento'):
            if len([historico for historico in self.lc.historicovencimentoletracambio_set.all() if historico.data != None and historico.data <= self.data]) > 0:
#                 self.guarda_vencimento = self.lc.historicovencimentoletracambio_set.filter(data__lte=self.data, lc=self.lc_id).order_by('-data')[0].vencimento
                self.guarda_vencimento = sorted([historico for historico in self.lc.historicovencimentoletracambio_set.all() if historico.data != None and historico.data <= self.data],
                                 key=lambda x: x.data, reverse=True)[0].vencimento
            else:
                self.guarda_vencimento = [historico for historico in self.lc.historicovencimentoletracambio_set.all() if historico.data == None][0].vencimento
        return self.guarda_vencimento
    
    def venda_permitida(self, data_venda=None):
        if data_venda == None:
            data_venda = datetime.date.today()
        if self.tipo_operacao == 'C':
            if HistoricoCarenciaLetraCambio.objects.filter(data__lte=data_venda).exists():
#             historico = HistoricoCarenciaLetraCambio.objects.filter(data__lte=data_venda).order_by('-data')
#             if historico:
                # Verifica o período de carência pegando a data mais recente antes da operação de compra
                return (HistoricoCarenciaLetraCambio.objects.filter(data__lte=data_venda).order_by('-data')[0].carencia <= (data_venda - self.data).days)
            else:
                carencia = HistoricoCarenciaLetraCambio.objects.get(lc=self.lc_id).carencia
                return (carencia <= (data_venda - self.data).days)
        else:
            return False
        
    @property
    def link(self):
        return reverse('lcambio:editar_operacao_lc', kwargs={'id_operacao': self.id})
    
class OperacaoVendaLetraCambio (models.Model):
    operacao_compra = models.ForeignKey('OperacaoLetraCambio', limit_choices_to={'tipo_operacao': 'C'}, related_name='operacao_compra')
    operacao_venda = models.ForeignKey('OperacaoLetraCambio', limit_choices_to={'tipo_operacao': 'V'}, related_name='operacao_venda')
    
    class Meta:
        unique_together=('operacao_compra', 'operacao_venda')
        
    @property
    def data(self):
        return self.operacao_venda.data
    
class HistoricoPorcentagemLetraCambio (models.Model):
    porcentagem = models.DecimalField(u'Porcentagem de rendimento', max_digits=5, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    lc = models.ForeignKey('LetraCambio')
    
    def alteracao_anterior(self):
        if self.data == None:
            return None
        else:
            if HistoricoPorcentagemLetraCambio.objects.filter(lc=self.lc, data__lt=self.data).exists():
                return HistoricoPorcentagemLetraCambio.objects.filter(lc=self.lc, data__lt=self.data).order_by('-data')[0]
            else:
                return HistoricoPorcentagemLetraCambio.objects.get(lc=self.lc, data=None)
            
    def alteracao_posterior(self):
        if self.data == None:
            if HistoricoPorcentagemLetraCambio.objects.filter(lc=self.lc, data__isnull=False).exists():
                return HistoricoPorcentagemLetraCambio.objects.filter(lc=self.lc, data__isnull=False).order_by('data')[0]
            return None
        else:
            if HistoricoPorcentagemLetraCambio.objects.filter(lc=self.lc, data__gt=self.data).exists():
                return HistoricoPorcentagemLetraCambio.objects.filter(lc=self.lc, data__gt=self.data).order_by('data')[0]
            return None
    
class HistoricoCarenciaLetraCambio (models.Model):
    """
    O período de carência é medido em dias
    """
    carencia = models.IntegerField(u'Período de carência')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    lc = models.ForeignKey('LetraCambio')
    
class HistoricoVencimentoLetraCambio (models.Model):
    """
    O período de vencimento é medido em dias
    """
    vencimento = models.IntegerField(u'Período de vencimento')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    lc = models.ForeignKey('LetraCambio')
            
class HistoricoValorMinimoInvestimentoLetraCambio (models.Model):
    valor_minimo = models.DecimalField(u'Valor mínimo para investimento', max_digits=9, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    lc = models.ForeignKey('LetraCambio')
    
class CheckpointLetraCambio (models.Model):
    ano = models.SmallIntegerField(u'Ano')
    operacao = models.ForeignKey('OperacaoLetraCambio', limit_choices_to={'tipo_operacao': 'C'})
    qtd_restante = models.DecimalField(u'Quantidade restante da operação', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    qtd_atualizada = models.DecimalField(u'Quantidade atualizada da operação', max_digits=17, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    
    class Meta:
        unique_together=('operacao', 'ano')