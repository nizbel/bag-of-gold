# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.td import OperacaoTitulo, Titulo
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia_por_titulo
from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.signals import post_save
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
    titulo = Titulo.objects.get(tipo='LTN', data_vencimento=datetime.date(2017, 1, 1))
    # Verificar quantidade atual de operações do investidor
    qtd_atual = quantidade_titulos_ate_dia_por_titulo(instance, titulo.id, datetime.date.today())
    print qtd_atual
    if qtd_atual > 0:
        pendencia_vencimento_td, criada = PendenciaVencimentoTesouroDireto.objects.get_or_create(investidor=instance, titulo=titulo, defaults={'quantidade': qtd_atual})
        if (not criada) and pendencia_vencimento_td.quantidade != qtd_atual:
            pendencia_vencimento_td.quantidade = qtd_atual
            pendencia_vencimento_td.save()
    else:
        if PendenciaVencimentoTesouroDireto.objects.filter(investidor=instance, titulo=titulo).exists():
            PendenciaVencimentoTesouroDireto.objects.filter(investidor=instance, titulo=titulo).delete()
    
        
class PendenciaVencimentoTesouroDireto (Pendencia):
    titulo = models.ForeignKey('bagogold.Titulo')
    quantidade = models.DecimalField(u'Quantidade', max_digits=7, decimal_places=2)

    class Meta:
        unique_together=('titulo', 'investidor')
        
    def texto(self):
        return u'Título %s atingiu o vencimento, gerar vendas' % (self.titulo.nome())
        
@receiver(post_save, sender=OperacaoTitulo, dispatch_uid="pendencias_vencimento_td")
def verificar_pendencias_vencimento_td(sender, instance, **kwargs):
    if instance.titulo.titulo_vencido():
        # Verificar quantidade atual de operações do investidor
        qtd_atual = quantidade_titulos_ate_dia_por_titulo(instance.investidor, instance.titulo.id, datetime.date.today())
        print qtd_atual
        if qtd_atual > 0:
            pendencia_vencimento_td = PendenciaVencimentoTesouroDireto.objects.get_or_create(investidor=instance.investidor, titulo=instance.titulo)
            if pendencia_vencimento_td.quantidade != qtd_atual:
                pendencia_vencimento_td.quantidade = qtd_atual
                pendencia_vencimento_td.save()
        else:
            if PendenciaVencimentoTesouroDireto.objects.filter(investidor=instance.investidor, titulo=instance.titulo).exists():
                PendenciaVencimentoTesouroDireto.objects.filter(investidor=instance.investidor, titulo=instance.titulo).delete()
    