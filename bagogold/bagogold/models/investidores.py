# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
 
class Investidor (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    corretagem_padrao = models.DecimalField(u'Corretagem padrão', max_digits=5, decimal_places=2, default=0)
    """
    F = valor fixo, P = valor percentual da operação
    """
    tipo_corretagem = models.CharField(u'Tipo de corretagem', max_length=1, default='F')
    auto_atualizar_saldo = models.BooleanField(u'Atualizar saldo automaticamente?', default=False)
    
    def __unicode__(self):
        return self.user.first_name + ' ' + self.user.last_name
    
@receiver(post_save, sender=User, dispatch_uid="user_registered")
def create_investidor(sender, instance, **kwargs):
    Investidor.objects.get_or_create(user=instance)