# -*- coding: utf-8 -*-
from django.db import models
 
class CarregamentoMetronic (models.Model):
    carregar_dados = models.BooleanField(u'Carregar dados', default=False)
    ultimo_carregamento = models.DateTimeField(u'Último carregamento', auto_now=True)
    
