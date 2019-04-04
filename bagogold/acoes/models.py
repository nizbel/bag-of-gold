# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from math import floor

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.aggregates import Count
from django.urls.base import reverse

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic


class Acao (models.Model):
    TIPOS_ACAO_NUMERO = {3: u'ON',
                  4: u'PN',
                  5: u'PNA',
                  6: u'PNB',
                  7: u'PNC',
                  8: u'PND',
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
    
    ticker = models.CharField(u'Ticker da ação', max_length=10)
    empresa = models.ForeignKey('bagogold.Empresa', related_name='acao_novo') 
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
        if self.tipo in self.TIPOS_ACAO_DESCRICAO.keys():
            return self.TIPOS_ACAO_DESCRICAO[self.tipo]
        
class ProventoOficialManager(models.Manager):
    def get_queryset(self):
        return super(ProventoOficialManager, self).get_queryset().filter(oficial_bovespa=True)
    
class ProventoAcao (models.Model):
    TIPO_PROVENTO_DIVIDENDO = 1
    DESCRICAO_TIPO_PROVENTO_DIVIDENDO = u'Dividendos'
    TIPO_PROVENTO_JSCP = 2
    DESCRICAO_TIPO_PROVENTO_JSCP = u'JSCP'
    TIPO_PROVENTO_ACOES = 3
    DESCRICAO_TIPO_PROVENTO_ACOES = u'Ações'
    
    ESCOLHAS_TIPO_PROVENTO_ACAO=((TIPO_PROVENTO_DIVIDENDO, DESCRICAO_TIPO_PROVENTO_DIVIDENDO),
                            (TIPO_PROVENTO_JSCP, DESCRICAO_TIPO_PROVENTO_JSCP),
                            (TIPO_PROVENTO_ACOES, DESCRICAO_TIPO_PROVENTO_ACOES),)
    
    acao = models.ForeignKey('Acao', verbose_name='Ação')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=20, decimal_places=16)
    """
    1 = dividendos, 2 = juros sobre capital próprio, 3 = proventos em ações
    """
    tipo_provento = models.SmallIntegerField(u'Tipo de provento')
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento', blank=True, null=True)
    observacao = models.CharField(u'Observação', blank=True, null=True, max_length=300)
    oficial_bovespa = models.BooleanField(u'Oficial Bovespa?', default=False)
    
    class Meta:
        unique_together = ['acao', 'valor_unitario', 'data_ex', 'data_pagamento', 'tipo_provento', 'oficial_bovespa']
        
    def __unicode__(self):
        tipo = self.descricao_tipo_provento
        return u'%s de %s com valor %s e data EX %s a ser pago em %s' % (tipo, self.acao.ticker, self.valor_unitario, self.data_ex, self.data_pagamento)
    
    @property
    def descricao_tipo_provento(self):
        for tipo_id, descricao in ProventoAcao.ESCOLHAS_TIPO_PROVENTO_ACAO:
            if tipo_id == self.tipo_provento:
                return descricao
        raise ValueError('Tipo de provento inválido')
    
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
    provento = models.ForeignKey('ProventoAcao', limit_choices_to={'tipo_provento': 'A'})
    
    def __unicode__(self):
        return u'Ações de %s, com frações de R$%s a receber em %s' % (self.acao_recebida.ticker, self.valor_calculo_frac, self.data_pagamento_frac)
    
class AtualizacaoSelicProvento (models.Model):
    """
    Define o total de rendimento recebido por atualizar o provento pela Selic
    """
    valor_rendimento = models.DecimalField(u'Valor do rendimento', max_digits=19, decimal_places=15, blank=True, null=True)
    data_inicio = models.DateField(u'Data de início')
    data_fim = models.DateField(u'Data de fim')
    provento = models.OneToOneField('ProventoAcao')
    
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
    DESTINACAO_BH = 1
    DESCRICAO_DESTINACAO_BH = 'Buy and Hold'
    DESTINACAO_TRADE = 2
    DESCRICAO_DESTINACAO_TRADE = 'Trading'
    
    ESCOLHAS_DESTINACAO = ((DESTINACAO_BH, DESCRICAO_DESTINACAO_BH),
                           (DESTINACAO_TRADE, DESCRICAO_DESTINACAO_TRADE))
    
    @staticmethod
    def destinacao_descricao(destinacao):
        for escolha in OperacaoAcao.ESCOLHAS_DESTINACAO:
            if escolha[0] == destinacao:
                return escolha[1]
    
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)  
    quantidade = models.IntegerField(u'Quantidade') 
    data = models.DateField(u'Data', blank=True, null=True)
    corretagem = models.DecimalField(u'Corretagem', max_digits=11, decimal_places=2)
    emolumentos = models.DecimalField(u'Emolumentos', max_digits=11, decimal_places=2)
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    acao = models.ForeignKey('Acao', verbose_name='Ação')
    consolidada = models.NullBooleanField(u'Consolidada?', blank=True, null=True)
    """
    1 = Buy and Hold; 2 = Trading
    """
    destinacao = models.SmallIntegerField(u'Destinação', choices=ESCOLHAS_DESTINACAO)
    investidor = models.ForeignKey('bagogold.Investidor', related_name='op_acao_novo')
     
    def __unicode__(self):
        return '(' + self.tipo_operacao + ') ' +str(self.quantidade) + ' ' + self.acao.ticker + ' a R$' + str(self.preco_unitario) + ' em ' + str(self.data.strftime('%d/%m/%Y'))

    def qtd_proventos_utilizada(self):
        qtd_total = sum([uso_proventos.qtd_utilizada for uso_proventos in self.usoproventosoperacaoacao_set.all()])
        return qtd_total
        
    def utilizou_proventos(self):
#         return UsoProventosOperacaoAcao.objects.filter(operacao=self).exists()
        return self.usoproventosoperacaoacao_set.exists()
    
    @property
    def link(self):
        if self.destinacao == OperacaoAcao.DESTINACAO_BH:
            return reverse('acoes:bh:editar_operacao_bh', kwargs={'id_operacao': self.id})
        else:
            return reverse('acoes:trading:editar_operacao_acao_t', kwargs={'id_operacao': self.id})
            

class UsoProventosOperacaoAcao (models.Model):
    operacao = models.ForeignKey('OperacaoAcao', verbose_name='Operação')
    qtd_utilizada = models.DecimalField(u'Quantidade de proventos utilizada', max_digits=11, decimal_places=2)
    divisao_operacao = models.OneToOneField('bagogold.DivisaoOperacaoAcao', related_name='uso_prov_op_acao_novo')

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
    investidor = models.ForeignKey('bagogold.Investidor', related_name='tx_custodia_novo')
    
# Eventos
class EventoAcao (models.Model):
    acao = models.ForeignKey('Acao')
    data = models.DateField(u'Data')
    
    class Meta():
        abstract = True
        
class EventoAlteracaoAcao (EventoAcao):
    nova_acao = models.ForeignKey('Acao', related_name='alteracao')
    
    class Meta:
        unique_together=(('acao',))
    
class EventoAgrupamentoAcao (EventoAcao):
    proporcao = models.DecimalField(u'Proporção de agrupamento', max_digits=13, decimal_places=12, validators=[MaxValueValidator(Decimal('0.999999999999'))])
    valor_fracao = models.DecimalField(u'Valor para as frações', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    data_pgto_fracao = models.DateField(u'Data de pagamento para as frações', blank=True, null=True)
    
    class Meta:
        unique_together=('acao', 'data')
        
    def qtd_apos(self, qtd_inicial):
        return Decimal(floor(qtd_inicial * self.proporcao))
    
    def preco_medio_apos(self, preco_medio_inicial, qtd_inicial):
        qtd_apos = self.qtd_apos(qtd_inicial)
        return 0 if qtd_apos == 0 else preco_medio_inicial * qtd_inicial / qtd_apos
    
class EventoDesdobramentoAcao (EventoAcao):
    proporcao = models.DecimalField(u'Proporção de desdobramento', max_digits=16, decimal_places=12, validators=[MinValueValidator(Decimal('1.000000000001'))])
    valor_fracao = models.DecimalField(u'Valor para as frações', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    data_pgto_fracao = models.DateField(u'Data de pagamento para as frações', blank=True, null=True)
    
    class Meta:
        unique_together=('acao', 'data')
        
    def qtd_apos(self, qtd_inicial):
        return Decimal(floor(qtd_inicial * self.proporcao))
    
    def preco_medio_apos(self, preco_medio_inicial, qtd_inicial):
        qtd_apos = self.qtd_apos(qtd_inicial)
        return 0 if qtd_apos == 0 else preco_medio_inicial * qtd_inicial / qtd_apos
    
class EventoBonusAcao (EventoAcao):
    proporcao = models.DecimalField(u'Proporção de desdobramento', max_digits=16, decimal_places=12, validators=[MinValueValidator(Decimal('0.000000000001'))])
    valor_fracao = models.DecimalField(u'Valor para as frações', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    data_pgto_fracao = models.DateField(u'Data de pagamento para as frações', blank=True, null=True)
    preco_unitario_acao = models.DecimalField(u'Preço unitário por ação', blank=True, null=True, max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('acao', 'data')
        
    def qtd_bonus(self, qtd_inicial):
        return Decimal(floor(qtd_inicial * self.proporcao))
    
#     def preco_medio_apos(self, preco_medio_inicial, qtd_inicial):
#         qtd_apos = self.qtd_apos(qtd_inicial)
#         return 0 if qtd_apos == 0 else preco_medio_inicial * qtd_inicial / qtd_apos
    
    @property
    def acao_recebida(self):
        if hasattr(self, 'eventobonusacaorecebida'):
            return self.eventobonusacaorecebida.acao_recebida
        return self.acao
    
class EventoBonusAcaoRecebida (models.Model):
    bonus = models.OneToOneField('EventoBonusAcao')
    acao_recebida = models.ForeignKey('Acao')
    
    def save(self, *args, **kwargs):
        if self.acao_recebida == self.bonus.acao:
            raise ValueError('Ação recebida não pode ser igual a ação que recebeu bonificação')
        super(EventoBonusAcaoRecebida, self).save(*args, **kwargs)
    
# Checkpoints
class CheckpointAcao(models.Model):
    ano = models.SmallIntegerField(u'Ano')
    acao = models.ForeignKey('Acao')
    destinacao = models.SmallIntegerField(u'Destinação', choices=OperacaoAcao.ESCOLHAS_DESTINACAO)
    investidor = models.ForeignKey('bagogold.Investidor')
    quantidade = models.IntegerField(u'Quantidade no ano', validators=[MinValueValidator(0)])
    preco_medio = models.DecimalField(u'Preço médio', max_digits=11, decimal_places=4)
    
    class Meta:
        unique_together=('acao', 'ano', 'investidor', 'destinacao')
        
    def __unicode__(self):
        return u'%s: %s com %s %s a R$ %s (%s)' % (self.ano, self.investidor, self.quantidade, self.acao, self.preco_medio, 
                                                   OperacaoAcao.destinacao_descricao(self.destinacao))
        
class CheckpointProventosAcao(models.Model):
    ano = models.SmallIntegerField(u'Ano')
    destinacao = models.SmallIntegerField(u'Destinação', choices=OperacaoAcao.ESCOLHAS_DESTINACAO)
    investidor = models.ForeignKey('bagogold.Investidor')
    valor = models.DecimalField(u'Valor da poupança de proventos', max_digits=22, decimal_places=16)
        
    class Meta:
        unique_together=('ano', 'investidor', 'destinacao')
    