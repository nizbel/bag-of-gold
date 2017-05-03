# -*- coding: utf-8 -*-
from django.db import models
import datetime
from bagogold.bagogold.models.divisoes import DivisaoOperacaoAcao
 
class Acao (models.Model):
    ticker = models.CharField(u'Ticker da ação', max_length=10)
    empresa = models.ForeignKey('Empresa') 
    """
    Tipos 3 (ON), 4 (PN), 5 (PNA), 6 (PNB), 7 (PNC), 8 (PND), 11 (UNT)
    """
    tipo = models.CharField(u'Tipo de ação', max_length=5)
    
    class Meta:
        ordering = ['ticker']
        unique_together = ['ticker', 'empresa', 'tipo']
    
    def __unicode__(self):
        return self.ticker
    
    def valor_no_dia(self, dia):
        if dia == datetime.date.today():
            try:
                return ValorDiarioAcao.objects.filter(acao__ticker=self.ticker, data_hora__day=dia.day, data_hora__month=dia.month).order_by('-data_hora')[0].preco_unitario
            except:
                pass
        return HistoricoAcao.objects.filter(acao__ticker=self.ticker, data__lte=dia).order_by('-data')[0].preco_unitario
    
    def descricao_tipo(self):
        if self.tipo == 3:
            return u'Ordinária'
        elif self.tipo == 4:
            return u'Preferencial'
        elif self.tipo == 5:
            return u'Preferencial Classe A'
        elif self.tipo == 6:
            return u'Preferencial Classe B'
        elif self.tipo == 7:
            return u'Preferencial Classe C'
        elif self.tipo == 8:
            return u'Preferencial Classe D'
        elif self.tipo == 11:
            return u'UNIT'
        
    def descricao_tipo_resumido(self):
        if self.tipo == 3:
            return u'ON'
        elif self.tipo == 4:
            return u'PN'
        elif self.tipo == 5:
            return u'PNA'
        elif self.tipo == 6:
            return u'PNB'
        elif self.tipo == 7:
            return u'PNC'
        elif self.tipo == 8:
            return u'PND'
        elif self.tipo == 11:
            return u'UNT'

class ProventoOficialManager(models.Manager):
    def get_queryset(self):
        return super(ProventoOficialManager, self).get_queryset().filter(oficial_bovespa=True)
    
class Provento (models.Model):
    ESCOLHAS_TIPO_PROVENTO_ACAO=(('A', "Ações"),
                            ('D', "Dividendos"),
                            ('J', "Juros sobre capital próprio"),)
    
    acao = models.ForeignKey('Acao', verbose_name='Ação')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=22, decimal_places=18)
    """
    A = proventos em ações, D = dividendos, J = juros sobre capital próprio
    """
    tipo_provento = models.CharField(u'Tipo de provento', max_length=1)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento', blank=True, null=True)
    observacao = models.CharField(u'Observação', blank=True, null=True, max_length=300)
    oficial_bovespa = models.BooleanField(u'Oficial Bovespa?', default=False)
    
    class Meta:
        unique_together = ['acao', 'valor_unitario', 'data_ex', 'data_pagamento', 'tipo_provento', 'oficial_bovespa']
        
    def __unicode__(self):
        tipo = ''
        if self.tipo_provento == 'A':
            tipo = u'Ações'
        elif self.tipo_provento == 'D':
            tipo = u'Dividendos'
        elif self.tipo_provento == 'J':
            tipo = u'JSCP'
        return u'%s de %s com valor %s e data EX %s a ser pago em %s' % (tipo, self.acao.ticker, self.valor_unitario, self.data_ex, self.data_pagamento)
    
    def descricao_tipo_provento(self):
        if self.tipo_provento == 'A':
            return u'Ações'
        elif self.tipo_provento == 'D':
            return u'Dividendos'
        elif self.tipo_provento == 'J':
            return u'JSCP'
        else:
            return u'Indefinido'
    
    objects = ProventoOficialManager()
    gerador_objects = models.Manager()


class AcaoProvento (models.Model):
    """
    Define a ação recebida num evento de proventos em forma de ações
    """
    acao_recebida = models.ForeignKey('Acao', verbose_name='Ação')
    data_pagamento_frac = models.DateField(u'Data do pagamento de frações', blank=True, null=True)
    valor_calculo_frac = models.DecimalField(u'Valor para cálculo das frações', max_digits=14, decimal_places=10, default=0)
    provento = models.ForeignKey('Provento', limit_choices_to={'tipo_provento': 'A'})
    
    def __unicode__(self):
        return u'Ações de %s, com frações de R$%s a receber em %s' % (self.acao_recebida.ticker, self.valor_calculo_frac, self.data_pagamento_frac)
    
class OperacaoAcao (models.Model):
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)  
    quantidade = models.IntegerField(u'Quantidade') 
    data = models.DateField(u'Data', blank=True, null=True)
    corretagem = models.DecimalField(u'Corretagem', max_digits=11, decimal_places=2)
    emolumentos = models.DecimalField(u'Emolumentos', max_digits=11, decimal_places=2)
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    acao = models.ForeignKey('Acao', verbose_name='Ação')
    consolidada = models.NullBooleanField(u'Consolidada?', blank=True, null=True)
    """
    B = Buy and Hold; T = Trading
    """
    destinacao = models.CharField(u'Destinação', max_length=1)
    investidor = models.ForeignKey('Investidor')
     
    def __unicode__(self):
        return '(' + self.tipo_operacao + ') ' +str(self.quantidade) + ' ' + self.acao.ticker + ' a R$' + str(self.preco_unitario) + ' em ' + str(self.data)

    def qtd_proventos_utilizada(self):
        qtd_total = 0
        for divisao in DivisaoOperacaoAcao.objects.filter(operacao=self):
            if hasattr(divisao, 'usoproventosoperacaoacao'):
                qtd_total += divisao.usoproventosoperacaoacao.qtd_utilizada
        return qtd_total
        
    def utilizou_proventos(self):
        return self.qtd_proventos_utilizada() > 0

class UsoProventosOperacaoAcao (models.Model):
    operacao = models.ForeignKey('OperacaoAcao', verbose_name='Operação')
    qtd_utilizada = models.DecimalField(u'Quantidade de proventos utilizada', max_digits=11, decimal_places=2)
    divisao_operacao = models.OneToOneField('DivisaoOperacaoAcao')

    def __unicode__(self):
        return 'R$ ' + str(self.qtd_utilizada) + ' em ' + self.divisao_operacao.divisao.nome + ' para ' + unicode(self.divisao_operacao.operacao)
    
class OperacaoCompraVenda (models.Model):
    compra = models.ForeignKey('OperacaoAcao', limit_choices_to={'tipo_operacao': 'C'}, related_name='compra', verbose_name='Compra')
    venda = models.ForeignKey('OperacaoAcao', limit_choices_to={'tipo_operacao': 'V'}, related_name='venda', verbose_name='Venda')
    day_trade = models.NullBooleanField(u'É day trade?', blank=True)
    quantidade = models.IntegerField(u'Quantidade de ações')
    
    class Meta:
        unique_together = ('compra', 'venda')
        
    def __unicode__(self):
        return 'Compra: ' + self.compra.__unicode__() + ', Venda: ' + self.venda.__unicode__()
    
class HistoricoAcao (models.Model):
    acao = models.ForeignKey('Acao', unique_for_date='data', verbose_name='Ação')
    data = models.DateField(u'Data')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    oficial_bovespa = models.BooleanField(u'Oficial Bovespa?', default=False)
    
    class Meta:
        unique_together = ('acao', 'data')
    
class ValorDiarioAcao (models.Model):
    acao = models.ForeignKey('Acao', verbose_name='Ação')
    data_hora = models.DateTimeField(u'Horário')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    
    def __unicode__(self):
        return self.acao.ticker + ' em ' + str(self.data_hora) + ': R$' + str(self.preco_unitario)
    
class TaxaCustodiaAcao (models.Model):
    valor_mensal = models.DecimalField(u'Valor mensal', max_digits=11, decimal_places=2)
    ano_vigencia = models.IntegerField(u'Ano de início de vigência')
    mes_vigencia = models.IntegerField(u'Mês de início de vigência')
    investidor = models.ForeignKey('Investidor')
    
    