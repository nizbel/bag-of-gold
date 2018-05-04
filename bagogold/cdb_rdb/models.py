# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
import datetime

class CDB_RDB (models.Model):
    CDB = 'C'
    RDB = 'R'
    
    CDB_RDB_PREFIXADO = 1
    CDB_RDB_DI = 2
    CDB_RDB_IPCA = 3
    
    nome = models.CharField(u'Nome', max_length=50)
    investidor = models.ForeignKey('bagogold.Investidor', related_name='cdb_rdb_novo')
    """
    Tipo de investimento, C = CDB, R = RDB
    """
    tipo = models.CharField(u'Tipo', max_length=1)
    """
    Tipo de rendimento, 1 = Prefixado, 2 = Pós-fixado, 3 = IPCA
    """    
    tipo_rendimento = models.PositiveSmallIntegerField(u'Tipo de rendimento')
    
    
    def __unicode__(self):
        return self.nome
    
    def carencia_atual(self):
        return self.carencia_na_data(datetime.date.today())
        
    def carencia_na_data(self, data):
        if HistoricoCarenciaCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self, data__lte=data).exists():
            return HistoricoCarenciaCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self, data__lte=data).order_by('-data')[0].carencia
        else:
            return HistoricoCarenciaCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self).carencia
        
    def descricao_tipo(self):
        if self.tipo == self.CDB:
            return 'CDB'
        elif self.tipo == self.RDB:
            return 'RDB'
        raise ValueError('Tipo indefinido')
    
    def eh_prefixado(self):
        return self.tipo_rendimento == CDB_RDB.CDB_RDB_PREFIXADO
    
    def indice(self):
        if self.tipo_rendimento == CDB_RDB.CDB_RDB_DI:
            return 'DI'
        elif self.tipo_rendimento == CDB_RDB.CDB_RDB_IPCA:
            return 'IPCA'
        return 'Prefixado'
    
    def porcentagem_atual(self):
        return self.porcentagem_na_data(datetime.date.today())
        
    def porcentagem_na_data(self, data):
        if HistoricoPorcentagemCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self, data__lte=data).exists():
            return HistoricoPorcentagemCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self, data__lte=data).order_by('-data')[0].porcentagem
        else:
            return HistoricoPorcentagemCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self).porcentagem
    
    def valor_minimo_atual(self):
        return self.valor_minimo_na_data(datetime.date.today())
        
    def valor_minimo_na_data(self, data):
        if HistoricoValorMinimoInvestimentoCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self, data__lte=data).exists():
            return HistoricoValorMinimoInvestimentoCDB_RDB.objects.filter(data__isnull=False, cdb_rdb=self, data__lte=data).order_by('-data')[0].valor_minimo
        else:
            return HistoricoValorMinimoInvestimentoCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self).valor_minimo
        
    def vencimento_atual(self):
        return self.vencimento_na_data(datetime.date.today())
        
    def vencimento_na_data(self, data):
        if HistoricoVencimentoCDB_RDB.objects.filter(data__isnull=False, data__lte=data, cdb_rdb=self).exists():
            return HistoricoVencimentoCDB_RDB.objects.filter(data__isnull=False, data__lte=data, cdb_rdb=self).order_by('-data')[0].vencimento
        else:
            return HistoricoVencimentoCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self).vencimento
        
    
class OperacaoCDB_RDB (models.Model):
    quantidade = models.DecimalField(u'Quantidade investida/resgatada', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    cdb_rdb = models.ForeignKey('CDB_RDB')
    investidor = models.ForeignKey('bagogold.Investidor', related_name='op_cdb_rdb_novo')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.cdb_rdb, self.data)
    
    def carencia(self):
        if not hasattr(self, 'guarda_carencia'):
            if HistoricoCarenciaCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.cdb_rdb).exists():
                self.guarda_carencia = HistoricoCarenciaCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.cdb_rdb).order_by('-data')[0].carencia
            else:
                self.guarda_carencia = HistoricoCarenciaCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self.cdb_rdb).carencia
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
        if not hasattr(self, 'guarda_data_inicial'):
            if self.tipo_operacao == 'V':
                self.guarda_data_inicial = OperacaoVendaCDB_RDB.objects.get(operacao_venda=self).operacao_compra.data
            else:
                self.guarda_data_inicial = self.data
        return self.guarda_data_inicial
        
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
            return OperacaoVendaCDB_RDB.objects.get(operacao_venda=self).operacao_compra
        else:
            return None
    
    def porcentagem(self):
        if not hasattr(self, 'guarda_porcentagem'):
            if self.tipo_operacao == 'C':
                if HistoricoPorcentagemCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.cdb_rdb).exists():
                    self.guarda_porcentagem = HistoricoPorcentagemCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.cdb_rdb).order_by('-data')[0].porcentagem
                else:
                    self.guarda_porcentagem = HistoricoPorcentagemCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self.cdb_rdb).porcentagem
            elif self.tipo_operacao == 'V':
                self.guarda_porcentagem = self.operacao_compra_relacionada().porcentagem()
        return self.guarda_porcentagem
    
    def qtd_disponivel_venda(self, desconsiderar_vendas=list()):
        if self.tipo_operacao != 'C':
            raise ValueError('Operação deve ser de compra')
        vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=self).exclude(operacao_venda__in=desconsiderar_vendas).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoCDB_RDB.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def qtd_disponivel_venda_na_data(self, data, desconsiderar_operacao=None):
        if self.tipo_operacao != 'C':
            raise ValueError('Operação deve ser de compra')
        vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=self, operacao_venda__data__lte=data).exclude(operacao_venda=desconsiderar_operacao).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoCDB_RDB.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def vencimento(self):
        if not hasattr(self, 'guarda_vencimento'):
            if HistoricoVencimentoCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.cdb_rdb).exists():
                self.guarda_vencimento = HistoricoVencimentoCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.cdb_rdb).order_by('-data')[0].vencimento
            else:
                self.guarda_vencimento = HistoricoVencimentoCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self.cdb_rdb).vencimento
        return self.guarda_vencimento
    
    def venda_permitida(self, data_venda=None):
        if data_venda == None:
            data_venda = datetime.date.today()
        if self.tipo_operacao == 'C':
            historico = HistoricoCarenciaCDB_RDB.objects.exclude(data=None).filter(data__lte=data_venda).order_by('-data')
            if historico:
                # Verifica o período de carência pegando a data mais recente antes da operação de compra
                return (historico[0].carencia <= (data_venda - self.data).days)
            else:
                carencia = HistoricoCarenciaCDB_RDB.objects.get(cdb_rdb=self.cdb_rdb).carencia
                return (carencia <= (data_venda - self.data).days)
        else:
            return False
    
class OperacaoVendaCDB_RDB (models.Model):
    operacao_compra = models.ForeignKey('OperacaoCDB_RDB', limit_choices_to={'tipo_operacao': 'C'}, related_name='operacao_compra')
    operacao_venda = models.ForeignKey('OperacaoCDB_RDB', limit_choices_to={'tipo_operacao': 'V'}, related_name='operacao_venda')
    
    class Meta:
        unique_together=('operacao_compra', 'operacao_venda')
        
    @property
    def data(self):
        return self.operacao_venda.data
    
class HistoricoPorcentagemCDB_RDB (models.Model):
    porcentagem = models.DecimalField(u'Porcentagem de rendimento', max_digits=5, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    cdb_rdb = models.ForeignKey('CDB_RDB')
    
    def alteracao_anterior(self):
        if self.data == None:
            return None
        else:
            if HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=self.cdb_rdb, data__lt=self.data).exists():
                return HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=self.cdb_rdb, data__lt=self.data).order_by('-data')[0]
            else:
                return HistoricoPorcentagemCDB_RDB.objects.get(cdb_rdb=self.cdb_rdb, data=None)
            
    def alteracao_posterior(self):
        if self.data == None:
            if HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=self.cdb_rdb, data__isnull=False).exists():
                return HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=self.cdb_rdb, data__isnull=False).order_by('data')[0]
            return None
        else:
            if HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=self.cdb_rdb, data__gt=self.data).exists():
                return HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=self.cdb_rdb, data__gt=self.data).order_by('data')[0]
            return None
    
class HistoricoCarenciaCDB_RDB (models.Model):
    """
    O período de carência é medido em dias
    """
    carencia = models.IntegerField(u'Período de carência')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    cdb_rdb = models.ForeignKey('CDB_RDB')
    
class HistoricoVencimentoCDB_RDB (models.Model):
    """
    O período de vencimento é medido em dias
    """
    vencimento = models.IntegerField(u'Período de vencimento')
    data = models.DateField(u'Data da variação', blank=True, null=True)
    cdb_rdb = models.ForeignKey('CDB_RDB')
            
class HistoricoValorMinimoInvestimentoCDB_RDB (models.Model):
    valor_minimo = models.DecimalField(u'Valor mínimo para investimento', max_digits=9, decimal_places=2)
    data = models.DateField(u'Data da variação', blank=True, null=True)
    cdb_rdb = models.ForeignKey('CDB_RDB')
    
class CheckpointCDB_RDB (models.Model):
    ano = models.SmallIntegerField(u'Ano')
    operacao = models.ForeignKey('OperacaoCDB_RDB', limit_choices_to={'tipo_operacao': 'C'})
    qtd_restante = models.DecimalField(u'Quantidade restante da operação', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    qtd_atualizada = models.DecimalField(u'Quantidade atualizada da operação', max_digits=17, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    
    class Meta:
        unique_together=('operacao', 'ano')