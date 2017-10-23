# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoCDB_RDB, \
    TransferenciaEntreDivisoes
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models.expressions import F
from django.template.response import TemplateResponse
from itertools import chain
from operator import attrgetter

@login_required
@adiciona_titulo_descricao('Linha do tempo de divisão', 'Mostra as transferências e a utilização do dinheiro de uma divisão, ordenadas por data')
def linha_do_tempo(request):
    
    divisao = Divisao.objects.get(nome='Geral', investidor=request.user.investidor)
    
    divisao.saldo = Decimal(0)

    operacoes = DivisaoOperacaoCDB_RDB.objects.filter(divisao=divisao).annotate(data=F('operacao__data'))
        
    # Transferências
    transf_cedente = TransferenciaEntreDivisoes.objects.filter(divisao_cedente=divisao, investimento_origem=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB)
    transf_recebedora = TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=divisao, investimento_destino=TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB)
    
    eventos = sorted(chain(transf_recebedora, transf_cedente, operacoes),
                            key=attrgetter('data'))
    
    return TemplateResponse(request, 'divisoes/linha_do_tempo.html', {'divisao': divisao})

