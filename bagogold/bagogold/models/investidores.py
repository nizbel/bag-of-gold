# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import Divisao, DivisaoPrincipal
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
 
class Investidor (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    corretagem_padrao = models.DecimalField(u'Corretagem padrão', max_digits=5, decimal_places=2, default=0)
    """
    F = valor fixo, P = valor percentual da operação
    """
    tipo_corretagem = models.CharField(u'Tipo de corretagem', max_length=1, default='F')
    auto_atualizar_saldo = models.BooleanField(u'Atualizar saldo automaticamente?', default=False)
    
    def __unicode__(self):
        nome_completo = self.user.first_name + ' ' + self.user.last_name
        if nome_completo.strip() != '':
            return nome_completo
        else:
            return self.user.username
    
    
@receiver(post_save, sender=User, dispatch_uid="usuario_criado")
def create_investidor(sender, instance, created, **kwargs):
    if created:
        """
        Cria investidor para cada usuário criado
        """
        investidor, criado = Investidor.objects.get_or_create(user=instance)
        """ 
        Cria uma divisão e configura como principal
        """
        divisao, criado = Divisao.objects.get_or_create(investidor=investidor, nome='Geralf')
        DivisaoPrincipal.objects.get_or_create(investidor=investidor, divisao=divisao)