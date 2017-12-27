# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import \
    PendenciaDocumentoProvento
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia_por_titulo
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
import datetime
 
class Pendencia (models.Model):
    # Tipos de investimento para pendências
    CDB_RDB = 2
    LCI_LCA = 3
    TESOURO_DIRETO = 4
    
    investidor = models.ForeignKey('bagogold.Investidor')
    data_criacao = models.DateTimeField(u'Data de criação', auto_now_add=True)
    
    class Meta():
        abstract = True
        
@receiver(post_save, sender=Investidor, dispatch_uid="pendencias_primeiro_acesso_dia")
def verificar_pendencias_primeiro_acesso_dia(sender, instance, **kwargs):
    from bagogold.pendencias.utils.investidor import verificar_pendencias_investidor
    verificar_pendencias_investidor(instance)
        
class PendenciaVencimentoTesouroDireto (Pendencia):   
    titulo = models.ForeignKey('bagogold.Titulo')
    quantidade = models.DecimalField(u'Quantidade', max_digits=7, decimal_places=2)

    class Meta:
        unique_together=('titulo', 'investidor')
        
    def texto_descricao(self):
        return u'Título %s atingiu o vencimento, gerar vendas' % (self.titulo.nome())
    
    def texto(self):
        return u'Título: <strong>%s</strong> <br>Quantidade: <strong>%s</strong>' % (self.titulo.nome(), str(self.quantidade).replace('.', ','))
    
    def texto_id(self):
        return 'titulo_vencido_%s' % (self.id)
    
    def texto_label(self):
        return u'Título vencido'
    
    def tipo_investimento(self):
        return Pendencia.TESOURO_DIRETO
    
    @staticmethod
    def verificar_pendencia(investidor, titulo_id, qtd_atual):
        if qtd_atual > 0:
            pendencia_vencimento_td, criada = PendenciaVencimentoTesouroDireto.objects.get_or_create(investidor=investidor, titulo_id=titulo_id, 
                                                                                             defaults={'quantidade': qtd_atual})
            if (not criada) and pendencia_vencimento_td.quantidade != qtd_atual:
                pendencia_vencimento_td.quantidade = qtd_atual
                pendencia_vencimento_td.save()
        else:
            if PendenciaVencimentoTesouroDireto.objects.filter(investidor=investidor, titulo__id=titulo_id).exists():
                PendenciaVencimentoTesouroDireto.objects.filter(investidor=investidor, titulo__id=titulo_id).delete()
                
@receiver(post_save, sender=OperacaoTitulo, dispatch_uid="pendencia_vencimento_td_on_save")
def verificar_pendencia_vencimento_td_on_save(sender, instance, **kwargs):
    if instance.titulo.titulo_vencido():
        # Verificar quantidade atual de operações do investidor
        qtd_atual = quantidade_titulos_ate_dia_por_titulo(instance.investidor, instance.titulo.id, datetime.date.today())
        PendenciaVencimentoTesouroDireto.verificar_pendencia(instance.investidor, instance.titulo.id, qtd_atual)
        
@receiver(post_delete, sender=OperacaoTitulo, dispatch_uid="pendencia_vencimento_td_on_delete")
def verificar_pendencia_vencimento_td_on_delete(sender, instance, **kwargs):
    if instance.titulo.titulo_vencido():
        # Verificar quantidade atual de operações do investidor
        qtd_atual = quantidade_titulos_ate_dia_por_titulo(instance.investidor, instance.titulo.id, datetime.date.today())
        PendenciaVencimentoTesouroDireto.verificar_pendencia(instance.investidor, instance.titulo.id, qtd_atual)
    
class PendenciaDocumentoGeradorProventos (Pendencia):   

    class Meta:
        unique_together=('investidor',)
        
    def texto_descricao(self):
        return u'%s documentos a serem lidos/validados' % (self.quantidade())
    
    def texto(self):
        return u'Quantidade de documentos: <strong>%s</strong>' % (self.quantidade())
    
    def texto_id(self):
        return 'provento_documento_%s' % (self.id)
    
    def texto_label(self):
        return u'Documentos a ler/validar'
    
    def quantidade(self):
        return PendenciaDocumentoProvento.objects.all().count()
    
    @staticmethod
    def verificar_pendencia(investidor):
        if PendenciaDocumentoProvento.objects.filter().exists() and investidor.user.has_perm('bagogold.pode_gerar_proventos'):
            pendencia_documento_provento, criada = PendenciaDocumentoGeradorProventos.objects.get_or_create(investidor=investidor)
        else:
            if PendenciaDocumentoGeradorProventos.objects.filter(investidor=investidor).exists():
                PendenciaDocumentoGeradorProventos.objects.filter(investidor=investidor).delete()