# -*- coding: utf-8 -*-

class Command(BaseCommand):
    help = 'TEMPORÁRIO ajusta provento para documento de acionistas da AGRO'
    
    def handle:
        documento_deb = DocumentoProventoBovespa.objects.get(protocolo='536527')
        documento_aci = DocumentoProventoBovespa.objects.get(protocolo='536533')
        
        # Apagar pendencia
        PendenciaDocumentoProvento.objects.filter(documento__protocolo=documento_aci.protocolo).delete()
        
        # Adicionar responsáveis
        responsavel_leitura_deb = InvestidorResponsavelLeitura.objects.get(documento__protocolo=documento_deb.protocolo)
        responsavel_validacao_deb = InvestidorResponsavelValidacao.objects.get(documento__protocolo=documento_deb.protocolo)
        
        responsavel_leitura_aci = responsavel_leitura_deb
        responsavel_leitura_aci.id = None
        responsavel_leitura_aci.documento = documento_leitura_aci
        responsavel_leitura_aci.decisao = 'C'
        responsavel_leitura_aci.save()
        responsavel_validacao_aci = responsavel_validacao_deb
        responsavel_validacao_aci.id = None
        responsavel_validacao_aci.documento = documento_leitura_aci
        repsonsavel_validacao_aci.save()

        # Alterar decisão do responsável pela leitura do documento de debentures
        responsavel_leitura_deb.decisao = 'E'
        responsavel_leitura_deb.save()
        
        # Mirar provento no documento de acionistas
        provento_documento = ProventoAcaoDocumento.objects.get(documento__protocolo=documento_deb.protocolo)
        provento_documento.documento = documento_aci
        provento_documento.documento.save()