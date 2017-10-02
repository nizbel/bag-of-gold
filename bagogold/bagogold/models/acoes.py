# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoAcao
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic
from decimal import Decimal
from django.db import models
from django.db.models.aggregates import Count
import datetime
 
class Acao (models.Model):
    TIPOS_ACAO_NUMERO = {3: u'ON',
                  4: u'PN',
                  5: u'PNA',
                  6: u'PNB',
                  7: u'PNC',
                  8: u'PNC',
                  11: u'UNT'
    }
    TIPOS_ACAO_DESCRICAO = {'ON': u'Ordinária',
                  'PN': u'Preferencial',
                  'PNA': u'Preferencial Classe A',
                  'PNB': u'Preferencial Classe B',
                  'PNC': u'Preferencial Classe C',
                  'PND': u'Preferencial Classe D',
                  'UNT': u'UNIT'
    }
    ESTADO_VIGENTE = 1
    ESTADO_ENCERRADA = 2
    ESTADOS_ACAO = {ESTADO_VIGENTE: 'Vigente',
                    ESTADO_ENCERRADA: 'Encerrada'
    }
    
    ticker = models.CharField(u'Ticker da ação', max_length=10)
    empresa = models.ForeignKey('Empresa') 
    """
    Tipos 3 (ON), 4 (PN), 5 (PNA), 6 (PNB), 7 (PNC), 8 (PND), 11 (UNT)
    """
    tipo = models.CharField(u'Tipo de ação', max_length=5)
    estado = models.SmallIntegerField(u'Estado da ação', default=ESTADO_VIGENTE, choices=ESTADOS_ACAO)
    
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
        if self.tipo in self.TIPOS_ACAO_DESCRICAO.keys():
            return self.TIPOS_ACAO_DESCRICAO[self.tipo]
        
class ProventoOficialManager(models.Manager):
    def get_queryset(self):
        return super(ProventoOficialManager, self).get_queryset().filter(oficial_bovespa=True)
    
class Provento (models.Model):
    ESCOLHAS_TIPO_PROVENTO_ACAO=(('A', "Ações"),
                            ('D', "Dividendos"),
                            ('J', "Juros sobre capital próprio"),)
    
    acao = models.ForeignKey('Acao', verbose_name='Ação')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=20, decimal_places=16)
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
    
    @property
    def valor_final(self):
        if hasattr(self, 'atualizacaoselicprovento'):
            return self.valor_unitario + self.atualizacaoselicprovento.rendimento().quantize(Decimal('0.0000000000000001'))
        return self.valor_unitario
    
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
    
class AtualizacaoSelicProvento (models.Model):
    """
    Define o total de rendimento recebido por atualizar o provento pela Selic
    """
    valor_rendimento = models.DecimalField(u'Valor do rendimento', max_digits=19, decimal_places=15, blank=True, null=True)
    data_inicio = models.DateField(u'Data de início')
    data_fim = models.DateField(u'Data de fim')
    provento = models.OneToOneField('Provento')
    
    def __unicode__(self):
        if self.valor_rendimento:
            return u'Atualização pela Selic de R$ %s' % (self.valor_rendimento)
        return u'Atualização pela Selic de %s a %s' % (self.data_inicio.strftime('%d/%m/%Y'), self.data_fim.strftime('%d/%m/%Y'))
    
    def rendimento(self):
        if self.valor_rendimento:
            return self.valor_rendimento
        
        # Se não possui valor de rendimento definido, buscar valor pelo histórico da selic atual
        from bagogold.bagogold.utils.taxas_indexacao import calcular_valor_atualizado_com_taxas_selic
        historico_selic = HistoricoTaxaSelic.objects.filter(data__range=[self.data_inicio, self.data_fim]).values('taxa_diaria').annotate(qtd_dias=Count('taxa_diaria'))
        taxas_dos_dias = {}
        for taxa_quantidade in historico_selic:
            taxas_dos_dias[taxa_quantidade['taxa_diaria']] = taxa_quantidade['qtd_dias']
        return calcular_valor_atualizado_com_taxas_selic(taxas_dos_dias, self.provento.valor_unitario) - self.provento.valor_unitario
    
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
    
    