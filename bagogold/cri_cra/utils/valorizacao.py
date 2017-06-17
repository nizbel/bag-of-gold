# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.cri_cra.models.cri_cra import CRI_CRA, DataRemuneracaoCRI_CRA
from django.db.models.aggregates import Count
from decimal import Decimal
import datetime
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas_di

def calcular_valor_um_cri_cra_na_data(certificado, data=datetime.date.today()):
    """
    Calcula o valor de um certificado na data apontada
    Parâmetros: Certificado (CRI/CRA)
                Data
    Retorno:    Valor na data
    """
    # Data não pode ser posterior a data de vencimento
    if data > certificado.data_vencimento:
        data = certificado.data_vencimento
    elif data < certificado.data_emissao:
        raise ValueError('Data anterior à data de emissão do certificado')
        
    if certificado.tipo_indexacao not in [escolha[0] for escolha in CRI_CRA.ESCOLHAS_TIPO_INDEXACAO]:
        raise ValueError('Indexador inválido')
    
    # Buscar data inicial, considerando a última data de remuneração antes da data enviada
    if DataRemuneracaoCRI_CRA.objects.filter(cri_cra=certificado, data__lte=data).exists():
        data_inicial = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=certificado, data__lte=data).order_by('-data')[0].data
    else:
        data_inicial = certificado.data_inicio_rendimento 
    
    # TODO incluir amortizações
    valor_inicial = certificado.valor_emissao
    
    if certificado.tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_DI:
        return calcular_valor_cri_cra_di(valor_inicial, certificado.porcentagem, data_inicial, data, certificado.juros_adicional)
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
    taxas = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_final]).values('taxa').annotate(qtd_dias=Count('data'))
    taxa_qtd_dias = {}
    for taxa in taxas:
        taxa_qtd_dias[Decimal(taxa['taxa'])] = taxa['qtd_dias']
    if (juros_adicional == 0):
        valor_atualizado = calcular_valor_atualizado_com_taxas_di(taxa_qtd_dias, valor_inicial, percentual_di)
    else:
        # TODO adicionar juro adicional
        pass
    
    return valor_atualizado.quantize(Decimal('0.01'))