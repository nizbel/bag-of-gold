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

def calcular_qtd_cotas_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de cotas até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Quantidade de cotas por fundo {fundo_id: qtd}
    """
    qtd_cotas = dict(OperacaoFundoInvestimento.objects.filter(investidor=investidor, data__lte=dia).exclude(data__isnull=True).values('fundo_investimento') \
        .annotate(total=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))).values_list('fundo_investimento', 'total').exclude(total=0))
    
    return qtd_cotas

def calcular_qtd_cotas_ate_dia_por_fundo(investidor, fundo_id, dia=datetime.date.today()):
    """ 
    Calcula a quantidade de cotas até dia determinado para um fundo determinado
    Parâmetros: Investidor
                ID do Fundo de investimento
                Dia final
    Retorno: Quantidade de cotas para o fundo determinado
    """
    
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

def calcular_valor_fundos_investimento_ate_dia(investidor, dia=datetime.date.today()):
    """ 
    Calcula a o valor das cotas do investidor até dia determinado
    Parâmetros: Investidor
                Dia final
    Retorno: Valor por fundo {fundo_id: valor (em reais)}
    """
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
#     fundo_nome = fundo_nome.replace('+', 'mais')
    slug = slugify(fundo_nome)
    slug = slug.replace('-de-', '-').replace('-no-', '-').replace('-em-', '-')
    slug = re.sub('-$', '', re.sub('^-', '', re.sub('-+', '-', re.sub('(fi-|fundos|fundo|fdo|investimentos|investimento|invest|inv)', '', slug))))
    # Verifica se já existe o slug de Fundo de Investimento criado
    while FundoInvestimento.objects.filter(slug=slug).exists():
        # Adicionar numeral ao final do slug, mantendo o limite de 30 caracteres
#         print 'colisao', slug
#         print fundo_nome
#         print list(FundoInvestimento.objects.filter(slug=slug))
        # Buscar último fundo com esse nome
        ultimo_fundo_mesmo_nome = FundoInvestimento.objects.filter(slug=slug).order_by('-data_constituicao')[0]
        slug_ultimo_fundo = ultimo_fundo_mesmo_nome.slug
        final_slug = slug_ultimo_fundo[slug_ultimo_fundo.rfind('-')+1:]
        # Número do slug
        numero_slug = 1 if not final_slug.isdigit() else int(final_slug)+1
        
        # Criar slug temporário para verificar tamanho
        slug_temp = u'%s-%s' % (slug, numero_slug)
        while len(slug_temp) > 100:
            slug = slug[:-1]
            slug_temp = u'%s-%s' % (slug, numero_slug)
        slug = slug_temp
    return slug