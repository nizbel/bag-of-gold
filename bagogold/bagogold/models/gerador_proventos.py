# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.testFII import baixar_demonstrativo_rendimentos
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import models
from django.dispatch import receiver
import datetime
import os
import re

def ticker_path(instance, filename):
    return 'doc proventos/{0}/{1}'.format(instance.ticker_empresa(), filename)

class DocumentoProventoBovespa (models.Model):
    url = models.CharField(u'URL do documento', blank=True, null=True, max_length=200)
    empresa = models.ForeignKey('Empresa')
    protocolo =  models.CharField(u'Protocolo', max_length=10)
    """
    Define se é provento de ação ou FII, A = Ação, F = FII
    """
    tipo = models.CharField(u'Tipo de provento', max_length=1)
    documento = models.FileField(upload_to=ticker_path, blank=True, null=True)
    data_referencia = models.DateField(u'Data de referência')
    
    class Meta:
        unique_together = ('empresa', 'protocolo')
        
    def __unicode__(self):
        return self.documento.name.split('/')[-1]
        
    def apagar_documento(self):
        if os.path.isfile(self.documento.path):
            self.documento.delete()
                
    def baixar_documento(self):
        # Verificar se documento já não foi baixado
        print default_storage.exists('doc proventos/{0}/{1}.pdf'.format(self.ticker_empresa(), '%s-%s.pdf' % (self.ticker_empresa(), self.protocolo)))
#         documento = baixar_demonstrativo_rendimentos(self.url)
#         try:
#             self.documento.save('%s-%s.pdf' % (self.ticker_empresa(), self.protocolo), File(documento))
#             # Se possui '_' é porque já existia um arquivo antes, apagar este arquivo e salvar o documento novamente
#             if '_' in self.documento.name:
#                 # Apagar documento original
#                 path_documento_original = self.documento.path[:self.documento.path.find('_')] + self.extensao_documento()
#                 print path_documento_original
#                 if os.path.isfile(path_documento_original):
#                     os.remove(path_documento_original)
#                 # Apagar documento criado
#                 self.apagar_documento()
#                 # Salvar novamente
#                 self.documento.save('%s-%s.pdf' % (self.ticker_empresa(), self.protocolo), File(documento))
#         except Exception as e:
#             # Apaga o documento antes de lançar o erro
#             if self.documento:
#                 if os.path.isfile(self.documento.path):
#                     os.remove(self.documento.path)
#             raise e
    
    def extensao_documento(self):
        nome, extensao = os.path.splitext(self.documento.name)
        return extensao
    
    def ticker_empresa(self):
        return re.sub('\d', '', Acao.objects.filter(empresa=self.empresa)[0].ticker)
    
    def pendente(self):
        return len(PendenciaDocumentoProvento.objects.filter(documento=self)) > 0 

@receiver(models.signals.post_delete, sender=DocumentoProventoBovespa)
def apagar_documento_on_delete(sender, instance, **kwargs):
    """
    Apaga o documento no disco quando o arquivo é deletado da base
    """
    if instance.documento:
        if os.path.isfile(instance.documento.path):
            os.remove(instance.documento.path)
            
class ProventoAcaoDocumento (models.Model):
    provento = models.ForeignKey('Provento')
    documento = models.ForeignKey('DocumentoProventoBovespa')
    
class ProventoFIIDocumento (models.Model):
    provento = models.ForeignKey('ProventoFII')
    documento = models.ForeignKey('DocumentoProventoBovespa')

class PendenciaDocumentoProvento (models.Model):
    documento = models.ForeignKey('DocumentoProventoBovespa')
    data_criacao = models.DateField(editable=False)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.data_criacao = datetime.date.today()
        return super(PendenciaDocumentoProvento, self).save(*args, **kwargs)