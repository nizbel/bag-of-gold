# -*- coding: utf-8 -*-
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.dispatch.dispatcher import receiver
 
class Pendencia (models.Model):
    investidor = models.ForeignKey('bagogold.Investidor')
    data_criacao = models.DateTimeField(u'Data de criação', auto_now_add=True)
    
    class Meta():
        abstract = True
        
class PendenciaVencimentoTesouroDireto (Pendencia):
    titulo = models.ForeignKey('bagogold.Titulo')
    quantidade = models.DecimalField(u'Quantidade', max_digits=7, decimal_places=2)

    class Meta:
        unique_together=('titulo', 'investidor')
        
@receiver(user_logged_in, dispatch_uid="pendencia_vencimento_td_usuario_logado")
def verificar_pendencias_vencimento_td(sender, user, **kwargs):
    print user