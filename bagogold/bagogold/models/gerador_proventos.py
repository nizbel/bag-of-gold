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
    TIPO_DOCUMENTO_FATO_RELEVANTE = u'Fato Relevante'
    TIPO_DOCUMENTO_COMUNICADO_MERCADO = u'Comunicado ao Mercado'
    TIPO_DOCUMENTO_AVISO_ACIONISTAS = u'Aviso aos Acionistas'
    TIPO_DOCUMENTO_AVISO_COTISTAS = u'Aviso aos Cotistas'
    TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO = u'Aviso aos Cotistas - Estruturado'
    TIPOS_DOCUMENTO_VALIDOS = [TIPO_DOCUMENTO_FATO_RELEVANTE, TIPO_DOCUMENTO_COMUNICADO_MERCADO, TIPO_DOCUMENTO_AVISO_ACIONISTAS, TIPO_DOCUMENTO_AVISO_COTISTAS, TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO]
    
    url = models.CharField(u'URL do documento', blank=True, null=True, max_length=200)
    empresa = models.ForeignKey('Empresa')
    protocolo =  models.CharField(u'Protocolo', max_length=15)
    """
    Define se é provento de ação ou FII, A = Ação, F = FII
    """
    tipo = models.CharField(u'Tipo de provento', max_length=1)
    documento = models.FileField(upload_to=ticker_path, blank=True, null=True)
    data_referencia = models.DateField(u'Data de referência')
    tipo_documento = models.CharField(u'Tipo de documento', max_length=100)
    
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
#         return re.sub('\d', '', Acao.objects.filter(empresa=self.empresa)[0].ticker)
        return self.empresa.ticker_empresa()
    
    def pendente(self):
        return PendenciaDocumentoProvento.objects.filter(documento=self).exists()
    
    def pendencias(self):
        return PendenciaDocumentoProvento.objects.filter(documento=self)
    
    def responsavel_leitura(self):
        if hasattr(self, 'investidorleituradocumento'):
            return self.investidorleituradocumento.investidor
        return None
    
    def responsavel_validacao(self):
        if hasattr(self, 'investidorvalidacaodocumento'):
            return self.investidorvalidacaodocumento.investidor
        return None
    
    def descricao_tipo(self):
        if self.tipo == 'A':
            return 'Ação'
        elif self.tipo == 'F':
            return 'FII'
        else:
            return 'Tipo indefinido'
    
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
    
    def tipo_completo(self):
        return 'Leitura' if self.tipo == 'L' else 'Validação'
    
class ProventoAcaoDocumento (models.Model):
    provento = models.ForeignKey('Provento')
    documento = models.ForeignKey('DocumentoProventoBovespa')
    versao = models.PositiveSmallIntegerField(u'Versão')
    descricao_provento = models.OneToOneField('ProventoAcaoDescritoDocumentoBovespa')
        
    class Meta:
        unique_together=(('documento', 'provento'), ('versao', 'provento'))
        
    def __unicode__(self):
        return u'Versão %s no documento %s' % (self.versao, self.documento)
        
class ProventoFIIDocumento (models.Model):
    provento = models.ForeignKey('ProventoFII')
    documento = models.ForeignKey('DocumentoProventoBovespa')
    versao = models.PositiveSmallIntegerField(u'Versão')
    descricao_provento = models.OneToOneField('ProventoFIIDescritoDocumentoBovespa')
    
    class Meta:
        unique_together=(('documento', 'provento'), ('versao', 'provento'))
        
class ProventoAcaoDescritoDocumentoBovespa (models.Model):
    acao = models.ForeignKey('Acao')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=20, decimal_places=16)
    """
    A = proventos em ações, D = dividendos, J = juros sobre capital próprio
    """
    tipo_provento = models.CharField(u'Tipo de provento', max_length=1)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento', blank=True, null=True)
    observacao = models.CharField(u'Observação', blank=True, null=True, max_length=300)
    
    def __unicode__(self):
        return u'%s de %s com valor %s e data EX %s a ser pago em %s' % (self.descricao_tipo_provento(), self.acao.ticker, self.valor_unitario, self.data_ex, self.data_pagamento)
    
    def descricao_tipo_provento(self):
        if self.tipo_provento == 'A':
            return u'Ações'
        elif self.tipo_provento == 'D':
            return u'Dividendos'
        elif self.tipo_provento == 'J':
            return u'JSCP'
        else:
            return u'Indefinido'

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

class SelicProventoAcaoDescritoDocBovespa (models.Model):
    """
    Define o total de rendimento recebido por atualizar o provento pela Selic
    """
    data_inicio = models.DateField(u'Data de início')
    data_fim = models.DateField(u'Data de fim')
    provento = models.OneToOneField('ProventoAcaoDescritoDocumentoBovespa')
    
    def __unicode__(self):
        return u'Atualização pela Selic de %s a %s' % (self.data_inicio.strftime('%d/%m/%Y'), self.data_fim.strftime('%d/%m/%Y'))

class ProventoFIIDescritoDocumentoBovespa (models.Model):
    fii = models.ForeignKey('FII')
    valor_unitario = models.DecimalField(u'Valor unitário', max_digits=20, decimal_places=16)
    """
    A = amortização, R = rendimentos
    """
    tipo_provento = models.CharField(u'Tipo de provento', max_length=1)
    data_ex = models.DateField(u'Data EX')
    data_pagamento = models.DateField(u'Data do pagamento')
    url_documento = models.CharField(u'URL do documento', blank=True, null=True, max_length=200)
    
    def __unicode__(self):
        return 'R$ %s de %s em %s com data EX %s' % (str(self.valor_unitario), self.fii.ticker, str(self.data_pagamento), str(self.data_ex))
    
    def descricao_tipo_provento(self):
        if self.tipo_provento == 'A':
            return u'Amortização'
        elif self.tipo_provento == 'R':
            return u'Rendimento'
        else:
            return u'Indefinido'
            
class PagamentoLeitura (models.Model):
    VALOR_HORA = Decimal(25)

    investidor = models.ForeignKey('Investidor')
    data = models.DateField(u'Data do pagamento')
    valor = models.DecimalField(u'Valor pago', decimal_places=2, max_digits=6)
    
    def __unicode__(self):
        return u'R$ %s pagos a %s em %s' % (self.valor, self.investidor, self.data.strftime('%d/%m/%Y'))