# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Provento, AcaoProvento
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    PendenciaDocumentoProvento, ProventoAcaoDocumento, \
    ProventoAcaoDescritoDocumentoBovespa, AcaoProventoAcaoDescritoDocumentoBovespa, \
    InvestidorValidacaoDocumento, InvestidorRecusaDocumento
from itertools import chain
from operator import attrgetter

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
    
def versionar_descricoes_relacionadas_acoes(descricao, provento_relacionado):
    """
    Versiona descrições de proventos em ações relacionadas
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
        descricao.proventoacaodocumento.provento = provento_relacionado
        descricao.proventoacaodocumento.save()
        
            
def copiar_proventos_acoes(provento, provento_a_copiar):
    """
    Copia dados de um provento em ações para outro
    Parâmetros: Provento a receber dados
                Provento a ser copiado
    """
    dados_provento_a_salvar = list()
    provento.acao = provento_a_copiar.acao
    provento.valor_unitario = provento_a_copiar.valor_unitario
    provento.tipo_provento = provento_a_copiar.tipo_provento
    provento.data_ex = provento_a_copiar.data_ex
    provento.data_pagamento = provento_a_copiar.data_pagamento
    provento.observacao = provento_a_copiar.observacao
    dados_provento_a_salvar.append(provento)
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
                dados_provento_a_salvar.append(acoes_provento[indice_acao_provento])
            else:
                # Criar nova ação recebida do provento
                nova_acao_provento = ProventoAcao(acao_recebida=acao_provento_a_copiar.acao_recebida, \
                                                  data_pagamento_frac=acao_provento_a_copiar.data_pagamento_frac, \
                                                  valor_calculo_frac=acao_provento_a_copiar.valor_calculo_frac, provento=provento)
                dados_provento_a_salvar.append(nova_acao_provento)
            # Passar à próxima ação recebida
            indice_acao_provento += 1
    # Se provento a copiar não for do tipo provento em ações, mas o provento a receber a cópia for, apagar ações recebidas
    elif provento.tipo_provento == 'A':
        for acao_provento in AcaoProvento.objects.filter(provento__id=provento.id):
            acao_provento.delete()
    # Apagar provento a ser copiado
    for acao_provento_a_copiar in AcaoProvento.objects.filter(provento__id=provento_a_copiar.id):
        acao_provento_a_copiar.delete()
    provento_a_copiar.delete()
    # Salvar provento com dados copiados
    for dado in dados_provento_a_salvar:
        dado.save()
    

def converter_descricao_provento_para_provento_fii(descricao_provento):
    pass

def criar_descricoes_provento_acoes(descricoes_proventos, acoes_descricoes_proventos, documento):
    """
    Cria descrições para proventos em ações a partir de um documento
    Parâmetros: Lista de proventos
                Lista de ações recebidas em proventos
                Documento que traz os proventos
    """
    objetos_salvos = list()
    try:
        for descricao_provento in descricoes_proventos:
            descricao_provento.save()
            objetos_salvos.append(descricao_provento)
            descricoes_acao_provento = [acao_descricao_provento for acao_descricao_provento in acoes_descricoes_proventos if acao_descricao_provento.provento.id == descricao_provento.id]
            for descricao_acao_provento in descricoes_acao_provento:
                descricao_acao_provento.provento = descricao_provento
                descricao_acao_provento.save()
                objetos_salvos.append(descricao_acao_provento)
            # Converte para proventos reais, porém não validados
            provento, acoes_provento = converter_descricao_provento_para_provento_acoes(descricao_provento)
            # Busca proventos já existentes, ou cria se não existirem
            try:
                provento = Provento.gerador_objects.get(valor_unitario=provento.valor_unitario, acao=provento.acao, data_ex=provento.data_ex, data_pagamento=provento.data_pagamento, \
                                               tipo_provento=provento.tipo_provento)
                
                # Caso seja um provento de ações, verifica se as ações recebidas batem
                if provento.tipo_provento == 'A':
                    if len(provento.acaoprovento_set) != len(descricoes_acao_provento):
                        raise ValueError('Há um provento não oficial cadastrado com dados incompatíveis')
                    for acao_provento in provento.acaoprovento_set:
                        provento_corresponde = False
                        for descricao_acao_provento in descricoes_acao_provento:
                            if descricao_acao_provento.acao_recebida == acao_provento.acao_recebida \
                            and descricao_acao_provento.data_pagamento_frac == acao_provento.data_pagamento_frac \
                            and descricao_acao_provento.valor_calculo_frac == acao_provento.valor_calculo_frac:
                                provento_corresponde = True
                                break
                        if not provento_corresponde:
                            raise ValueError('Há um provento não oficial cadastrado com dados incompatíveis')
                            
            except Provento.DoesNotExist:
                provento.save()
                objetos_salvos.append(provento)
                for acao_provento in acoes_provento:
                    acao_provento.provento = provento
                    acao_provento.save()
                    objetos_salvos.append(acao_provento)
            # Relaciona a descrição ao provento encontrado/criado
            provento_documento = ProventoAcaoDocumento.objects.create(provento=provento, documento=documento, descricao_provento=descricao_provento, versao=1)
            objetos_salvos.append(provento_documento)
    except Exception as e:
        # Apaga objetos em caso de erro
        for objeto in objetos_salvos:
            objeto.delete()
        raise e

def buscar_proventos_proximos_acao(descricao_provento):
    """
    Retorna lista com os proventos próximas à data EX de uma descrição de provento
    Parâmetros: Descrição de provento de ação
    Retorno:    Lista de proventos ordenada por quantidade de dias em relação à data EX
    """
    proventos_proximos_ant = Provento.objects.filter(acao=descricao_provento.acao, data_ex__lte=descricao_provento.data_ex) \
        .exclude(id=descricao_provento.proventoacaodocumento.provento.id).order_by('-data_ex')[:5]
    proventos_proximos_post = Provento.objects.filter(acao=descricao_provento.acao, data_ex__gt=descricao_provento.data_ex) \
        .exclude(id=descricao_provento.proventoacaodocumento.provento.id).order_by('data_ex')[:5]
    
    # Ordenar pela diferença com a data da descrição de provento
    return sorted(chain(proventos_proximos_ant, proventos_proximos_post),
                    key= lambda x: abs((x.data_ex - descricao_provento.data_ex).days))