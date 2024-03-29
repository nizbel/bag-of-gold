# -*- coding: utf-8 -*-
from bagogold.bagogold.models.divisoes import DivisaoOperacaoFundoInvestimento
from bagogold.fundo_investimento.models import OperacaoFundoInvestimento, \
    HistoricoValorCotas, FundoInvestimento
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Case, When
from django.db.models.fields import DecimalField
from django.utils.text import slugify
import datetime
import re

def calcular_qtd_cotas_ate_dia(investidor, dia=None):
    """ 
    Calcula a quantidade de cotas até dia determinado
    
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de cotas por fundo {fundo_id: qtd}
    """
    # Preparar data
    if dia == None:
        dia = datetime.date.today()
        
    qtd_cotas = dict(OperacaoFundoInvestimento.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).values('fundo_investimento') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('fundo_investimento', 'total').exclude(total=0))
    
    return qtd_cotas

def calcular_qtd_cotas_ate_dia_por_fundo(investidor, fundo_id, dia=None):
    """ 
    Calcula a quantidade de cotas até dia determinado para um fundo determinado
    
    Parâmetros: Investidor
                ID do Fundo de investimento
                Dia final
    Retorno: Quantidade de cotas para o fundo determinado
    """
    # Preparar data
    if dia == None:
        dia = datetime.date.today()
    
    qtd_cotas = OperacaoFundoInvestimento.objects.filter(investidor=investidor, fundo_investimento__id=fundo_id, data__lte=dia).exclude(data__isnull=True) \
        .aggregate(qtd_cotas=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField())))['qtd_cotas'] or 0
        
    return qtd_cotas

def calcular_qtd_cotas_ate_dia_por_divisao(dia, divisao_id):
    """ 
    Calcula a quantidade de cotas até dia determinado
    Parâmetros: Dia final
                Id da divisão
    Retorno: Quantidade de cotas {fundo_id: qtd}
    """
#     operacoes_divisao_id = DivisaoOperacaoFundoInvestimento.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id).values('operacao__id')
#     if len(operacoes_divisao_id) == 0:
#         return {}
#     operacoes = OperacaoFundoInvestimento.objects.filter(id__in=operacoes_divisao_id).exclude(data__isnull=True).order_by('data')
#     
#     qtd_cotas = {}
#     
#     for operacao in operacoes:
#         # Preparar a quantidade da operação pela quantidade que foi destinada a essa divisão
#         operacao.quantidade = DivisaoOperacaoFundoInvestimento.objects.get(divisao__id=divisao_id, operacao=operacao).quantidade
#         
#         if operacao.fundo_investimento.id not in qtd_cotas:
#             qtd_cotas[operacao.fundo_investimento.id] = 0
#             
#         # Verificar se se trata de compra ou venda
#         if operacao.tipo_operacao == 'C':
#             qtd_cotas[operacao.fundo_investimento.id] += operacao.quantidade
#             
#         elif operacao.tipo_operacao == 'V':
#             qtd_cotas[operacao.fundo_investimento.id] -= operacao.quantidade
#             
#         print qtd_cotas
#         
#     for key, item in qtd_cotas.items():
#         if qtd_cotas[key] == 0:
#             del qtd_cotas[key]
    qtd_cotas = dict(DivisaoOperacaoFundoInvestimento.objects.filter(operacao__data__lte=dia, divisao__id=divisao_id) \
                     .annotate(fundo_id=F('operacao__fundo_investimento')).values('fundo_id') \
                     .annotate(qtd=Sum(Case(When(operacao__tipo_operacao='C', then=F('operacao__quantidade') * F('quantidade') / F('operacao__valor')),
                            When(operacao__tipo_operacao='V', then=(F('operacao__quantidade') * F('quantidade') / F('operacao__valor'))*-1),
                            output_field=DecimalField()))).values_list('fundo_id', 'qtd').exclude(qtd=0))
            
    return qtd_cotas

def calcular_valor_fundos_investimento_ate_dia(investidor, dia=None):
    """ 
    Calcula a o valor das cotas do investidor até dia determinado
    
    Parâmetros: Investidor
                Dia final
    Retorno: Valor por fundo {fundo_id: valor (em reais)}
    """
    # Preparar data
    if dia == None:
        dia = datetime.date.today()
        
    fundos = calcular_qtd_cotas_ate_dia(investidor, dia)
    valor_fundos = {}
    for fundo_id in fundos.keys():
        if HistoricoValorCotas.objects.filter(fundo_investimento__id=fundo_id, data__lte=dia).exists():
            historico_fundo = HistoricoValorCotas.objects.filter(fundo_investimento__id=fundo_id, data__lte=dia).order_by('-data')[0]
            if investidor and OperacaoFundoInvestimento.objects.filter(fundo_investimento__id=fundo_id, investidor=investidor, data__range=[historico_fundo.data + datetime.timedelta(days=1), dia]).exists():
                valor_cota = OperacaoFundoInvestimento.objects.filter(fundo_investimento__id=fundo_id, investidor=investidor, 
                                                                data__range=[historico_fundo.data + datetime.timedelta(days=1), dia]).order_by('-data')[0].valor_cota()
            else:
                valor_cota = historico_fundo.valor_cota
        else:
            valor_cota = OperacaoFundoInvestimento.objects.filter(fundo_investimento__id=fundo_id, investidor=investidor, data__lte=dia).order_by('-data')[0].valor_cota()
        valor_fundos[fundo_id] = valor_cota * fundos[fundo_id]
    return valor_fundos

def criar_slug_fundo_investimento_valido(fundo_nome):
    """
    Gera um slug válido para um fundo de investimento a partir de seu nome
    Parâmetros: Nome do fundo de investimento
    Retorno: Slug válido
    """
    slug = slugify(fundo_nome.replace('.', '-').replace('/', '-'))

    for string in ['de', 'no', 'em', 'com', 'da[s]?', 'do[s]?', 'na[s]?', 'sem', 'fi[i]?', 'fundo[s]?', 'fdo[s]?', 'investimento[s]?', 'invest', 'inv']:
        slug = re.sub('-%s(?=-)' % (string), '-', re.sub('(^%s-|-%s$)' % (string, string), '', slug))
    slug = re.sub('-$', '', re.sub('^-', '', re.sub('-+', '-', slug)))
    
    final = 0
    slug_temp = slug
    # Verifica se já existe o slug de Fundo de Investimento criado
    while FundoInvestimento.objects.filter(slug=slug_temp).exists():
        # Adicionar numeral ao final do slug, mantendo o limite de 100 caracteres
        final += 1
        slug_temp = '%s-%s' % (slug, final)
        if slug_temp > 100:
            string_final = str(final)
            slug_temp = '%s-%s' % (slug[: 100 - (len(string_final) + 1)], string_final)
    slug = slug_temp
    return slug


def formatar_cnpj(string):
    string = re.sub(r'\D', '', string)
    while len(string) < 14:
        string = '0' + string
    return string[0:2] + '.' + string[2:5] + '.' + string[5:8] + '/' + string[8:12] + '-' + string[12:14]