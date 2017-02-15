# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from django.db import models
import re
 
class Empresa (models.Model):
    nome = models.CharField('Nome da empresa', max_length=100)
    nome_pregao = models.CharField('Nome de pregão', max_length=30)
    codigo_cvm = models.CharField('Código CVM', max_length=10, blank=True, null=True)
    
    class Meta:
        unique_together=('codigo_cvm',)
    
    def __unicode__(self):
        return self.nome
    
    def ticker_empresa(self):
        return re.sub('\d', '', Acao.objects.filter(empresa=self)[0].ticker)