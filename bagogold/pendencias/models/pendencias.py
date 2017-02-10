# -*- coding: utf-8 -*-
from django.db import models
 
class Pendencia (models.Model):
    investidor = models.ForeignKey('bagogold.Investidor')
    data_criacao = models.DateTimeField(u'Data de criação', auto_now_add=True)
    
    class Meta():
        abstract = True
        
class PendenciaVencimentoTesouroDireto (Pendencia):
    titulo = models.ForeignKey('bagogold.Titulo')
    quantidade = models.DecimalField(u'Quantidade', max_digits=7, decimal_places=2)
    # Adicionar UNICIDADE