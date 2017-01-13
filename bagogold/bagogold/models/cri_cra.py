# -*- coding: utf-8 -*-
from django.db import models

class CRI_CRA (models.Model):
    codigo = models.CharField(u'Código', max_length=20)
    """
    Tipo de investimento, I = CRI, A = CRA
    """
    tipo = models.CharField(u'Tipo', max_length=1)
    """
    1 = Prefixado, 2 = IPCA, 3 = DI
    """
    tipo_indexacao = models.PositiveSmallIntegerField(u'Tipo de indexação')
    porcentagem = models.DecimalField(u'Porcentagem sobre indexação', decimal_places=3, max_digits=6)
    juros_adicional = models.DecimalField(u'Juros adicional', decimal_places=3, max_digits=6)
    data_emissao = models.DateField(u'Data de emissão')
    valor_emissao = models.DecimalField(u'Valor nominal na emissão', max_digits=15, decimal_places=8)
    data_vencimento = models.DateField(u'Data de vencimento')
    
    def __unicode__(self):
        return '%s, emitida em %s a R$ %s, com vencimento em %s' % (self.codigo, str(self.data_emissao), self.valor_emissao, str(self.data_vencimento))
    
class OperacaoCRI_CRA (models.Model):
    investidor = models.ForeignKey('Investidor')
    cri_cra = models.ForeignKey('CRI_CRA')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)
    quantidade = models.IntegerField(u'Quantidade')