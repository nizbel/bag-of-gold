# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.criptomoeda.models import Criptomoeda
from decimal import Decimal
from django.template.response import TemplateResponse
from urllib2 import urlopen
import json


def editar_operacao_criptomoeda(request):
    pass

def inserir_operacao_criptomoeda(request):
    pass

def historico(request):
    pass

@adiciona_titulo_descricao('Listar fundos de investimento cadastrados', 'Lista os fundos cadastrados no sistema e suas principais características')
def listar_moedas(request):
    moedas = Criptomoeda.objects.all()
    
    # Carrega o valor de um dólar em reais, mais atual
    url_dolar = 'http://api.fixer.io/latest?base=USD&symbols=BRL'
    resultado = urlopen(url_dolar)
    data = json.load(resultado) 
    dolar_para_real = Decimal(data['rates']['BRL'])
    
    for moeda in moedas:
        url = 'https://api.cryptonator.com/api/ticker/%s-usd' % (moeda.ticker)
        resultado = urlopen(url)
        data = json.load(resultado) 
        moeda.valor_atual = dolar_para_real * Decimal(data['ticker']['price'])
    
    return TemplateResponse(request, 'criptomoedas/listar_moedas.html', {'moedas': moedas})

def painel(request):
    pass

def sobre(request):
    pass