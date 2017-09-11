# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.outros_investimentos.models import Investimento
from django.template.response import TemplateResponse

def editar_investimento(request):
    pass

def editar_operacao(request):
    pass

def historico(request):
    pass

def inserir_investimento(request):
    pass

def inserir_operacao(request):
    pass

@adiciona_titulo_descricao('Listar outros investimentos', 'Lista de investimentos cadastrados pelo investidor')
def listar_investimentos(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'outros_investimentos/listar_investimentos.html', {'investimentos': list()})
    
    investimentos = Investimento.objects.filter(investidor=investidor)
    
    return TemplateResponse(request, 'outros_investimentos/listar_investimentos.html', {'investimentos': investimentos})

def painel(request):
    pass