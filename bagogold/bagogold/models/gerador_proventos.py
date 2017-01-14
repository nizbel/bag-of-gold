# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.testFII import baixar_demonstrativo_rendimentos
from django.core.files import File
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
import re
from django.core.validators import MinLengthValidator

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
        permissions = (('pode_gerar_proventos', 'Pode gerar proventos a partir de documentos'),)
        
    def __unicode__(self):
        return u'%s-%s' % (self.empresa.ticker_empresa(), self.protocolo)
        
    def apagar_documento(self):
        if os.path.isfile(self.documento.path):
            self.documento.delete()
                
    def baixar_e_salvar_documento(self):
        # Verificar se documento já não foi baixado
        documento_existe = False
        # Extensão padrão é PDF
        extensao = 'pdf'
        diretorio_path = '{0}doc proventos/{1}/'.format(settings.MEDIA_ROOT, self.ticker_empresa())
        for (_, _, nomes_arquivo) in os.walk(diretorio_path):
            for indice, nome_arquivo in enumerate(nomes_arquivo):
                if '%s-%s' % (self.ticker_empresa(), self.protocolo) in nome_arquivo.split('.')[0]:
                    extensao = nomes_arquivo[indice].split('.')[1]
                    documento_existe = True
                    break
        if documento_existe:
            baixou_arquivo = False
            self.documento.name = 'doc proventos/{0}/{1}'.format(self.ticker_empresa(), '%s-%s.%s' % (self.ticker_empresa(), self.protocolo, extensao))
            self.save()
        else:
            baixou_arquivo = True
            documento, extensao = baixar_demonstrativo_rendimentos(self.url)
            if extensao == '':
                extensao = 'pdf'
            self.documento.save('%s-%s.%s' % (self.ticker_empresa(), self.protocolo, extensao), File(documento))
        return baixou_arquivo
    
    def extensao_documento(self):
        _, extensao = os.path.splitext(self.documento.name)
        return extensao
    
    def ticker_empresa(self):
        return re.sub('\d', '', Acao.objects.filter(empresa=self.empresa)[0].ticker)
    
    def pendente(self):
        return len(PendenciaDocumentoProvento.objects.filter(documento=self)) > 0 
    
    def responsavel_leitura(self):
        if hasattr(self, 'investidorleituradocumento'):
            return self.investidorleituradocumento.investidor
        return None
    
    def responsavel_validacao(self):
        if hasattr(self, 'investidorvalidacaodocumento'):
            return self.investidorvalidacaodocumento.investidor
        return None
    
    def ultima_recusa(self):
        recusas = InvestidorRecusaDocumento.objects.filter(documento=self).order_by('-data_recusa')
        if recusas:
            return recusas[0]
        return None

@receiver(post_save, sender=DocumentoProventoBovespa, dispatch_uid="documento_provento_bovespa_criado")
def criar_pendencia_on_save(sender, instance, created, **kwargs):
    if created:
        """
        Cria pendência
        """
        pendencia, criada = PendenciaDocumentoProvento.objects.get_or_create(documento=instance)
        if not criada:
            instance.delete()

@receiver(models.signals.post_delete, sender=DocumentoProventoBovespa)
def apagar_documento_on_delete(sender, instance, **kwargs):
    """
    Apaga o documento no disco quando o arquivo é deletado da base
    """
    if instance.documento:
        if os.path.isfile(instance.documento.path):
            os.remove(instance.documento.path)

class InvestidorLeituraDocumento (models.Model):
    documento = models.OneToOneField('DocumentoProventoBovespa')
    investidor = models.ForeignKey('Investidor')
    """
    A decisão que o leitor teve sobre o documento, C = Criar provento, E = Excluir
    """
    decisao = models.CharField(u'Decisão', max_length=1)
    data_leitura = models.DateTimeField(u'Data da leitura', auto_now_add=True)
    
    class Meta:
        unique_together=('documento', 'investidor')
        
    def __unicode__(self):
        return unicode(self.investidor)

class InvestidorRecusaDocumento (models.Model):
    documento = models.ForeignKey('DocumentoProventoBovespa')
    investidor = models.ForeignKey('Investidor', related_name='leituras_que_recusou')
    motivo = models.CharField(u'Motivo da recusa', max_length=500, validators=[MinLengthValidator(10)])
    data_recusa = models.DateTimeField(u'Data da recusa', auto_now_add=True)
    responsavel_leitura = models.ForeignKey('Investidor', related_name='leituras_recusadas')
    
class InvestidorResponsavelPendencia (models.Model):
    pendencia = models.OneToOneField('PendenciaDocumentoProvento')
    investidor = models.ForeignKey('Investidor')
    data_alocacao = models.DateTimeField(u'Data da alocação', auto_now_add=True)
    
    class Meta:
        unique_together=('pendencia', 'investidor')
        
class InvestidorValidacaoDocumento (models.Model):
    documento = models.OneToOneField('DocumentoProventoBovespa')
    investidor = models.ForeignKey('Investidor')
    data_validacao = models.DateTimeField(u'Data da validação', auto_now_add=True)
    
    class Meta:
        unique_together=('documento', 'investidor')
        
    def __unicode__(self):
        return unicode(self.investidor)
            
class PendenciaDocumentoProvento (models.Model):
    documento = models.ForeignKey('DocumentoProventoBovespa')
    data_criacao = models.DateField(auto_now_add=True)
    """
    Tipo de pendência, L = Leitura, V = Validação
    """
    tipo = models.CharField(u'Tipo de pendência', max_length=1, default='L')
    
    def responsavel(self):
        if hasattr(self, 'investidorresponsavelpendencia'):
            return self.investidorresponsavelpendencia.investidor
        return None
    
class ProventoAcaoDocumento (models.Model):
    provento = models.ForeignKey('Provento')
    documento = models.ForeignKey('DocumentoProventoBovespa')
    versao = models.PositiveSmallIntegerField(u'Versão')
    descricao_provento = models.OneToOneField('ProventoAcaoDescritoDocumentoBovespa')
        
    class Meta:
        unique_together=(('documento', 'provento'), ('versao', 'provento'))
        
class ProventoFIIDocumento (models.Model):
    provento = models.ForeignKey('ProventoFII')
    documento = models.ForeignKey('DocumentoProventoBovespa')
    versao = models.PositiveSmallIntegerField(u'Versão')
    descricao_provento = models.OneToOneField('ProventoFIIDescritoDocumentoBovespa')
    
    class Meta:
        unique_together=(('documento', 'provento'), ('versao', 'provento'))
        
class ProventoAcaoDescritoDocumentoBovespa (models.Model):
    acao = models.ForeignKey('Acao')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=16, decimal_places=12)
    """
    A = proventos em ações, D = dividendos, J = juros sobre capital próprio
    """
    tipo_provento = models.CharField(u'Tipo de provento', max_length=1)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento', blank=True, null=True)
    observacao = models.CharField(u'Observação', blank=True, null=True, max_length=300)
    
    class Meta:
        unique_together=(('data_ex', 'data_pagamento', 'acao', 'tipo_provento', 'valor_unitario'))
        
    def __unicode__(self):
        tipo = ''
        if self.tipo_provento == 'A':
            tipo = u'Ações'
        elif self.tipo_provento == 'D':
            tipo = u'Dividendos'
        elif self.tipo_provento == 'J':
            tipo = u'JSCP'
        return u'%s de %s com valor %s e data EX %s a ser pago em %s' % (tipo, self.acao.ticker, self.valor_unitario, self.data_ex, self.data_pagamento)

class AcaoProventoAcaoDescritoDocumentoBovespa (models.Model):
    """
    Define a ação recebida num evento de proventos em forma de ações
    """
    acao_recebida = models.ForeignKey('Acao')
    data_pagamento_frac = models.DateField(u'Data do pagamento de frações', blank=True, null=True)
    valor_calculo_frac = models.DecimalField(u'Valor para cálculo das frações', max_digits=14, decimal_places=10, default=0)
    provento = models.ForeignKey('ProventoAcaoDescritoDocumentoBovespa', limit_choices_to={'tipo_provento': 'A'})
    
    def __unicode__(self):
        return u'Ações de %s, com frações de R$%s a receber em %s' % (self.acao_recebida.ticker, self.valor_calculo_frac, self.data_pagamento_frac)

class ProventoFIIDescritoDocumentoBovespa (models.Model):
    fii = models.ForeignKey('FII')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=13, decimal_places=9)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento')
    url_documento = models.CharField(u'URL do documento', blank=True, null=True, max_length=200)
    
    class Meta:
        unique_together=(('data_ex', 'data_pagamento', 'fii', 'valor_unitario'))
        
    def __unicode__(self):
        return '(R$ %s de %s em %s com data EX %s' % (str(self.valor_unitario), self.fii.ticker, str(self.data_pagamento), str(self.data_ex))