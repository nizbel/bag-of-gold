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