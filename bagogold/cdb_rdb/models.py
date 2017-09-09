# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
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
        if HistoricoVencimentoCDB_RDB.objects.filter(data__isnull=false, data__lte=data, cdb_rdb=self).exists():
            return HistoricoVencimentoCDB_RDB.objects.filter(data__isnull=false, data__lte=data, cdb_rdb=self).order_by('-data')[0].vencimento
        else:
            return HistoricoVencimentoCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self).vencimento
        
    
class OperacaoCDB_RDB (models.Model):
    quantidade = models.DecimalField(u'Quantidade investida/resgatada', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    investimento = models.ForeignKey('CDB_RDB')
    investidor = models.ForeignKey('bagogold.Investidor', related_name='op_cdb_rdb_novo')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.investimento, self.data)
    
    def save(self, *args, **kw):
        # Apagar operação venda caso operação seja editada para compra
        if OperacaoVendaCDB_RDB.objects.filter(operacao_venda=self) and self.tipo_operacao == 'C':
            OperacaoVendaCDB_RDB.objects.get(operacao_venda=self).delete()
        super(OperacaoCDB_RDB, self).save(*args, **kw)
    
    def carencia(self):
        if HistoricoCarenciaCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).exists():
            return HistoricoCarenciaCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).order_by('-data')[0].carencia
        else:
            return HistoricoCarenciaCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self.investimento).carencia
        
    def data_carencia(self):
        data_carencia = self.data + datetime.timedelta(days=self.carencia())
        # Verifica se é fim de semana ou feriado
        while data_carencia.weekday() > 4 or verificar_feriado_bovespa(data_carencia):
            data_carencia += datetime.timedelta(days=1)
        return data_carencia
        
    def data_vencimento(self):
        data_vencimento = self.data + datetime.timedelta(days=self.vencimento())
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
        if self.tipo_operacao == 'C':
            if HistoricoPorcentagemCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).exists():
                return HistoricoPorcentagemCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).order_by('-data')[0].porcentagem
            else:
                return HistoricoPorcentagemCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self.investimento).porcentagem
        elif self.tipo_operacao == 'V':
            return self.operacao_compra_relacionada().porcentagem()
    
    def qtd_disponivel_venda(self, desconsiderar_vendas=list()):
        vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=self).exclude(operacao_venda__in=desconsiderar_vendas).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoCDB_RDB.objects.filter(id__in=vendas):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def qtd_disponivel_venda_na_data(self, data):
        vendas = OperacaoVendaCDB_RDB.objects.filter(operacao_compra=self).values_list('operacao_venda__id', flat=True)
        qtd_vendida = 0
        for venda in OperacaoCDB_RDB.objects.filter(id__in=vendas, data__lt=data):
            qtd_vendida += venda.quantidade
        return self.quantidade - qtd_vendida
    
    def vencimento(self):
        if HistoricoVencimentoCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).exists():
            return HistoricoVencimentoCDB_RDB.objects.filter(data__lte=self.data, cdb_rdb=self.investimento).order_by('-data')[0].vencimento
        else:
            return HistoricoVencimentoCDB_RDB.objects.get(data__isnull=True, cdb_rdb=self.investimento).vencimento
    
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
    
#     def save(self, *args, **kw):
#         if self.valor_minimo < 0:
#             raise forms.ValidationError('Valor mínimo não pode ser negativo')
#         super(HistoricoValorMinimoInvestimentoCDB_RDB, self).save(*args, **kw)
    
