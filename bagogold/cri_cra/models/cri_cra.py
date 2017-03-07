# -*- coding: utf-8 -*-
from django.db import models

class CRI_CRA (models.Model):
    TIPO_CRI = 'I'
    TIPO_CRA = 'A'
    ESCOLHAS_TIPO_CRI_CRA = ((TIPO_CRI, 'CRI'),
                             (TIPO_CRA, 'CRA'))
    
    
    codigo = models.CharField(u'Código', max_length=20)
    tipo = models.CharField(u'Tipo', max_length=1, choices=ESCOLHAS_TIPO_CRI_CRA)
    """
    1 = Prefixado, 2 = IPCA, 3 = DI
    """
    tipo_indexacao = models.PositiveSmallIntegerField(u'Tipo de indexação')
    porcentagem = models.DecimalField(u'Porcentagem sobre indexação', decimal_places=3, max_digits=6)
    juros_adicional = models.DecimalField(u'Juros adicional', decimal_places=3, max_digits=6)
    data_emissao = models.DateField(u'Data de emissão')
    valor_emissao = models.DecimalField(u'Valor nominal na emissão', max_digits=15, decimal_places=8)
    data_vencimento = models.DateField(u'Data de vencimento')
    amortizacao_integral_vencimento = models.BooleanField(u'Amortização integral no vencimento?')
    
    def __unicode__(self):
        return '%s, emitida em %s a R$ %s, com vencimento em %s' % (self.codigo, str(self.data_emissao), self.valor_emissao, str(self.data_vencimento))
    
    def descricao_tipo(self):
        for escolha in self.ESCOLHAS_TIPO_CRI_CRA:
            if self.tipo == escolha[0]:
                return escolha[1]
        return 'Indefinido'
    
class OperacaoCRI_CRA (models.Model):
    investidor = models.ForeignKey('bagogold.Investidor')
    cri_cra = models.ForeignKey('CRI_CRA')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    quantidade = models.IntegerField(u'Quantidade')
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    
class DataRemuneracaoCRI_CRA (models.Model):
    data = models.DateField(u'Data de remuneração')
    cri_cra = models.ForeignKey('CRI_CRA')
    
class DataAmortizacaoCRI_CRA (models.Model):
    data = models.DateField(u'Data de remuneração')
    quantidade = models.DecimalField(u'Percentual de amortização', decimal_places=4, max_digits=7)
    cri_cra = models.ForeignKey('CRI_CRA')