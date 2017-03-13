# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCRI_CRA
from bagogold.cri_cra.models.cri_cra import OperacaoCRI_CRA
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
    qtd = 0
    qtd += OperacaoCRI_CRA.objects.filter(tipo_operacao='C', data__lte=data, cri_cra=cri_cra).aggregate(Sum('quantidade'))['quantidade__sum'] or 0
    qtd -= OperacaoCRI_CRA.objects.filter(tipo_operacao='V', data__lte=data, cri_cra=cri_cra).aggregate(Sum('quantidade'))['quantidade__sum'] or 0
    return qtd

def qtd_cri_cra_ate_dia_para_divisao_para_certificado(dia, divisao_id, cri_cra_id):
    """ 
    Calcula a quantidade de certificados de determinado CRI/CRA até dia determinado para uma divisão
    Parâmetros: Dia final
                ID da divisão
    Retorno: Quantidade de títulos {titulo_id: qtd}
    """
    qtd_titulos = {}
    operacoes_divisao = list(DivisaoOperacaoCRI_CRA.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id, operacao__cri_cra__id=cri_cra_id).annotate(titulo=F('operacao__cri_cra')) \
        .annotate(qtd_soma=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))))
        
    print operacoes_divisao
    
    return 0