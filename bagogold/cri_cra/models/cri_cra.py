# -*- coding: utf-8 -*-
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models

class CRI_CRA (models.Model):
    TIPO_CRI = 'I'
    TIPO_CRA = 'A'
    ESCOLHAS_TIPO_CRI_CRA = ((TIPO_CRI, 'CRI'),
                             (TIPO_CRA, 'CRA'))
    
    TIPO_INDEXACAO_DI = 1
    TIPO_INDEXACAO_PREFIXADO = 2
    TIPO_INDEXACAO_IPCA = 3
    TIPO_INDEXACAO_SELIC = 4
    TIPO_INDEXACAO_IGPM = 5
    ESCOLHAS_TIPO_INDEXACAO = ((TIPO_INDEXACAO_DI, 'DI'),
                               (TIPO_INDEXACAO_PREFIXADO, 'Prefixado'),
                               (TIPO_INDEXACAO_IPCA, 'IPCA'),
                               (TIPO_INDEXACAO_SELIC, 'Selic'),
#                                (TIPO_INDEXACAO_IGPM, 'IGP-M')
                                )
    
    nome = models.CharField(u'Nome', max_length=50)
    codigo_isin = models.CharField(u'Código ISIN', max_length=20)
    """
    Tipo de investimento, CRA = 'A', CRI = 'I'
    """
    tipo = models.CharField(u'Tipo', max_length=1, choices=ESCOLHAS_TIPO_CRI_CRA)
    """
    1 = DI, 2 = Prefixado, 3 = IPCA, 4 = Selic, 5 = IGP-M
    """
    tipo_indexacao = models.PositiveSmallIntegerField(u'Tipo de indexação', choices=ESCOLHAS_TIPO_INDEXACAO)
    porcentagem = models.DecimalField(u'Porcentagem sobre indexação', decimal_places=3, max_digits=6)
    juros_adicional = models.DecimalField(u'Juros adicional', decimal_places=3, max_digits=6, default=0)
    data_emissao = models.DateField(u'Data de emissão')
    valor_emissao = models.DecimalField(u'Valor nominal na emissão', max_digits=15, decimal_places=8, validators=[MinValueValidator(Decimal('0.00000001'))])
    data_inicio_rendimento = models.DateField(u'Data de início do rendimento')
    data_vencimento = models.DateField(u'Data de vencimento')
    investidor = models.ForeignKey('bagogold.Investidor')
    
    class Meta:
        unique_together=('investidor', 'codigo_isin')
    
    def __unicode__(self):
        return '%s, emitida em %s a R$ %s, com vencimento em %s' % (self.codigo_isin, str(self.data_emissao), self.valor_emissao, str(self.data_vencimento))
    
    def descricao_tipo(self):
        for escolha in self.ESCOLHAS_TIPO_CRI_CRA:
            if self.tipo == escolha[0]:
                return escolha[1]
        return 'Indefinido'
    
    def descricao_tipo_indexacao(self):
        for escolha in self.ESCOLHAS_TIPO_INDEXACAO:
            if self.tipo_indexacao == escolha[0]:
                return escolha[1]
        return 'Indefinido'
    
    def indexacao_completa(self):
        return '%s%% do %s' % (self.porcentagem, self.descricao_tipo_indexacao())
    
    def amortizacao_integral_vencimento(self):
        return not (DataAmortizacaoCRI_CRA.objects.filter(cri_cra=self).count() > 0)
    
class OperacaoCRI_CRA (models.Model):
    cri_cra = models.ForeignKey('CRI_CRA')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantidade = models.IntegerField(u'Quantidade', validators=[MinValueValidator(1)])
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    taxa = models.DecimalField(u'Taxa', max_digits=11, decimal_places=2)
    
class DataRemuneracaoCRI_CRA (models.Model):
    data = models.DateField(u'Data de remuneração')
    cri_cra = models.ForeignKey('CRI_CRA')
    
    class Meta:
        unique_together=('data', 'cri_cra')
        
    def __unicode__(self):
        return u'Remuneração na data %s' % (self.data.strftime('%d/%m/%Y'))
    
class DataAmortizacaoCRI_CRA (models.Model):
    data = models.DateField(u'Data de amortização')
    percentual = models.DecimalField(u'Percentual de amortização', decimal_places=4, max_digits=7, validators = [MinValueValidator(Decimal('0.0001'))])
    cri_cra = models.ForeignKey('CRI_CRA')
    
    class Meta:
        unique_together=('data', 'cri_cra')
        
    def __unicode__(self):
        return u'Amortização de %s%% na data %s' % (self.percentual, self.data.strftime('%d/%m/%Y'))