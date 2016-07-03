# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
 
class Investidor (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    corretagem_padrao = models.DecimalField(u'Corretagem padrão', max_digits=5, decimal_places=2, blank=True, null=True)
    """
    F = valor fixo, P = valor percentual da operação
    """
    tipo_corretagem = models.CharField(u'Tipo de corretagem', max_length=1, blank=True, null=True)
    auto_atualizar_saldo = models.BooleanField(u'Atualizar saldo automaticamente?', default=False)
    
    def __unicode__(self):
        return self.user.first_name + ' ' + self.user.last_name
    
