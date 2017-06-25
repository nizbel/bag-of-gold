# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.criptomoeda.models import Criptomoeda
from decimal import Decimal
from django.template.response import TemplateResponse
from urllib2 import urlopen
import datetime
import json

@adiciona_titulo_descricao('Listar fundos de investimento cadastrados', 'Lista os fundos cadastrados no sistema e suas principais características')
def listar_moedas(request):
    moedas = Criptomoeda.objects.all()
    
    for moeda in moedas:
        url = 'https://api.cryptonator.com/api/ticker/%s-usd' % (moeda.ticker)
        resultado = urlopen(url)
        data = json.load(resultado) 
        moeda.valor_atual = Decimal(data['ticker']['price'])
        moeda.valor_horario = datetime.datetime.fromtimestamp(data['timestamp'])
    
    return TemplateResponse(request, 'criptomoedas/listar_moedas.html', {'moedas': moedas})