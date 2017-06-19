# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoCRI_CRA
from bagogold.cri_cra.models.cri_cra import OperacaoCRI_CRA, CRI_CRA,\
    DataRemuneracaoCRI_CRA
from bagogold.cri_cra.utils.valorizacao import calcular_valor_um_cri_cra_na_data
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When
from django.db.models.fields import DecimalField
import datetime

def quantidade_cri_cra_na_data_para_certificado(cri_cra, data=datetime.date.today()):
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

def qtd_cri_cra_ate_dia_para_divisao_para_certificado(divisao_id, cri_cra_id, dia=datetime.date.today()):
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

def qtd_cri_cra_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de certificados até dia determinado para investidor
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de certificados {cri_cra_id: qtd}
    """
    qtd_cri_cra = dict(OperacaoCRI_CRA.objects.filter(data__lte=dia, cri_cra__investidor=investidor) \
        .values('cri_cra').annotate(qtd=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('cri_cra', 'qtd').exclude(qtd=0))

    return qtd_cri_cra

def qtd_cri_cra_ate_dia_para_certificado(cri_cra_id, dia=datetime.date.today()):
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

def qtd_cri_cra_ate_dia_para_divisao(divisao_id, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de certificados até dia determinado para uma divisão
    Parâmetros: Dia final
                ID da divisão
    Retorno: Quantidade de títulos {titulo_id: qtd}
    """
    qtd_titulos = dict(list(DivisaoOperacaoCRI_CRA.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).annotate(cri_cra=F('operacao__cri_cra')) \
        .values('cri_cra').annotate(qtd_soma=Sum(Case(When(operacao__tipo_operacao='C', then=F('quantidade')),
                            When(operacao__tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('cri_cra', 'qtd_soma').exclude(qtd_soma=0)))
        
    return qtd_titulos

def calcular_valor_cri_cra_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula o valor dos certificados do investidor até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Valor dos certificados {cri_cra_id: valor_da_data}
    """
    qtd_cri_cra = qtd_cri_cra_ate_dia(investidor, dia)
    
    for cri_cra in CRI_CRA.objects.filter(id__in=qtd_cri_cra.keys()):
        qtd_cri_cra[cri_cra.id] = calcular_valor_um_cri_cra_na_data(cri_cra, dia) * qtd_cri_cra[cri_cra.id]

    return qtd_cri_cra

def calcular_valor_cri_cra_ate_dia_para_divisao(divisao_id, dia=datetime.date.today()):
    """ 
    Calcula o valor dos certificados do investidor até dia determinado por divisão
    Parâmetros: Investidor
                Dia final
    Retorno: Valor dos certificados {cri_cra_id: valor_da_data}
    """
    qtd_cri_cra = qtd_cri_cra_ate_dia_para_divisao(divisao_id, dia)
    
    for cri_cra in CRI_CRA.objects.filter(id__in=qtd_cri_cra.keys()):
        qtd_cri_cra[cri_cra.id] = calcular_valor_um_cri_cra_na_data(cri_cra, dia) * qtd_cri_cra[cri_cra.id]

    return qtd_cri_cra

def calcular_rendimentos_cri_cra_ate_data_para_cri_cra(cri_cra, data=datetime.date.today()):
    """
    Calcula a quantidade de rendimentos recebida até data para um Certificado
    Parâmetros: CRI/CRA
                Dia final
    Retorno: Valor total dos rendimentos recebidos do certificado
    """
    datas_rendimento = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cri_cra, data__lte=data)
    # Retorna a soma das quantidades de certificados nas datas pelo valor recebido nas datas
    return sum([(quantidade_cri_cra_na_data_para_certificado(cri_cra, data_rendimento.data - datetime.timedelta(days=1)) * data_rendimento.qtd_remuneracao()) \
                 for data_rendimento in datas_rendimento])
        
def calcular_rendimentos_cri_cra_ate_data(investidor, data=datetime.date.today()):
    """
    Calcula a quantidade de rendimentos recebida até data
    Parâmetros: Investidor
                Dia final
    Retorno: Valor total dos rendimentos recebidos para todos os certificados
    """
    datas_rendimento = DataRemuneracaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, data__lte=data)
    return sum([(quantidade_cri_cra_na_data_para_certificado(data_rendimento.cri_cra, data_rendimento.data - datetime.timedelta(days=1)) * data_rendimento.qtd_remuneracao()) \
                 for data_rendimento in datas_rendimento])