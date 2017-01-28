# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, ProventoAcaoDocumento,\
    InvestidorLeituraDocumento, InvestidorValidacaoDocumento,\
    InvestidorRecusaDocumento
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'TEMPORÁRIO ajusta provento para documento de acionistas da AGRO'
    
    def handle(self, *args, **options):
        documento_deb = DocumentoProventoBovespa.objects.get(protocolo='536527')
        documento_aci = DocumentoProventoBovespa.objects.get(protocolo='536533')
        
        InvestidorLeituraDocumento.objects.get(documento__protocolo=documento_aci.protocolo).delete()
        InvestidorValidacaoDocumento.objects.get(documento__protocolo=documento_aci.protocolo).delete()
                
        # Apagar pendencia
        PendenciaDocumentoProvento.objects.filter(documento__protocolo=documento_aci.protocolo).delete()
        
        # Adicionar responsáveis
        responsavel_leitura_deb = InvestidorLeituraDocumento.objects.get(documento__protocolo=documento_deb.protocolo)
        responsavel_validacao_deb = InvestidorValidacaoDocumento.objects.get(documento__protocolo=documento_deb.protocolo)
        
        # Alterar decisão do responsável pela leitura do documento de debentures
        responsavel_leitura_deb.decisao = 'E'
        responsavel_leitura_deb.save()
        
        responsavel_leitura_aci = responsavel_leitura_deb
        responsavel_leitura_aci.pk = None
        responsavel_leitura_aci.documento = documento_aci
        responsavel_leitura_aci.decisao = 'C'
        responsavel_leitura_aci.save()
        responsavel_validacao_aci = responsavel_validacao_deb
        responsavel_validacao_aci.pk = None
        responsavel_validacao_aci.documento = documento_aci
        responsavel_validacao_aci.save()
        
        # Mirar provento no documento de acionistas
        provento_documento = ProventoAcaoDocumento.objects.get(documento__protocolo=documento_deb.protocolo)
        provento_documento.documento = documento_aci
        provento_documento.save()
