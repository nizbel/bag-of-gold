# -*- coding: utf-8 -*-
from django.db import models

class Divisao (models.Model):
    nome = models.CharField(u'Nome da divisão', max_length=50)
    valor_objetivo = models.DecimalField(u'Objetivo', max_digits=11, decimal_places=2, blank=True)
    
    def __unicode__(self):
        return self.nome
    
class DivisaoOperacaoLC (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoLetraCredito')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=11, decimal_places=2)
    
    def save(self, *args, **kw):
        try:
            divisao_operacao_lc = DivisaoOperacaoLC.objects.get(divisao=self.divisao, operacao=self.operacao)
        except DivisaoOperacaoLC.DoesNotExist:
            super(DivisaoOperacaoLC, self).save(*args, **kw)
    
class DivisaoOperacaoAcoes (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoAcao')