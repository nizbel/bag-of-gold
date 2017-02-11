# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.td import OperacaoTitulo, Titulo
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia_por_titulo
from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
import datetime
 
class Pendencia (models.Model):
    investidor = models.ForeignKey('bagogold.Investidor')
    data_criacao = models.DateTimeField(u'Data de criação', auto_now_add=True)
    
    class Meta():
        abstract = True
        
@receiver(post_save, sender=Investidor, dispatch_uid="pendencias_primeiro_acesso_dia")
def verificar_pendencias_primeiro_acesso_dia(sender, instance, **kwargs):
    print instance
    #TODO Buscar pendencias
        
class PendenciaVencimentoTesouroDireto (Pendencia):   
    titulo = models.ForeignKey('bagogold.Titulo')
    quantidade = models.DecimalField(u'Quantidade', max_digits=7, decimal_places=2)

    class Meta:
        unique_together=('titulo', 'investidor')
        
    def texto(self):
        return u'Título %s atingiu o vencimento, gerar vendas' % (self.titulo.nome())
    
    @staticmethod
    def verificar_pendencia(investidor, titulo):
        # Verificar quantidade atual de operações do investidor
        qtd_atual = quantidade_titulos_ate_dia_por_titulo(investidor, titulo.id, datetime.date.today())
        if qtd_atual > 0:
            pendencia_vencimento_td, criada = PendenciaVencimentoTesouroDireto.objects.get_or_create(investidor=investidor, titulo=titulo, 
                                                                                             defaults={'quantidade': qtd_atual})
            if (not criada) and pendencia_vencimento_td.quantidade != qtd_atual:
                pendencia_vencimento_td.quantidade = qtd_atual
                pendencia_vencimento_td.save()
        else:
            if PendenciaVencimentoTesouroDireto.objects.filter(investidor=investidor, titulo=titulo).exists():
                PendenciaVencimentoTesouroDireto.objects.filter(investidor=investidor, titulo=titulo).delete()
        
@receiver(post_save, sender=OperacaoTitulo, dispatch_uid="pendencia_vencimento_td_on_save")
def verificar_pendencia_vencimento_td_on_save(sender, instance, **kwargs):
    if instance.titulo.titulo_vencido():
        PendenciaVencimentoTesouroDireto.verificar_pendencia(instance.investidor, instance.titulo)
        
@receiver(post_delete, sender=OperacaoTitulo, dispatch_uid="pendencia_vencimento_td_on_delete")
def verificar_pendencia_vencimento_td_on_delete(sender, instance, **kwargs):
    if instance.titulo.titulo_vencido():
        PendenciaVencimentoTesouroDireto.verificar_pendencia(instance.investidor, instance.titulo)
    