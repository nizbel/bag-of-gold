# -*- coding: utf-8 -*-
from bagogold.cri_cra.models.cri_cra import OperacaoCRI_CRA
from django.db.models.aggregates import Sum

def quantidade_cri_cra_na_data_por_certificado(data, cri_cra):
    """
    Traz a quantidade que o investidor possui de determinado CRI/CRA até data definida
    Parâmetros: Data
                CRI/CRA
    Retorno: Quantidade possuída
    """
    qtd = 0
    qtd += OperacaoCRI_CRA.objects.filter(tipo_operacao='C', data__lte=data, cri_cra=cri_cra).aggregate(Sum('quantidade'))
    qtd -= OperacaoCRI_CRA.objects.filter(tipo_operacao='V', data__lte=data, cri_cra=cri_cra).aggregate(Sum('quantidade'))
    return qtd