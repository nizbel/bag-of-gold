# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.response import TemplateResponse
import calendar
import datetime


# Create your views here.

@login_required
def home(request):
    operacoes = OperacaoAcao.objects.exclude(data__isnull=True).order_by('data')
    
    # Dados para acompanhamento de vendas mensal e tributavel
    ano = operacoes[0].data.year
    mes = operacoes[0].data.month
    qtd_vendas_mensal = 0
    lucro_mensal = 0
    lucro_geral = 0
    
    # Dados para o gráfico
    graf_lucro_acumulado = list()
    graf_lucro_mensal = list()
    
    for operacao in operacoes:
        # Verificar se mes e ano foram alterados
        if (ano != operacao.data.year or mes != operacao.data.month): 
            
            # Adicionar dados ao gráfico
            graf_lucro_acumulado += [[str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000), float(lucro_geral)]]
            graf_lucro_mensal += [[str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000), float(lucro_mensal)]]
            
            ano = operacao.data.year
            mes = operacao.data.month
            
            # Reiniciar contadores mensais
            qtd_vendas_mensal = 0
            lucro_mensal = 0
            
        
        # Verificar se se trata de compra ou venda
        if operacao.tipo_operacao == 'C':
            operacao.total_gasto = -1 * (operacao.quantidade * operacao.preco_unitario + \
            operacao.emolumentos + operacao.corretagem)
        elif operacao.tipo_operacao == 'V':
            operacao.total_gasto = (operacao.quantidade * operacao.preco_unitario - \
            operacao.emolumentos - operacao.corretagem)
        
            qtd_vendas_mensal += operacao.quantidade * operacao.preco_unitario
            
        lucro_mensal += operacao.total_gasto
        lucro_geral += operacao.total_gasto
        operacao.lucro_mensal = lucro_mensal
        operacao.lucro_geral = lucro_geral
        operacao.qtd_vendas_mensal = qtd_vendas_mensal
                
    # Adicionar dados ao gráfico
    # TODO change this
    graf_lucro_acumulado[len(graf_lucro_acumulado)-1] = [str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000), float(lucro_geral)]
    graf_lucro_mensal[len(graf_lucro_mensal)-1] = [str(calendar.timegm(datetime.date(ano, mes, 1).timetuple()) * 1000), float(lucro_mensal)]
            
    return TemplateResponse(request, 'acoes/home_acoes.html', {'operacoes': operacoes, 'graf_lucro_acumulado': graf_lucro_acumulado,
                                                  'graf_lucro_mensal': graf_lucro_mensal})