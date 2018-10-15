# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from itertools import chain

from django.db import transaction
from lxml import etree

from bagogold.bagogold.models.acoes import Provento, AcaoProvento, \
    AtualizacaoSelicProvento
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    PendenciaDocumentoProvento, ProventoAcaoDocumento, \
    ProventoAcaoDescritoDocumentoBovespa, AcaoProventoAcaoDescritoDocumentoBovespa, \
    InvestidorValidacaoDocumento, InvestidorRecusaDocumento, ProventoFIIDocumento, \
    ProventoFIIDescritoDocumentoBovespa, DocumentoProventoBovespa
from bagogold.fii.models import ProventoFII, FII


def alocar_pendencia_para_investidor(pendencia, investidor):
    """
    Torna um investidor responsável pela pendência especificada
    Parâmetros: Pendência
                Investidor
    Retorno: (Se operação obteve sucesso, mensagem de explicação)
    """
    # Verifica se já há responsável pela pendência
    if pendencia.responsavel() != None:
        return (False, u'Pendência já possui responsável')
    # Verifica se pendência é de validação e investidor já foi responsável pela leitura
    elif pendencia.tipo == 'V' and pendencia.documento.responsavel_leitura() == investidor:
        return (False, u'Investidor já fez a leitura do documento, não pode validar')
    
    try:
        InvestidorResponsavelPendencia.objects.create(pendencia=pendencia, investidor=investidor)
    except:
        return (False, u'Não foi possível alocar a pendência')
    return (True, u'Alocação de pendência feita com sucesso!')

def desalocar_pendencia_de_investidor(pendencia, investidor):
    """
    Remove a responsabilidade de um investidor sobre a pendência apontada
    Parâmetros: Pendência
                Investidor
    Retorno: (Se operação obteve sucesso, mensagem de explicação)
    """
    try:
        InvestidorResponsavelPendencia.objects.get(pendencia=pendencia, investidor=investidor).delete()
        return (True, u'Desalocação de pendência feita com sucesso!')
    except InvestidorResponsavelPendencia.DoesNotExist:
        return (False, u'A pendência não estava alocada para o investidor')
    except:
        return (False, u'Não foi possível desalocar a pendência')
    
def salvar_investidor_responsavel_por_leitura(pendencia, investidor, decisao):   
    """
    Cria vínculo de responsabilidade pela leitura do documento para o investidor. Altera pendência de leitura para validação
    Parâmetros: Pendência
                Investidor
                Decisão tomada na leitura ('C' (Criar provento) ou 'E' (Excluir))
    Retorno: Vínculo de responsabilidade pela leitura
    """
    if pendencia.tipo != 'L':
        raise ValueError(u'Pendência deve ser do tipo "Leitura"')
    if decisao not in ['C', 'E']:
        raise ValueError(u'Decisão sobre o documento inválida')
    
    # Desaloca pendência
    retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, investidor)
    if not retorno:
        raise ValueError(mensagem)
    
    responsavel_leitura = InvestidorLeituraDocumento.objects.create(documento=pendencia.documento, investidor=investidor, decisao=decisao)
    # Alterar pendência para validação
    pendencia.tipo = 'V'
    pendencia.save()
    return responsavel_leitura

def desfazer_investidor_responsavel_por_leitura(pendencia, investidor):
    """
    Desfaz vínculo de responsabilidade pela leitura, retorna pendência para leitura, realoca pendência para leitor
    Parâmetros: Pendência
                Investidor
    """
    if pendencia.tipo != 'L':
        pendencia.tipo = 'L'
        pendencia.save()
    
    InvestidorResponsavelPendencia.objects.get_or_create(pendencia=pendencia, investidor=investidor)
    
    try:
        InvestidorLeituraDocumento.objects.get(documento=pendencia.documento, investidor=investidor).delete()
    except InvestidorLeituraDocumento.DoesNotExist:
        pass

def salvar_investidor_responsavel_por_validacao(pendencia, investidor):   
    """
    Cria vínculo de responsabilidade pela validação do documento para o investidor
    Parâmetros: Pendência
                Investidor
    Retorno: Vínculo de responsabilidade pela validação
    """
    if pendencia.tipo != 'V':
        raise ValueError(u'Pendência deve ser do tipo "Validação"')
    
    # Desaloca pendência
    retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, investidor)
    if not retorno:
        raise ValueError(mensagem)
    
    responsavel_validacao = InvestidorValidacaoDocumento.objects.create(documento=pendencia.documento, investidor=investidor)
    return responsavel_validacao

def desfazer_investidor_responsavel_por_validacao(pendencia, investidor):
    """
    Desfaz vínculo de responsabilidade pela validação, retorna pendência para validação, realoca pendência para validador
    Parâmetros: Pendência
                Investidor
    """
    if pendencia.tipo != 'V':
        pendencia.tipo = 'V'
        pendencia.save()
    
    InvestidorResponsavelPendencia.objects.get_or_create(pendencia=pendencia, investidor=investidor)
    
    try:
        InvestidorValidacaoDocumento.objects.get(documento=pendencia.documento, investidor=investidor).delete()
    except InvestidorValidacaoDocumento.DoesNotExist:
        pass
    
def salvar_investidor_responsavel_por_recusar_documento(pendencia, investidor, motivo):
    """
    Cria vínculo de responsabilidade pela recusa de documento para o investidor
    Parâmetros: Pendência
                Investidor
    Retorno: Vínculo de responsabilidade pela recusa
    """
    if pendencia.tipo != 'V':
        raise ValueError(u'Pendência deve ser do tipo "Validação"')
    
    # Verificar se o vínculo pode ser criado
    responsavel_recusa = InvestidorRecusaDocumento(documento=pendencia.documento, investidor=investidor, motivo=motivo, \
                                                   responsavel_leitura=pendencia.documento.responsavel_leitura())
    responsavel_recusa.full_clean()
    
    # Pendência volta a ser de leitura
    pendencia.tipo = 'L'
    pendencia.save()
    
    # Desaloca pendência para o validador
    retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, investidor)
    if not retorno:
        raise ValueError(mensagem)
    # Realoca pendência para o leitor
    retorno, mensagem = alocar_pendencia_para_investidor(PendenciaDocumentoProvento.objects.get(id=pendencia.id), \
                                                         InvestidorLeituraDocumento.objects.get(documento=pendencia.documento).investidor)
    if not retorno:
        raise ValueError(mensagem)
    
    # Remove responsável por leitura
    InvestidorLeituraDocumento.objects.get(documento=pendencia.documento).delete()
    
    # Salvar responsavel pela recusa
    responsavel_recusa.save()
    return responsavel_recusa

def converter_descricao_provento_para_provento_acoes(descricao_provento):
    """
    Cria um provento a partir de uma descrição de provento, para ações
    Parâmetros: Descrição de provento (ações)
    Retorno:    Tupla com provento e ações recebidas, ex.: (Provento de dividendos, ), (Provento de ações, [ações recebidas])
    """
    if not isinstance(descricao_provento, ProventoAcaoDescritoDocumentoBovespa):
        raise ValueError(u'Objeto não é uma descrição de provento para ações')
    
    # Se dividendo ou JSCP, converter diretamente
    if descricao_provento.tipo_provento in ['D', 'J']:
        novo_provento = Provento(acao=descricao_provento.acao, tipo_provento=descricao_provento.tipo_provento, data_ex=descricao_provento.data_ex, data_pagamento=descricao_provento.data_pagamento,
                        valor_unitario=descricao_provento.valor_unitario)
        novo_provento.full_clean()
        
        # Criar atualização pela Selic caso exista
        if hasattr(descricao_provento, 'selicproventoacaodescritodocbovespa'):
            novo_provento.atualizacaoselicprovento = AtualizacaoSelicProvento(data_inicio=descricao_provento.selicproventoacaodescritodocbovespa.data_inicio,
                                                                              data_fim=descricao_provento.selicproventoacaodescritodocbovespa.data_fim, provento=novo_provento)
        
        return (novo_provento, list())
    # Para dividendo em ações, copiar também a descrição de recebimento de ações
    else:
        novo_provento = Provento(acao=descricao_provento.acao, tipo_provento=descricao_provento.tipo_provento, data_ex=descricao_provento.data_ex, data_pagamento=descricao_provento.data_pagamento,
                        valor_unitario=descricao_provento.valor_unitario)
        novo_provento.full_clean()
        lista_acoes = list()
        for acao_provento in AcaoProventoAcaoDescritoDocumentoBovespa.objects.filter(provento=descricao_provento):
            nova_acao_provento = AcaoProvento(provento=novo_provento, data_pagamento_frac=acao_provento.data_pagamento_frac, valor_calculo_frac=acao_provento.valor_calculo_frac,
                                            acao_recebida=acao_provento.acao_recebida)
            nova_acao_provento.full_clean(exclude=('provento',))
            lista_acoes.append(nova_acao_provento)
        return (novo_provento, lista_acoes)
    
def converter_descricao_provento_para_provento_fiis(descricao_provento):
    """
    Cria um provento a partir de uma descrição de provento, para FIIs
    Parâmetros: Descrição de provento (FIIs)
    Retorno:    Provento
    """
    if not isinstance(descricao_provento, ProventoFIIDescritoDocumentoBovespa):
        raise ValueError(u'Objeto não é uma descrição de provento para FIIS')
    
    novo_provento = ProventoFII(fii=descricao_provento.fii, tipo_provento=descricao_provento.tipo_provento, data_ex=descricao_provento.data_ex, data_pagamento=descricao_provento.data_pagamento,
                    valor_unitario=descricao_provento.valor_unitario)
    novo_provento.full_clean()
    
    return novo_provento

def versionar_descricoes_relacionadas_acoes(descricao, provento_relacionado):
    """
    Versiona descrições de proventos de ações relacionados
    Parâmetros: Descrição a entrar para as versões
                Provento relacionado
    """
    # Buscar todas as versões do provento descrito
    versoes_provento = list(ProventoAcaoDocumento.objects.filter(provento=provento_relacionado))
    # Adicionar descricao à lista de versões pelo número do protocolo do documento
    versoes_provento.append(descricao.proventoacaodocumento)
    versoes_provento.sort(key=lambda x: x.documento.protocolo)
    # Gerar versões a partir de 1 na ordem feita
    for versao, item in enumerate(versoes_provento, start=1):
        item.versao = versao
        item.save()
    # Se versão adicionada for a ultima, o provento apontado deve ser copia do novo_provento
    if descricao.proventoacaodocumento.versao == len(versoes_provento):
        copiar_proventos_acoes(provento_relacionado, descricao.proventoacaodocumento.provento)
    # Guardar provento anterior para apagar posteriormente
    provento_anterior = Provento.gerador_objects.get(id=descricao.proventoacaodocumento.provento.id)
    
    descricao.proventoacaodocumento.provento = provento_relacionado
    descricao.proventoacaodocumento.save()
    
    # Apagar provento anterior
    for acao_provento_anterior in AcaoProvento.objects.filter(provento__id=provento_anterior.id):
        acao_provento_anterior.delete()
    if hasattr(provento_anterior, 'atualizacaoselicprovento'):
        provento_anterior.atualizacaoselicprovento.delete()
    provento_anterior.delete()
    
def reverter_provento_acao_para_versao_anterior(provento):
    """
    Reverte um provento de ações para sua versão anterior
    Parâmetros: Provento
    """
    versao_anterior = ProventoAcaoDocumento.objects.filter(provento=provento).order_by('-versao')[1]
    
    # Guardar atualização Selic atual
    if hasattr(provento, 'atualizacaoselicprovento'):
        atualizacao_selic = provento.atualizacaoselicprovento
    else:
        atualizacao_selic = None
    
    # Copiar dados da versão anterior para provento
    guarda_id_provento = provento.id
    provento, acoes_prov_versao_ant = converter_descricao_provento_para_provento_acoes(versao_anterior.descricao_provento)
    provento.id = guarda_id_provento
    # Se provento estava versionado, é oficial
    provento.oficial_bovespa = True
    provento.save()
    
    # Verificar Selic
    if hasattr(versao_anterior.descricao_provento, 'selicproventoacaodescritodocbovespa'):
        # Se versão anterior possui atualização, alterar guarda da Selic atual
        if atualizacao_selic != None:
            guarda_id_selic = atualizacao_selic.id
        else:
            guarda_id_selic = None
        atualizacao_selic = provento.atualizacaoselicprovento
        if guarda_id_selic != None:
            atualizacao_selic.id = guarda_id_selic
        atualizacao_selic.provento = provento
        atualizacao_selic.save()
    elif atualizacao_selic != None:
        # Se não possui, apagar caso guarda não seja nula
        atualizacao_selic.delete()
    
    acoes_recebidas_atuais = list(AcaoProvento.objects.filter(provento__id=provento.id))
    qtd_acoes_atuais = len(acoes_recebidas_atuais)
    if len(acoes_prov_versao_ant) == qtd_acoes_atuais:
        # Quantidade de ações iguais a versão anterior, sobrescrever um a um
        for indice, acao in enumerate(acoes_recebidas_atuais):
            guarda_id_acao = acao.id
            acao = acoes_prov_versao_ant[indice]
            acao.id = guarda_id_acao
            acao.provento = provento
            acao.save()
    elif len(acoes_prov_versao_ant) > qtd_acoes_atuais:
        # Quantidade de ações menor que a versão anterior, sobrescrever as que existirem, e então criar novas
        for indice, acao in enumerate(acoes_recebidas_atuais):
            guarda_id_acao = acao.id
            acao = acoes_prov_versao_ant[indice]
            acao.id = guarda_id_acao
            acao.provento = provento
            acao.save()
        # Continuar a partir do próx. valor de índice, ou 0 se não foi feita iteração
        indice = 0 if qtd_acoes_atuais == 0 else len(qtd_acoes_atuais)
        while indice < len(acoes_prov_versao_ant):
            acao = acoes_prov_versao_ant[indice]
            acao.provento = provento
            acao.save()
            indice += 1
        
    elif len(acoes_prov_versao_ant) < qtd_acoes_atuais:
        # Quantidade de ações maior que a versão anterior, sobrescrever com a versão anterior e apagar excedentes
        for indice, acao in enumerate(acoes_recebidas_atuais):
            if indice < len(acoes_prov_versao_ant):
                guarda_id_acao = acao.id
                acao = acoes_prov_versao_ant[indice]
                acao.id = guarda_id_acao
                acao.provento = provento
                acao.save()
            else:
                acao.delete()
            
def versionar_descricoes_relacionadas_fiis(descricao, provento_relacionado):
    """
    Versiona descrições de proventos de FIIs relacionados
    Parâmetros: Descrição a entrar para as versões
                Provento relacionado
    """
    # Buscar todas as versões do provento descrito
    versoes_provento = list(ProventoFIIDocumento.objects.filter(provento=provento_relacionado))
    # Adicionar descricao à lista de versões pelo número do protocolo do documento
    versoes_provento.append(descricao.proventofiidocumento)
    versoes_provento.sort(key=lambda x: x.documento.protocolo)
    # Gerar versões a partir de 1 na ordem feita
    for versao, item in enumerate(versoes_provento, start=1):
        item.versao = versao
        item.save()
    # Se versão adicionada for a ultima, o provento apontado deve ser copia do novo_provento
    if descricao.proventofiidocumento.versao == len(versoes_provento):
        copiar_proventos_fiis(provento_relacionado, descricao.proventofiidocumento.provento)
    # Guardar provento anterior para apagar posteriormente
    provento_anterior = ProventoFII.gerador_objects.get(id=descricao.proventofiidocumento.provento.id)
    
    descricao.proventofiidocumento.provento = provento_relacionado
    descricao.proventofiidocumento.save()
    
    # Apagar provento anterior
    provento_anterior.delete()
    
def reverter_provento_fii_para_versao_anterior(provento):
    """
    Reverte um provento de FIIS para sua versão anterior
    Parâmetros: Provento
    """
    versao_anterior = ProventoFIIDocumento.objects.filter(provento=provento).order_by('-versao')[1]
    # Copiar dados da versão anterior para provento
    guarda_id = provento.id
    provento = converter_descricao_provento_para_provento_fiis(versao_anterior.descricao_provento)
    provento.id = guarda_id
    # Se provento estava versionado, é oficial
    provento.oficial_bovespa = True
    provento.save()

def reiniciar_documento(documento):
    """
    Reinicia um documento, removendo responsáveis, voltando pendência para leitura e alterando proventos e suas descrições
    Parâmetros: Documento
    """
    try:
        with transaction.atomic():
            InvestidorValidacaoDocumento.objects.filter(documento=documento).delete()
            InvestidorLeituraDocumento.objects.filter(documento=documento).delete()
            InvestidorResponsavelPendencia.objects.filter(pendencia__documento=documento).delete()
            InvestidorRecusaDocumento.objects.filter(documento=documento).delete()
            
            # Reverter proventos criados
            if documento.tipo == 'A':
                for documento_provento in ProventoAcaoDocumento.objects.filter(documento=documento):
                    if documento_provento.versao == ProventoAcaoDocumento.objects.filter(provento=documento_provento.provento).order_by('-versao')[0].versao:
                        # Se for a versão 1, apagar provento
                        if documento_provento.versao == 1:
                            documento_provento.provento.delete()
                        else:
                            reverter_provento_acao_para_versao_anterior(documento_provento.provento)
                        documento_provento.descricao_provento.delete()
                        documento_provento.delete()
                    else:
                        # Se não é a última, apagar e atualizar versões posteriores
                        versao = documento_provento.versao
                        documento_provento.descricao_provento.delete()
                        documento_provento.delete()
                        
                        # Atualizar versões posteriores
                        for doc_prov_versao_posterior in ProventoAcaoDocumento.objects.filter(provento=documento_provento.provento, versao__gt=versao).order_by('versao'):
                            doc_prov_versao_posterior.versao -= 1
                            doc_prov_versao_posterior.save()
                            
            elif documento.tipo == 'F':
                for documento_provento in ProventoFIIDocumento.objects.filter(documento=documento):
                    if documento_provento.versao == ProventoFIIDocumento.objects.filter(provento=documento_provento.provento).order_by('-versao')[0].versao:
                        # Se for a versão 1, apagar provento
                        if documento_provento.versao == 1:
                            documento_provento.provento.delete()
                        else:
                            reverter_provento_fii_para_versao_anterior(documento_provento.provento)
                        documento_provento.descricao_provento.delete()
                        documento_provento.delete()
                    else:
                        # Se não é a última, apagar e atualizar versões posteriores
                        versao = documento_provento.versao
                        provento = documento_provento.provento
                        documento_provento.descricao_provento.delete()
                        documento_provento.delete()
                        
                        # Atualizar versões posteriores
                        for doc_prov_versao_posterior in ProventoFIIDocumento.objects.filter(provento=provento, versao__gt=versao).order_by('versao'):
                            doc_prov_versao_posterior.versao -= 1
                            doc_prov_versao_posterior.save()
            
            # Baixar documento se tiver sido apagado
            if not documento.documento:
                documento.baixar_e_salvar_documento()
            
            # Recriar ou atualizar pendência de leitura
            pendencia, criada = PendenciaDocumentoProvento.objects.get_or_create(documento=documento, defaults={'tipo': PendenciaDocumentoProvento.TIPO_LEITURA})
            if not criada:
                pendencia.tipo = PendenciaDocumentoProvento.TIPO_LEITURA
                pendencia.save()
    except:
        raise
            

def copiar_proventos_acoes(provento, provento_a_copiar):
    """
    Copia dados de um provento de ações para outro
    Parâmetros: Provento a receber dados
                Provento a ser copiado
    """
    with transaction.atomic():
        # Se provento a copiar for do tipo provento em ações, copiar ações recebidas
        if provento_a_copiar.tipo_provento == 'A':
            acoes_provento = AcaoProvento.objects.filter(provento__id=provento.id)
            indice_acao_provento = 0
            for acao_provento_a_copiar in AcaoProvento.objects.filter(provento__id=provento_a_copiar.id):
                if indice_acao_provento < len(acoes_provento):
                    # Copiar ação recebida do provento
                    acoes_provento[indice_acao_provento].acao_recebida = acao_provento_a_copiar.acao_recebida
                    acoes_provento[indice_acao_provento].data_pagamento_frac = acao_provento_a_copiar.data_pagamento_frac
                    acoes_provento[indice_acao_provento].valor_calculo_frac = acao_provento_a_copiar.valor_calculo_frac
                    acoes_provento[indice_acao_provento].save()
                else:
                    # Criar nova ação recebida do provento
                    nova_acao_provento = AcaoProvento(acao_recebida=acao_provento_a_copiar.acao_recebida, \
                                                      data_pagamento_frac=acao_provento_a_copiar.data_pagamento_frac, \
                                                      valor_calculo_frac=acao_provento_a_copiar.valor_calculo_frac, provento=provento)
                    nova_acao_provento.save()
                # Passar à próxima ação recebida
                indice_acao_provento += 1
            
            # Caso provento a receber dados seja atualizado pela Selic, apagar atualização
            if hasattr(provento, 'atualizacaoselicprovento'):
                provento.atualizacaoselicprovento.delete()
            
        # Se provento a copiar possuir atualização pela Selic, passar para provento a receber dados
        elif hasattr(provento_a_copiar, 'atualizacaoselicprovento'):
            if hasattr(provento, 'atualizacaoselicprovento'):
                provento.atualizacaoselicprovento.data_inicio = provento_a_copiar.atualizacaoselicprovento.data_inicio
                provento.atualizacaoselicprovento.data_fim = provento_a_copiar.atualizacaoselicprovento.data_fim
                provento.atualizacaoselicprovento.save()
            else:
                AtualizacaoSelicProvento.objects.create(provento=provento, data_inicio=provento_a_copiar.atualizacaoselicprovento.data_inicio,
                                                        data_fim=provento_a_copiar.atualizacaoselicprovento.data_fim)
            
            # Caso provento a receber dados possua ações a receber, apagá-las
            for acao_provento in AcaoProvento.objects.filter(provento__id=provento.id):
                acao_provento.delete()
            
        else:
            # Se provento a copiar não for do tipo provento em ações, mas o provento a receber a cópia for, apagar ações recebidas
            if provento.tipo_provento == 'A':
                for acao_provento in AcaoProvento.objects.filter(provento__id=provento.id):
                    acao_provento.delete()
            elif hasattr(provento, 'atualizacaoselicprovento'):
                provento.atualizacaoselicprovento.delete()
                
        provento.acao = provento_a_copiar.acao
        provento.valor_unitario = provento_a_copiar.valor_unitario
        provento.tipo_provento = provento_a_copiar.tipo_provento
        provento.data_ex = provento_a_copiar.data_ex
        provento.data_pagamento = provento_a_copiar.data_pagamento
        provento.observacao = provento_a_copiar.observacao
        provento.save()
        
def copiar_proventos_fiis(provento, provento_a_copiar):
    """
    Copia dados de um provento de FIIs para outro
    Parâmetros: Provento a receber dados
                Provento a ser copiado
    """
    provento.fii = provento_a_copiar.fii
    provento.valor_unitario = provento_a_copiar.valor_unitario
    provento.tipo_provento = provento_a_copiar.tipo_provento
    provento.data_ex = provento_a_copiar.data_ex
    provento.data_pagamento = provento_a_copiar.data_pagamento
    provento.save()
    

def criar_descricoes_provento_acoes(descricoes_proventos, acoes_descricoes_proventos, selic_descricoes_proventos, documento):
    """
    Cria descrições para proventos de ações a partir de um documento
    Parâmetros: Lista de proventos
                Lista de ações recebidas em proventos
                Lista de atualizações pela Selic para proventos
                Documento que traz os proventos
    """
    try:
        with transaction.atomic():
            for descricao_provento in descricoes_proventos:
                descricao_provento.save()
                
                # Proventos em ações
                descricoes_acao_provento = [acao_descricao_provento for acao_descricao_provento in acoes_descricoes_proventos if acao_descricao_provento.provento.id == descricao_provento.id]
                for descricao_acao_provento in descricoes_acao_provento:
                    descricao_acao_provento.provento = descricao_provento
                    descricao_acao_provento.save()
                
                # Proventos atualizados pela Selic
                descricoes_selic_provento = [selic_descricao_provento for selic_descricao_provento in selic_descricoes_proventos if selic_descricao_provento.provento.id == descricao_provento.id]
                for descricao_selic_provento in descricoes_selic_provento:
                    descricao_selic_provento.provento = descricao_provento
                    descricao_selic_provento.save()
                    
                # Se provento possuir as 2 listas, jogar erro
                if descricoes_acao_provento and descricoes_selic_provento:
                    raise ValueError(u'Proventos em ações não podem ser atualizados pela Selic')
                
                # Converte para proventos reais, porém não validados
                provento, acoes_provento = converter_descricao_provento_para_provento_acoes(descricao_provento)
                # Busca proventos já existentes, ou cria se não existirem
                if Provento.gerador_objects.filter(valor_unitario=provento.valor_unitario, acao=provento.acao, data_ex=provento.data_ex, data_pagamento=provento.data_pagamento, \
                                                   tipo_provento=provento.tipo_provento, oficial_bovespa=False).exists():
                    provento = Provento.gerador_objects.get(valor_unitario=provento.valor_unitario, acao=provento.acao, data_ex=provento.data_ex, data_pagamento=provento.data_pagamento, \
                                                   tipo_provento=provento.tipo_provento, oficial_bovespa=False)
                    
                    # Caso seja um provento de ações, verifica se as ações recebidas batem
                    if provento.tipo_provento == 'A':
                        if len(provento.acaoprovento_set) != len(descricoes_acao_provento):
                            raise ValueError('Há um provento não oficial cadastrado com dados de ações incompatíveis')
                        for acao_provento in provento.acaoprovento_set:
                            provento_corresponde = False
                            for descricao_acao_provento in descricoes_acao_provento:
                                if descricao_acao_provento.acao_recebida == acao_provento.acao_recebida \
                                and descricao_acao_provento.data_pagamento_frac == acao_provento.data_pagamento_frac \
                                and descricao_acao_provento.valor_calculo_frac == acao_provento.valor_calculo_frac:
                                    provento_corresponde = True
                                    break
                            if not provento_corresponde:
                                raise ValueError('Há um provento não oficial cadastrado com dados de ações incompatíveis')
                    # Caso contrário, verifica se atualização pela Selic condiz com que há cadastrado
                    else:
                        if hasattr(provento, 'atualizacaoselicprovento') and hasattr(descricao_provento, 'selicproventoacaodescritodocbovespa'):
                            if provento.atualizacaoselicprovento.data_inicio != descricao_provento.selicproventoacaodescritodocbovespa.data_inicio:
                                raise ValueError('Há um provento não oficial cadastrado com dados de atualização pela Selic incompatíveis')
                            if provento.atualizacaoselicprovento.data_fim != descricao_provento.selicproventoacaodescritodocbovespa.data_fim:
                                raise ValueError('Há um provento não oficial cadastrado com dados de atualização pela Selic incompatíveis')
                                
                else:
                    provento.save()
                    # Criar ações recebidas
                    for acao_provento in acoes_provento:
                        acao_provento.provento = provento
                        acao_provento.save()
                    # Criar atualização pela Selic
                    if hasattr(provento, 'atualizacaoselicprovento'):
                        atualizacao = provento.atualizacaoselicprovento
                        atualizacao.provento = provento
                        atualizacao.save()
                        
                # Relaciona a descrição ao provento encontrado/criado
                provento_documento = ProventoAcaoDocumento.objects.create(provento=provento, documento=documento, descricao_provento=descricao_provento, versao=1)
    except:
        raise
    
def criar_descricoes_provento_fiis(descricoes_proventos, documento):
    """
    Cria descrições para proventos de FIIs a partir de um documento
    Parâmetros: Lista de proventos
                Documento que traz os proventos
    """
    try:
        with transaction.atomic():
            for descricao_provento in descricoes_proventos:
                descricao_provento.save()
                # Converte para proventos reais, porém não validados
                provento = converter_descricao_provento_para_provento_fiis(descricao_provento)
                # Busca proventos já existentes, ou cria se não existirem
                if ProventoFII.gerador_objects.filter(valor_unitario=provento.valor_unitario, fii=provento.fii, data_ex=provento.data_ex, data_pagamento=provento.data_pagamento, \
                                                      tipo_provento=provento.tipo_provento, oficial_bovespa=False).exists():
                    provento = ProventoFII.gerador_objects.get(valor_unitario=provento.valor_unitario, fii=provento.fii, data_ex=provento.data_ex, data_pagamento=provento.data_pagamento, \
                                                   tipo_provento=provento.tipo_provento, oficial_bovespa=False)
                else:
                    provento.save()
                # Relaciona a descrição ao provento encontrado/criado
                provento_documento = ProventoFIIDocumento.objects.create(provento=provento, documento=documento, descricao_provento=descricao_provento, versao=1)
    except:
        raise
    
def buscar_proventos_proximos_acao(descricao_provento):
    """
    Retorna lista com os proventos próximas à data EX de uma descrição de provento de ação
    Parâmetros: Descrição de provento de ação
    Retorno:    Lista de proventos ordenada por quantidade de dias em relação à data EX
    """
    range_ant = [descricao_provento.data_ex - datetime.timedelta(days=365), descricao_provento.data_ex]
    proventos_proximos_ant = Provento.objects.filter(acao=descricao_provento.acao, data_ex__range=range_ant) \
        .exclude(id=descricao_provento.proventoacaodocumento.provento.id).order_by('-data_ex')[:5]
        
    range_post = [descricao_provento.data_ex + datetime.timedelta(days=1), descricao_provento.data_ex + datetime.timedelta(days=365)]
    proventos_proximos_post = Provento.objects.filter(acao=descricao_provento.acao, data_ex__range=range_post) \
        .exclude(id=descricao_provento.proventoacaodocumento.provento.id).order_by('data_ex')[:5]
    
    # Ordenar pela diferença com a data da descrição de provento
    return sorted(chain(proventos_proximos_ant, proventos_proximos_post),
                    key= lambda x: abs((x.data_ex - descricao_provento.data_ex).days))
    
def buscar_proventos_proximos_fii(descricao_provento):
    """
    Retorna lista com os proventos próximas à data EX de uma descrição de provento de FII
    Parâmetros: Descrição de provento de FII
    Retorno:    Lista de proventos ordenada por quantidade de dias em relação à data EX
    """
    range_ant = [descricao_provento.data_ex - datetime.timedelta(days=365), descricao_provento.data_ex]
    proventos_proximos_ant = ProventoFII.objects.filter(fii=descricao_provento.fii, data_ex__range=range_ant) \
        .exclude(id=descricao_provento.proventofiidocumento.provento.id).order_by('-data_ex')[:5]
        
    range_post = [descricao_provento.data_ex + datetime.timedelta(days=1), descricao_provento.data_ex + datetime.timedelta(days=365)]
    proventos_proximos_post = ProventoFII.objects.filter(fii=descricao_provento.fii, data_ex__range=range_post) \
        .exclude(id=descricao_provento.proventofiidocumento.provento.id).order_by('data_ex')[:5]
    
    # Ordenar pela diferença com a data da descrição de provento
    return sorted(chain(proventos_proximos_ant, proventos_proximos_post),
                    key= lambda x: abs((x.data_ex - descricao_provento.data_ex).days))
    
def ler_provento_estruturado_fii(documento_fii):
    """
    Lê XML estruturado da Bovespa para gerar descrição de provento de FII
    Parâmetros: Documento de FII
    """
    if documento_fii.tipo != 'F':
        raise ValueError('Documento deve ser de um FII')
    if documento_fii.tipo_documento != DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO:
        raise ValueError('Documento deve ser do %s' % (DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO))
    
    # Documento deve estar pendente de leitura
    if not PendenciaDocumentoProvento.objects.filter(documento=documento_fii).exists():
        raise ValueError('Documento deve estar pendente de leitura')
    
    documento_fii.documento.open()
    try:
        with transaction.atomic():
            tree = etree.parse(documento_fii.documento)
            # Pega o último (maior ID) FII que contenha o código de negociação em seu ticker
            fii = FII.objects.filter(ticker__icontains=list(tree.getroot().iter('CodNegociacaoCota'))[0].text.strip()).order_by('-id')[0]
            
            # Verificar se FII tem empresa igual a do documento
            if fii not in documento_fii.empresa.fii_set.all():
                raise ValueError('Documento cita FII de outra empresa')
            
            for element in tree.getroot().iter('Rendimento', 'Amortizacao'):
                descricao_provento = ProventoFIIDescritoDocumentoBovespa()
                # Se há pelo menos 5 campos, o provento pode ser prenchido
                if len(list(element.iter())) >= 5:
                    if element.tag == 'Rendimento':
                        descricao_provento.tipo_provento = 'R'
                    else:
                        descricao_provento.tipo_provento = 'A'
                    descricao_provento.fii = fii
                    for dado in element.iter():
                        if dado.tag == 'DataBase':
                            descricao_provento.data_ex = datetime.datetime.strptime(dado.text.strip(), '%Y-%m-%d')
                        if dado.tag == 'DataPagamento':
                            descricao_provento.data_pagamento = datetime.datetime.strptime(dado.text.strip(), '%Y-%m-%d')
                        if dado.tag == 'ValorProventoCota':
                            descricao_provento.valor_unitario = Decimal(dado.text.strip())
                    descricao_provento.save()
                    provento, criado = ProventoFII.gerador_objects.get_or_create(valor_unitario=descricao_provento.valor_unitario, fii=descricao_provento.fii, \
                                                                      data_ex=descricao_provento.data_ex, data_pagamento=descricao_provento.data_pagamento, \
                                                                      tipo_provento=descricao_provento.tipo_provento)
                    
                    # Verifica se provento foi criado
                    if criado:
                        # Se sim, cria como primeira versão
                        ProventoFIIDocumento.objects.create(documento=documento_fii, provento=provento, versao=1, descricao_provento=descricao_provento)
                    else:
                        # Se não, versionar
                        ProventoFIIDocumento.objects.create(documento=documento_fii, provento=provento, versao=0, descricao_provento=descricao_provento)
                        
                        # Buscar todas as versões do provento descrito
                        versoes_provento = list(ProventoFIIDocumento.objects.filter(provento=provento))
                        versoes_provento.sort(key=lambda x: x.documento.protocolo)
                        # Gerar versões a partir de 1 na ordem feita
                        for versao, item in enumerate(versoes_provento, start=1):
                            item.versao = versao
                            item.save()
                        
                    if not provento.oficial_bovespa:
                        provento.oficial_bovespa = True
                        provento.save()
                        
            # Apagar pendência
            for pendencia_provento in PendenciaDocumentoProvento.objects.filter(documento=documento_fii):
                pendencia_provento.delete()
                
            # Apagar outros documentos com mesmo protocolo
            for doc_mesmo_protocolo in DocumentoProventoBovespa.objects.filter(tipo='F', protocolo=documento_fii.protocolo).exclude(id=documento_fii.id):
                # Verificar se não possuem leitura, validacao ou recusas
                if not InvestidorRecusaDocumento.objects.filter(documento=doc_mesmo_protocolo).exists() and not InvestidorLeituraDocumento.objects.filter(documento=doc_mesmo_protocolo).exists() \
                    and not InvestidorValidacaoDocumento.objects.filter(documento=doc_mesmo_protocolo).exists():
                    reiniciar_documento(doc_mesmo_protocolo)
                    doc_mesmo_protocolo.delete()
    except:
        # Fechar documento e jogar erro
        documento_fii.documento.close()
        raise
    
    # Fechar arquivo
    documento_fii.documento.close()
            
def relacionar_proventos_lidos_sistema(provento_relacionar, provento_relacionado):
    """
    Relaciona proventos lidos pelo sistema
    Parâmetros: Provento a relacionar
                Provento a ser relacionado
    """
    # Verificar se proventos foram lidos pelo sistema
    if not (provento_relacionar.add_pelo_sistema and provento_relacionado.add_pelo_sistema):
        raise ValueError('Proventos devem ter sido adicionados pelo sistema')
    elif provento_relacionar.id == provento_relacionado.id:
        raise ValueError('Provento a relacionar é igual a provento relacionado')
    
    try:
        with transaction.atomic():
            # Buscar todas as versões do provento descrito
            versoes_provento_relacionado = list(ProventoFIIDocumento.objects.filter(provento=provento_relacionado))
            # Adicionar versões do provento a relacionar à lista de versões pelo número do protocolo do documento
            versoes_provento_relacionado.extend(provento_relacionar.proventofiidocumento_set.all())
            versoes_provento_relacionado.sort(key=lambda x: x.documento.protocolo)
            # Gerar versões a partir de 1 na ordem feita
            for versao, item in enumerate(versoes_provento_relacionado, start=1):
                item.versao = versao
                item.save()
            
            # Transformar provento em não oficial para depois oficializá-lo
            provento_relacionado.oficial_bovespa = False
            # Copiar última versão de descrição para o provento relacionado
            copiar_proventos_fiis(provento_relacionado, versoes_provento_relacionado[-1].provento)
            
            for provento_documento in provento_relacionar.proventofiidocumento_set.all():
                provento_documento.provento = provento_relacionado
                provento_documento.save()
            
            provento_relacionar.delete()
            
            # Oficializar
            provento_relacionado.oficial_bovespa = True
            provento_relacionado.save()
    except Exception as e:
        raise ValueError('Houve um erro ao relacionar os documentos - %s' % e)
