# -*- coding: utf-8 -*-
from django.db import models
import datetime
 
class Acao (models.Model):
    ticker = models.CharField(u'Ticker da ação', max_length=10)
    empresa = models.ForeignKey('Empresa') 
    """
    Tipos 3 (ON), 4 (PN), 5 (PNA), 6 (PNB), 7 (PNC), e 8 (PND)
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
    
class Provento (models.Model):
    acao = models.ForeignKey('Acao')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=16, decimal_places=12)
    """
    A = proventos em ações, D = dividendos, J = juros sobre capital próprio
    """
    tipo_provento = models.CharField(u'Tipo de provento', max_length=1)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento', blank=True, null=True)
    observacao = models.CharField(u'Observação', blank=True, null=True, max_length=300)
    oficial_bovespa = models.BooleanField(u'Oficial Bovespa?', default=False)
    
    def __unicode__(self):
        tipo = ''
        if self.tipo_provento == 'A':
            tipo = u'Ações'
        elif self.tipo_provento == 'D':
            tipo = u'Dividendos'
        elif self.tipo_provento == 'J':
            tipo = u'JSCP'
        return u'%s de %s com valor %s e data EX %s a ser pago em %s' % (tipo, self.acao.ticker, self.valor_unitario, self.data_ex, self.data_pagamento)


class AcaoProvento (models.Model):
    """
    Define a ação recebida num evento de proventos em forma de ações
    """
    acao_recebida = models.ForeignKey('Acao')
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
    acao = models.ForeignKey('Acao')
    consolidada = models.NullBooleanField(u'Consolidada?', blank=True, null=True)
    """
    B = Buy and Hold; T = Trading
    """
    destinacao = models.CharField(u'Destinação', max_length=1)
    investidor = models.ForeignKey('Investidor')
     
    def __unicode__(self):
        return '(' + self.tipo_operacao + ') ' +str(self.quantidade) + ' ' + self.acao.ticker + ' a R$' + str(self.preco_unitario) + ' em ' + str(self.data)

    def qtd_proventos_utilizada(self):
        try:
            return UsoProventosOperacaoAcao.objects.get(operacao=self).qtd_utilizada
        except UsoProventosOperacaoAcao.DoesNotExist:
            return 0
        
    def utilizou_proventos(self):
        return self.qtd_proventos_utilizada() > 0

class UsoProventosOperacaoAcao (models.Model):
    operacao = models.ForeignKey('OperacaoAcao')
    qtd_utilizada = models.DecimalField(u'Quantidade de proventos utilizada', max_digits=11, decimal_places=2)

class OperacaoCompraVenda (models.Model):
    compra = models.ForeignKey('OperacaoAcao', limit_choices_to={'tipo_operacao': 'C'}, related_name='compra')
    venda = models.ForeignKey('OperacaoAcao', limit_choices_to={'tipo_operacao': 'V'}, related_name='venda')
    day_trade = models.NullBooleanField(u'É day trade?', blank=True)
    
class HistoricoAcao (models.Model):
    acao = models.ForeignKey('Acao', unique_for_date='data')
    data = models.DateField(u'Data')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    oficial_bovespa = models.BooleanField(u'Oficial Bovespa?', default=False)
    
    class Meta:
        unique_together = ('acao', 'data')
    
class ValorDiarioAcao (models.Model):
    acao = models.ForeignKey('Acao')
    data_hora = models.DateTimeField(u'Horário')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    
class TaxaCustodiaAcao (models.Model):
    valor_mensal = models.DecimalField(u'Valor mensal', max_digits=11, decimal_places=2)
    ano_vigencia = models.IntegerField(u'Ano de início de vigência')
    mes_vigencia = models.IntegerField(u'Mês de início de vigência')
    investidor = models.ForeignKey('Investidor')
    
    