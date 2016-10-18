# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoPrincipal
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
    
    
@receiver(post_save, sender=User, dispatch_uid="usuario_criado")
def create_investidor(sender, instance, created, **kwargs):
    if created:
        """
        Cria investidor para cada usuário criado
        """
        investidor = Investidor.objects.get_or_create(user=instance)
        """ 
        Cria uma divisão e configura como principal
        """
        divisao = Divisao.objects.get_or_create(investidor=investidor, nome='Geral')
        DivisaoPrincipal.objects.get_or_create(investidor=investidor, divisao=divisao)