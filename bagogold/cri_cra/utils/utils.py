# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCRI_CRA
from bagogold.cri_cra.models.cri_cra import OperacaoCRI_CRA, CRI_CRA
from bagogold.cri_cra.utils.valorizacao import calcular_valor_um_cri_cra_na_data
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When
from django.db.models.fields import DecimalField

def quantidade_cri_cra_na_data_para_certificado(data, cri_cra):
    """
    Traz a quantidade que o investidor possui de determinado CRI/CRA até data definida
    Parâmetros: Data
                CRI/CRA
    Retorno: Quantidade possuída
    """
    qtd = OperacaoCRI_CRA.objects.filter(data__lte=data, cri_cra=cri_cra).values('cri_cra') \
        .annotate(qtd=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).aggregate(qtd_total=Sum('qtd'))['qtd_total'] or 0
                            
    return qtd

def qtd_cri_cra_ate_dia_para_divisao_para_certificado(dia, divisao_id, cri_cra_id):
    """ 
    Calcula a quantidade de certificados de determinado CRI/CRA até dia determinado para uma divisão
    Parâmetros: Dia final
                ID da divisão
                ID do certificado
    Retorno: Quantidade de títulos
    """
    qtd_total = DivisaoOperacaoCRI_CRA.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id, operacao__cri_cra__id=cri_cra_id).annotate(cri_cra=F('operacao__cri_cra')) \
        .values('cri_cra').annotate(qtd=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).aggregate(qtd_total=Sum('qtd'))['qtd_total']
        
    return qtd_total

def qtd_cri_cra_ate_dia(investidor, dia):
    """ 
    Calcula a quantidade de certificados até dia determinado para investidor
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de certificados {cri_cra_id: qtd}
    """
    qtd_cri_cra = dict(OperacaoCRI_CRA.objects.filter(data__lte=dia) \
        .values('cri_cra').annotate(qtd=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('cri_cra', 'qtd').exclude(qtd=0))
        
    return qtd_cri_cra

def qtd_cri_cra_ate_dia_para_certificado(dia, cri_cra_id):
    """ 
    Calcula a quantidade de certificados de determinado CRI/CRA até dia determinado para investidor
    Parâmetros: Dia final
                ID do certificado
    Retorno: Quantidade de títulos
    """
    qtd_total = OperacaoCRI_CRA.objects.filter(operacao__data__lte=dia, cri_cra__id=cri_cra_id) \
        .values('cri_cra').annotate(qtd=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).aggregate(qtd_total=Sum('qtd'))['qtd_total']
        
    return qtd_total

# TODO completar operação
def qtd_cri_cra_ate_dia_para_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de certificados até dia determinado para uma divisão
    Parâmetros: Dia final
                ID da divisão
    Retorno: Quantidade de títulos {titulo_id: qtd}
    """
    qtd_titulos = {}
    operacoes_divisao = list(DivisaoOperacaoCRI_CRA.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).annotate(cri_cra=F('operacao__cri_cra')) \
        .values('cri_cra').annotate(qtd_soma=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values('cri_cra', 'qtd_soma'))
        
    print operacoes_divisao
    
    return 0

def calcular_valor_cri_cra_ate_dia(investidor, dia):
    """ 
    Calcula o valor dos certificados do investidor até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Valor dos certificados {cri_cra_id: valor_da_data}
    """
    
    qtd_cri_cra = qtd_cri_cra_ate_dia(investidor, dia)
    
    for cri_cra_id in qtd_cri_cra.keys():
        qtd_cri_cra[cri_cra_id] = calcular_valor_um_cri_cra_na_data(CRI_CRA.objects.get(id=cri_cra_id), dia) * qtd_cri_cra[cri_cra_id]

    return qtd_cri_cra