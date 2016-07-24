# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.testFII import baixar_demonstrativo_rendimentos
from django.core.files import File
from django.db import models
import os
import re

def ticker_path(instance, filename):
    ticker = Acao.objects.filter(empresa=instance.empresa)[0].ticker
    return 'doc proventos/{0}/{1}'.format(re.sub('\d', '', ticker), filename)

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
        
    def save(self, *args, **kw):
        try:
            documento_existente = DocumentoBovespa.objects.get(empresa=self.empresa, protocolo=self.protocolo)
            if os.path.isfile(self.documento.path):
                os.remove(self.documento.path)
        except DocumentoBovespa.DoesNotExist:
            super(DocumentoBovespa, self).save(*args, **kw)
            
    def apagar_documento(self):
        if os.path.isfile(self.documento.path):
            os.remove(self.documento.path)
                
    def baixar_documento(self):
        documento = baixar_demonstrativo_rendimentos(self.url)
        self.documento.save('%s-%s.pdf' % (self.ticker_empresa(), self.protocolo), File(documento))
        
    def ticker_empresa(self):
        return Acao.objects.filter(empresa=self.empresa)[0].ticker
    
#     def pendente(self):
#        if self.tipo == 'A':
#            return len(ProventoAcaoDocumento.objects.filter(documento=self)) > 0
#        elif self.tipo == 'F':
#            return len(ProventoFIIDocumento.objects.filter(documento=self)) > 0 
    
class ProventoAcaoDocumento (models.Model):
    provento = models.ForeignKey('Provento')
    documento = models.ForeignKey('DocumentoBovespa')
    
class ProventoFIIDocumento (models.Model):
    provento = models.ForeignKey('ProventoFII')
    documento = models.ForeignKey('DocumentoBovespa')

class Pendencia (models.Model):
    documento = models.ForeignKey('DocumentoBovespa')