# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import InvestidorResponsavelPendencia

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
    
def converter_descricao_provento_para_provento_acoes_real(descricao_provento):
    pass

def converter_descricao_provento_para_provento_fii_real(descricao_provento):
    pass