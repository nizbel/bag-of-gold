# -*- coding: utf-8 -*-
from django.db import models

class DocumentoBovespa (models.Model):
    url = models.CharField(u'URL do documento', blank=True, null=True, max_length=200)
    empresa = models.ForeignKey('Empresa')
    protocolo =  models.CharField(u'Protocolo', max_length=10)
    """
    Define se é provento de ação ou FII
    """
    tipo = models.CharField(u'Tipo de provento', max_length=1)
    documento = models.FileField(upload_to='doc proventos/', blank=True, null=True)
    
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