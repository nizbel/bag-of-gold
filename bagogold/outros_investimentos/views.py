# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.outros_investimentos.models import Investimento
from bagogold.outros_investimentos.utils import \
    calcular_valor_outros_investimentos_ate_data
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse

def editar_investimento(request):
    pass

def historico(request):
    pass

def inserir_investimento(request):
    pass


@adiciona_titulo_descricao('Listar outros investimentos', 'Lista de investimentos cadastrados pelo investidor')
def listar_investimentos(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'outros_investimentos/listar_investimentos.html', {'investimentos': list()})
    
    investimentos = Investimento.objects.filter(investidor=investidor)
    
    return TemplateResponse(request, 'outros_investimentos/listar_investimentos.html', {'investimentos': investimentos})

@login_required
@adiciona_titulo_descricao('Painel de Outros Investimentos', 'Posição atual do investidor em outros investimentos')
def painel(request):
    investidor = request.user.investidor
    qtd_investimentos = calcular_valor_outros_investimentos_ate_data(investidor)
    
    investimentos = Investimento.objects.filter(id__in=qtd_investimentos.keys())
    
    return TemplateResponse(request, 'outros_investimentos/painel.html', {'investimentos': investimentos})