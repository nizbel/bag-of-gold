# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.models.acoes import Acao, ValorDiarioAcao, HistoricoAcao
from bagogold.bagogold.utils.acoes import quantidade_acoes_ate_dia, \
    calcular_poupanca_prov_acao_ate_dia
from bagogold.bagogold.utils.investidores import buscar_acoes_investidor_na_data
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
import datetime

@adiciona_titulo_descricao('Lista de ações', 'Lista as ações da Bovespa')
def listar_acoes(request):
    acoes = Acao.objects.all()
    
    return TemplateResponse(request, 'acoes/listar_acoes.html', {'acoes': acoes})

@adiciona_titulo_descricao('Lista de proventos', 'Lista os proventos de ações cadastrados')
def listar_proventos(request):
    proventos = Provento.objects.all()
    
    ultimas_atualizacoes = InvestidorValidacaoDocumento.objects.filter(documento__tipo='A').order_by('-data_validacao')[:5] \
        .values('documento').annotate(provento=F('documento__proventoacaodocumento__provento'))
    
    return TemplateResponse(request, 'acoes/listar_proventos.html', {'proventos': proventos, 'ultimas_atualizacoes': ultimas_atualizacoes})

@adiciona_titulo_descricao('Sobre Ações', 'Detalha o que são Ações')
def sobre(request):
    if request.user.is_authenticated():
        total_atual = 0
        data_atual = datetime.date.today()
        acoes_investidor = buscar_acoes_investidor_na_data(request.user.investidor)
        # Cálculo de quantidade
        for acao in Acao.objects.filter(id__in=acoes_investidor):
            acao_qtd = quantidade_acoes_ate_dia(request.user.investidor, acao.ticker, data_atual, considerar_trade=True)
            if acao_qtd > 0:
                if ValorDiarioAcao.objects.filter(acao__ticker=acao.ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
                    acao_valor = ValorDiarioAcao.objects.filter(acao__ticker=acao.ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_unitario
                else:
                    acao_valor = HistoricoAcao.objects.filter(acao__ticker=acao.ticker).order_by('-data')[0].preco_unitario
                total_atual += (acao_qtd * acao_valor)
        total_atual += calcular_poupanca_prov_acao_ate_dia(request.user.investidor, data_atual)
    else:
        total_atual = 0
    
    return TemplateResponse(request, 'acoes/sobre.html', {'total_atual': total_atual})