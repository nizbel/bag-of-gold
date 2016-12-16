# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Provento, AcaoProvento
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    PendenciaDocumentoProvento, ProventoAcaoDocumento, \
    ProventoAcaoDescritoDocumentoBovespa, AcaoProventoAcaoDescritoDocumentoBovespa
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
        raise ValueError('Pendência deve ser do tipo "Leitura"')
    # TODO testar permissão do investidor
    if decisao not in ['C', 'E']:
        raise ValueError('Decisão sobre o documento inválida')
    
    retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, investidor)
    # Desaloca pendência
    if not retorno:
        raise ValueError(mensagem)
    
    responsavel_leitura = InvestidorLeituraDocumento.objects.create(documento=pendencia.documento, investidor=investidor, decisao=decisao)
    # Alterar pendência para validação
    pendencia.tipo = 'V'
    pendencia.save()
    return responsavel_leitura

def retornar_investidor_responsavel_por_leitura(pendencia, investidor):
    """
    Desfaz vínculo de responsabilidade pela leitura, retorna pendência para leitura, realoca pendência para investidor
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

def converter_descricao_provento_para_provento_acoes(descricao_provento):
    """
    Cria um provento a partir de uma descrição de provento, para ações
    Parâmetros: Descrição de provento (ações)
    Retorno:    Tupla com provento e ações recebidas, ex.: (Provento de dividendos, ), (Provento de ações, [ações recebidas])
    """
    if not isinstance(descricao_provento, ProventoAcaoDescritoDocumentoBovespa):
        raise ValueError('Objeto não é uma descrição de provento para ações')
    
    # Se dividendo ou JSCP, converter diretamente
    if descricao_provento.tipo_provento in ['D', 'J']:
        return (Provento(acao=descricao_provento.acao, tipo_provento=descricao_provento.tipo_provento, data_ex=descricao_provento.data_ex, data_pagamento=descricao_provento.data_pagamento,
                        valor_unitario=descricao_provento.valor_unitario), list())
    # Para dividendo em ações, copiar também a descrição de recebimento de ações
    else:
        provento = Provento(acao=descricao_provento.acao, tipo_provento=descricao_provento.tipo_provento, data_ex=descricao_provento.data_ex, data_pagamento=descricao_provento.data_pagamento,
                        valor_unitario=descricao_provento.valor_unitario)
        lista_acoes = list()
        for acao_provento in AcaoProventoAcaoDescritoDocumentoBovespa.objects.filter(provento=descricao_provento):
            lista_acoes.append(AcaoProvento(provento=provento, data_pagamento_frac=acao_provento.data_pagamento_frac, valor_calculo_frac=acao_provento.valor_calculo_frac,
                                            acao_recebida=acao_provento.acao_recebida))
        return (provento, lista_acoes)
    
def versionar_descricoes_relacionadas_acoes(descricao, descricao_relacionada):
    """
    Versiona descrições de proventos em ações relacionadas
    """
    # Buscar todas as versões do provento descrito
    
    # Adicionar descricao à lista de versões pelo número do protocolo do documento
    
    # Gerar versões a partir de 1 na ordem feita
            

def converter_descricao_provento_para_provento_fii(descricao_provento):
    pass

def criar_descricoes_provento_acoes(descricoes_proventos, acoes_descricoes_proventos, documento):
    """
    Cria descrições para proventos em ações a partir de um documento
    Parâmetros: Lista de proventos
                Lista de ações recebidas em proventos
                Documento
    """
    objetos_salvos = list()
    try:
        for descricao_provento in descricoes_proventos:
            descricao_provento.save()
            objetos_salvos.append(descricao_provento)
            provento_documento = ProventoAcaoDocumento.objects.create(documento=documento, descricao_provento=descricao_provento, versao=1)
            objetos_salvos.append(provento_documento)
        for descricao_acao_provento in acoes_descricoes_proventos:
            descricao_acao_provento.provento = ProventoAcaoDescritoDocumentoBovespa.objects.get(id=descricao_acao_provento.provento.id)
            descricao_acao_provento.save()
            objetos_salvos.append(descricao_acao_provento)
    except Exception as e:
        # Apaga objetos em caso de erro
        for objeto in objetos_salvos:
            objeto.delete()
        raise e

def buscar_proventos_e_descricoes_proximos_acao(descricao_provento):
    """
    Retorna lista com os proventos e descrições de proventos próximas à data EX de uma descrição de provento
    Parâmetros: Descrição de provento de ação
    Retorno:    Lista de proventos e descrições de proventos ordenada por quantidade de dias em relação à data EX
    """
    # Proventos
    proventos_proximos_ant = Provento.objects.filter(acao=descricao_provento.acao, data_ex__lte=descricao_provento.data_ex).order_by('-data_ex')[:5]
    proventos_proximos_post = Provento.objects.filter(acao=descricao_provento.acao, data_ex__gt=descricao_provento.data_ex).order_by('data_ex')[:5]
    # Descrições de proventos
    desc_proventos_proximos_ant = ProventoAcaoDescritoDocumentoBovespa.objects.filter(acao=descricao_provento.acao, data_ex__lte=descricao_provento.data_ex).exclude(id=descricao_provento.id).order_by('-data_ex')[:5]
    desc_proventos_proximos_post = ProventoAcaoDescritoDocumentoBovespa.objects.filter(acao=descricao_provento.acao, data_ex__gt=descricao_provento.data_ex).order_by('data_ex')[:5]
    
    # Ordenar pela diferença com a data da descrição de provento
    return sorted(chain(proventos_proximos_ant, proventos_proximos_post, desc_proventos_proximos_ant, desc_proventos_proximos_post),
                    key= lambda x: abs((x.data_ex - descricao_provento.data_ex).days))[:10]