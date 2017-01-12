# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa
from django import forms
from django.db import models
import datetime

class CRI_CRA (models.Model):
    codigo = models.CharField(u'Código', max_length=20)
    nome = models.CharField(u'Nome', max_length=50)
    investidor = models.ForeignKey('Investidor')
    """
    Tipo de investimento, I = CRI, A = CRA
    """
    tipo = models.CharField(u'Tipo', max_length=1)
    """
    Tipo de rendimento, 1 = Pré-fixado, 2 = Pós-fixado
    """    
    tipo_rendimento = models.PositiveSmallIntegerField(u'Tipo de rendimento')
    data_emissao = 
    data_vencimento = 
    
    
    def __unicode__(self):
        return self.nome
    
