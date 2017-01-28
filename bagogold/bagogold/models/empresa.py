# -*- coding: utf-8 -*-
from django.db import models
 
class Empresa (models.Model):
    nome = models.CharField('Nome da empresa', max_length=100)
    nome_pregao = models.CharField('Nome de pregão', max_length=30)
    codigo_cvm = models.CharField('Código CVM', max_length=10, blank=True, null=True)
    
    def __unicode__(self):
        return self.nome