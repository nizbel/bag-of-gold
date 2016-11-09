# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    PendenciaDocumentoProvento

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
        pendencia = PendenciaDocumentoProvento.objects.get(id=pendencia.id)
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
    
def converter_descricao_provento_para_provento_acoes_real(descricao_provento):
    pass

def converter_descricao_provento_para_provento_fii_real(descricao_provento):
    pass