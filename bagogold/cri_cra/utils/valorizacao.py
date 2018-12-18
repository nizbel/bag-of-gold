# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.db.models.aggregates import Count, Sum

from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaDI
from bagogold.bagogold.utils.misc import verifica_se_dia_util, \
    qtd_dias_uteis_no_periodo
from bagogold.bagogold.utils.taxas_indexacao import \
    calcular_valor_atualizado_com_taxas_di, \
    calcular_valor_atualizado_com_taxas_di_e_juros, \
    calcular_valor_atualizado_com_taxa_prefixado
from bagogold.cri_cra.models.cri_cra import CRI_CRA, DataRemuneracaoCRI_CRA, \
    DataAmortizacaoCRI_CRA


def calcular_valor_um_cri_cra_na_data(certificado, data=datetime.date.today(), simular_valores=False):
    """
    Calcula o valor de um certificado na data apontada
    
    Parâmetros: Certificado (CRI/CRA)
                Data
                Caso não existam valores até o momento, simular com últimos índices?
    Retorno:    Valor na data
    """
    # Pegar último dia útil da data caso não seja útil
    while not verifica_se_dia_util(data):
        data = data - datetime.timedelta(days=1)
    # Data não pode ser posterior a data de vencimento
    if data > certificado.data_vencimento:
        data = certificado.data_vencimento
    elif data < certificado.data_emissao:
        raise ValueError('Data anterior à data de emissão do certificado')
        
    if certificado.tipo_indexacao not in [escolha[0] for escolha in CRI_CRA.ESCOLHAS_TIPO_INDEXACAO]:
        raise ValueError('Indexador inválido')
    
    # Buscar data inicial, considerando a última data de remuneração antes da data enviada
    if DataRemuneracaoCRI_CRA.objects.filter(cri_cra=certificado, data__lt=data).exists():
        data_inicial = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=certificado, data__lt=data).order_by('-data')[0].data
    else:
        data_inicial = certificado.data_inicio_rendimento 
    
    # TODO incluir amortizações
    valor_inicial = certificado.valor_emissao \
        * (1 - (DataAmortizacaoCRI_CRA.objects.filter(cri_cra=certificado, data__lt=data).aggregate(soma=Sum('percentual'))['soma'] or 0) / 100)
    
    # Para calcular rendimento, não considerar data final como passível de valorização
    if data == certificado.data_vencimento:
        data -= datetime.timedelta(days=1)
        
    # TODO incluir outros cálculos
    if certificado.tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_DI:
        return calcular_valor_cri_cra_di(valor_inicial, certificado.porcentagem, data_inicial, data, certificado.juros_adicional, simular_valores)
    elif certificado.tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_PREFIXADO:
        return calcular_valor_cri_cra_prefixado(valor_inicial, certificado.porcentagem, data_inicial, data)
        
def calcular_valor_cri_cra_di(valor_inicial, percentual_di, data_inicial, data_final, juros_adicional, simular_valores=False):
    """
    Calcula o valor de um certificado atualizado pelo DI
    
    Parâmetros: Valor inicial a ser atualizado
                Percentual do DI
                Data de início da atualização
                Data de fim da atualização
                Juros adicional (percentual ao ano)
                Calcular valor futuro considerando último índice DI?
    Retorno:    Valor atualizado
    """
    count = 0
    while count < 2:
        data_inicial = data_inicial - datetime.timedelta(days=1)
        if verifica_se_dia_util(data_inicial):
            count += 1
            
    count = 0
    while count < 2:
        data_final = data_final - datetime.timedelta(days=1)
        if verifica_se_dia_util(data_final):
            count += 1
        
    taxas = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_final]).values('taxa').annotate(qtd_dias=Count('data'))
    taxa_qtd_dias = {}
    for taxa in taxas:
        taxa_qtd_dias[Decimal(taxa['taxa'])] = taxa['qtd_dias']
    
    # Simular valores com última posição do DI
    if simular_valores:
        data_final_di, taxa_final_di = HistoricoTaxaDI.objects.filter(data__range=[data_inicial, data_final]).values_list('data', 'taxa').order_by('-data')[0]
        qtd_dias_uteis_ate_data = qtd_dias_uteis_no_periodo(data_final_di + datetime.timedelta(days=1), data_final + datetime.timedelta(days=1))
        # Considerar rendimento do dia anterior
        taxa_qtd_dias[taxa_final_di] += qtd_dias_uteis_ate_data
        
    # Calcular
    if (juros_adicional == 0):
        valor_atualizado = calcular_valor_atualizado_com_taxas_di(taxa_qtd_dias, valor_inicial, percentual_di)
    else:
        valor_atualizado = calcular_valor_atualizado_com_taxas_di_e_juros(taxa_qtd_dias, valor_inicial, percentual_di, juros_adicional)
    
    return valor_atualizado

def calcular_valor_cri_cra_prefixado(valor_inicial, percentual, data_inicial, data_final):
    """
    Calcula o valor de um certificado atualizada por taxa prefixada
    
    Parâmetros: Valor inicial a ser atualizado
                Taxa prefixada
                Data de início da atualização
                Data de fim da atualização
    Retorno:    Valor atualizado
    """
    return calcular_valor_atualizado_com_taxa_prefixado(valor_inicial, percentual, (data_final - data_inicial).days)