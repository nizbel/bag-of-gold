# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.cri_cra.models.cri_cra import CRI_CRA, DataRemuneracaoCRI_CRA
import datetime

def calcular_valor_cri_cra_na_data(certificado, data=datetime.date.today()):
    """
    Calcula o valor de um certificado na data apontada
    Parâmetros: Certificado (CRI/CRA)
                Data
    Retorno:    Valor na data
    """
    if data > certificado.data_vencimento:
        raise ValueError('Data posterior à data de vencimento do certificado')
    elif data < certificado.data_emissao:
        raise ValueError('Data anterior à data de emissão do certificado')
        
    if certificado.tipo_indexacao not in CRI_CRA.ESCOLHAS_TIPO_INDEXACAO:
        raise ValueError('Indexador inválido')
    
    # Buscar data inicial, considerando a última data de remuneração antes da data enviada
    if DataRemuneracaoCRI_CRA.objects.filter(cri_cra=certificado, data__lte=data).exists():
        data_inicial = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=certificado, data__lte=data).order_by('-data')[0].data
    else:
        data_inicial = certificado.data_emissao
    
    # TODO incluir amortizações
    valor_inicial = certificado.valor_emissao
    
    if certificado.tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_DI:
        return calcular_valor_cri_cra_di(valor_inicial, percentual_di, data_inicial, data, juros_adicional)
    elif certificado.tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_PREFIXADO:
        pass
        
def calcular_valor_cri_cra_di(valor_inicial, percentual_di, data_inicial, data_final, juros_adicional):
    """
    Calcula o valor de um certificado atualizado pelo DI
    Parâmetros: Valor inicial a ser atualizado
                Percentual do DI
                Data de início da atualização
                Data de fim da atualização
                Juros adicional (percentual ao ano)
    Retorno:    Valor atualizado
    """
    taxas = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_final])
    # TODO Buscar valor atualizado pelo DI com as taxas 
    
    return valor_atualizado