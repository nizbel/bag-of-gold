# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.testFII import baixar_demonstrativo_rendimentos
from django.core.files import File
from django.db import models
from django.dispatch import receiver
import os
import re

def ticker_path(instance, filename):
    return 'doc proventos/{0}/{1}'.format(re.sub('\d', '', instance.ticker_empresa()), filename)

class DocumentoBovespa (models.Model):
    url = models.CharField(u'URL do documento', blank=True, null=True, max_length=200)
    empresa = models.ForeignKey('Empresa')
    protocolo =  models.CharField(u'Protocolo', max_length=10)
    """
    Define se é provento de ação ou FII
    """
    tipo = models.CharField(u'Tipo de provento', max_length=1)
    documento = models.FileField(upload_to=ticker_path, blank=True, null=True)
    data_referencia = models.DateField(u'Data de referência')
    
    class Meta:
        unique_together = ('empresa', 'protocolo')
        
    def apagar_documento(self):
        if os.path.isfile(self.documento.path):
            os.remove(self.documento.path)
                
    def baixar_documento(self):
        documento = baixar_demonstrativo_rendimentos(self.url)
        try:
            self.documento.save('%s-%s.pdf' % (self.ticker_empresa(), self.protocolo), File(documento))
        except Exception as e:
            # Apaga o documento antes de lançar o erro
            if self.documento:
                if os.path.isfile(self.documento.path):
                    os.remove(self.documento.path)
            raise e
        
    def ticker_empresa(self):
        return Acao.objects.filter(empresa=self.empresa)[0].ticker
    
#     def pendente(self):
#        if self.tipo == 'A':
#            return len(ProventoAcaoDocumento.objects.filter(documento=self)) > 0
#        elif self.tipo == 'F':
#            return len(ProventoFIIDocumento.objects.filter(documento=self)) > 0 

@receiver(models.signals.post_delete, sender=DocumentoBovespa)
def apagar_documento_on_delete(sender, instance, **kwargs):
    """
    Apaga o documento no disco quando o arquivo é deletado da base
    """
    if instance.documento:
        if os.path.isfile(instance.documento.path):
            os.remove(instance.documento.path)
            
class ProventoAcaoDocumento (models.Model):
    provento = models.ForeignKey('Provento')
    documento = models.ForeignKey('DocumentoBovespa')
    
class ProventoFIIDocumento (models.Model):
    provento = models.ForeignKey('ProventoFII')
    documento = models.ForeignKey('DocumentoBovespa')

class Pendencia (models.Model):
    documento = models.ForeignKey('DocumentoBovespa')