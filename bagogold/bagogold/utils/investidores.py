# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from itertools import chain
from operator import attrgetter

from django.db.models.aggregates import Max

from bagogold.bagogold.models.acoes import OperacaoAcao, ValorDiarioAcao, \
    HistoricoAcao, AcaoProvento, Acao, Provento
from bagogold.debentures.models import HistoricoValorDebenture, \
    OperacaoDebenture
from bagogold.bagogold.models.divisoes import CheckpointDivisaoFII, \
    CheckpointDivisaoProventosFII, Divisao, CheckpointDivisaoCDB_RDB, \
    CheckpointDivisaoLetraCambio, CheckpointDivisaoLCI_LCA
from bagogold.bagogold.models.investidores import LoginIncorreto
from bagogold.bagogold.signals.divisao_cdb_rdb import \
    gerar_checkpoint_divisao_cdb_rdb
from bagogold.bagogold.signals.divisao_fii import gerar_checkpoint_divisao_fii, \
    gerar_checkpoint_divisao_proventos_fii
from bagogold.bagogold.signals.divisao_lc import gerar_checkpoint_divisao_lc
from bagogold.bagogold.utils.acoes import quantidade_acoes_ate_dia, \
    calcular_poupanca_prov_acao_ate_dia
from bagogold.debentures.utils import calcular_qtd_debentures_ate_dia
from bagogold.cdb_rdb.models import OperacaoCDB_RDB, CheckpointCDB_RDB
from bagogold.cdb_rdb.signals import gerar_checkpoint_cdb_rdb
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia
from bagogold.cri_cra.models.cri_cra import CRI_CRA, OperacaoCRI_CRA
from bagogold.cri_cra.utils.utils import qtd_cri_cra_ate_dia
from bagogold.cri_cra.utils.valorizacao import calcular_valor_um_cri_cra_na_data
from bagogold.criptomoeda.models import Criptomoeda, OperacaoCriptomoeda, \
    ValorDiarioCriptomoeda
from bagogold.criptomoeda.utils import calcular_qtd_moedas_ate_dia
from bagogold.fii.models import OperacaoFII, ValorDiarioFII, HistoricoFII, FII, \
    ProventoFII, CheckpointFII, CheckpointProventosFII
from bagogold.fii.signals import gerar_checkpoint_fii, \
    gerar_checkpoint_proventos_fii
from bagogold.fii.utils import calcular_qtd_fiis_ate_dia_por_ticker, \
    calcular_qtd_fiis_ate_dia, calcular_poupanca_prov_fii_ate_dia
from bagogold.fundo_investimento.models import OperacaoFundoInvestimento
from bagogold.fundo_investimento.utils import \
    calcular_valor_fundos_investimento_ate_dia
from bagogold.lc.models import OperacaoLetraCambio, CheckpointLetraCambio
from bagogold.lc.signals import gerar_checkpoint_lc
from bagogold.lc.utils import calcular_valor_lc_ate_dia
from bagogold.lci_lca.models import OperacaoLetraCredito, CheckpointLetraCredito
from bagogold.lci_lca.utils import calcular_valor_lci_lca_ate_dia
from bagogold.outros_investimentos.models import Investimento
from bagogold.outros_investimentos.utils import \
    calcular_valor_outros_investimentos_ate_data
from bagogold.tesouro_direto.models import OperacaoTitulo, ValorDiarioTitulo, \
    HistoricoTitulo
from bagogold.tesouro_direto.utils import quantidade_titulos_ate_dia
from bagogold.bagogold.signals.divisao_lci_lca import gerar_checkpoint_divisao_lci_lca
from bagogold.lci_lca.signals import gerar_checkpoint_lci_lca


def is_superuser(user):
    if user.is_superuser:
        return True
    raise PermissionDenied

def atualizar_checkpoints(investidor, ano_maximo=None):
    """
    Atualiza os checkpoints para um investidor, buscando os últimos checkpoints registrados
    
    Parâmetros: Investidor
                Último ano a partir do qual deve ser atualizado
    """
    if ano_maximo == None:
        ano_maximo = datetime.date.today().year
    
    # FII
    # Verificar se usuário possui operações em FII
    if OperacaoFII.objects.filter(investidor=investidor).exists():
        # Pegar últimos anos de checkpoints com quantidade maior que 0
        lista_fiis_anos = CheckpointFII.objects.filter(investidor=investidor).values('fii').annotate(ultimo_ano=Max('ano')) \
            .values('fii', 'ultimo_ano', 'quantidade').exclude(quantidade=0)
        for fii_ano in lista_fiis_anos:
            ultimo_ano_checkpoint = min(fii_ano['ultimo_ano'], ano_maximo)
            fii = FII.objects.get(id=fii_ano['fii'])
            # Repete o procedimento para o ano posterior ao último checkpoint, até o ano atual
            for ano in range(ultimo_ano_checkpoint+1, datetime.date.today().year+1):
                ano_atual = ano
                ano_anterior = ano_atual - 1
                
                # Verifica se ano anterior não possui quantidade 0 para poder gerar checkpoints do ano atual
                if CheckpointFII.objects.filter(investidor=investidor, ano=ano_anterior, fii=fii, quantidade__gt=0).exists():
                    gerar_checkpoint_fii(investidor, fii, ano_atual)
                for divisao_id in CheckpointDivisaoFII.objects.filter(divisao__investidor=investidor, ano=ano_anterior, 
                                                                      fii=fii, quantidade__gt=0).values_list('divisao', flat=True):
                    gerar_checkpoint_divisao_fii(Divisao.objects.get(id=divisao_id), fii, ano_atual)
                    
        # Gerar checkpoints de proventos
        if CheckpointProventosFII.objects.filter(investidor=investidor).exists():
            for ano in range(CheckpointProventosFII.objects.filter(investidor=investidor).order_by('-ano')[0].ano+1, datetime.date.today().year+1):
                gerar_checkpoint_proventos_fii(investidor, ano)
        
        lista_divisoes_anos = CheckpointDivisaoProventosFII.objects.filter(divisao__investidor=investidor).values('divisao').annotate(ultimo_ano=Max('ano')) \
            .values('divisao', 'ultimo_ano', 'valor').exclude(valor=0)
        for divisao_ano in lista_divisoes_anos:
            ultimo_ano_checkpoint = min(divisao_ano['ultimo_ano'], ano_maximo)
            divisao = Divisao.objects.get(id=divisao_ano['divisao'])
            # Repete o procedimento ano a ano, até o ano atual
            for ano in range(ultimo_ano_checkpoint+1, datetime.date.today().year+1):
                gerar_checkpoint_divisao_proventos_fii(divisao, ano)
                
    # CDB/RDB
    # Verificar se usuário possui operações em CDB/RDB
    if OperacaoCDB_RDB.objects.filter(investidor=investidor).exists():
        # Buscar ano mais recente de checkpoints anterior ao ano atual
        if CheckpointCDB_RDB.objects.filter(operacao__investidor=investidor, ano__lt=datetime.date.today().year).exists():
            ano_mais_recente = CheckpointCDB_RDB.objects.filter(operacao__investidor=investidor, ano__lt=datetime.date.today().year).order_by('-ano')[0].ano
        # Caso não haja checkpoint, buscar ano da primeira operação em cdb/rdb
        else:
            ano_mais_recente = OperacaoCDB_RDB.objects.filter(investidor=investidor).order_by('-data')[0].data.year
        
        ano_mais_recente = min(ano_mais_recente, ano_maximo)
        # Gerar checkpoints a partir do ano seguinte a esse ano mais recente
        for ano in xrange(ano_mais_recente, datetime.date.today().year+1):
            # Para checkpoints no ano mais recente
            for checkpoint in CheckpointCDB_RDB.objects.filter(operacao__investidor=investidor, ano=ano_mais_recente):
                gerar_checkpoint_cdb_rdb(checkpoint.operacao, ano)
        
#             # Para compras feitas entre o ano mais recente e o atual
#             for operacao in OperacaoCDB_RDB.objects.filter(investidor=investidor, data__year__gte=ano_mais_recente)
        
        # Repetir o processo para divisões
        if CheckpointDivisaoCDB_RDB.objects.filter(divisao_operacao__divisao__investidor=investidor, ano__lt=datetime.date.today().year).exists():
            ano_mais_recente = CheckpointDivisaoCDB_RDB.objects.filter(divisao_operacao__divisao__investidor=investidor, ano__lt=datetime.date.today().year).order_by('-ano')[0].ano
        # Caso não haja checkpoint, buscar ano da primeira operação em cdb/rdb
        else:
            ano_mais_recente = OperacaoCDB_RDB.objects.filter(investidor=investidor).order_by('-data')[0].data.year
            
        ano_mais_recente = min(ano_mais_recente, ano_maximo)
        # Gerar checkpoints a partir do ano seguinte a esse ano mais recente
        for ano in xrange(ano_mais_recente, datetime.date.today().year+1):
            # Para checkpoints no ano mais recente
            for checkpoint in CheckpointDivisaoCDB_RDB.objects.filter(divisao_operacao__operacao__investidor=investidor, ano=ano_mais_recente):
                gerar_checkpoint_divisao_cdb_rdb(checkpoint.divisao_operacao, ano)
                
    # Letra de Câmbio
    # Verificar se usuário possui operações em Letra de Câmbio
    if OperacaoLetraCambio.objects.filter(investidor=investidor).exists():
        # Buscar ano mais recente de checkpoints anterior ao ano atual
        if CheckpointLetraCambio.objects.filter(operacao__investidor=investidor, ano__lt=datetime.date.today().year).exists():
            ano_mais_recente = CheckpointLetraCambio.objects.filter(operacao__investidor=investidor, ano__lt=datetime.date.today().year).order_by('-ano')[0].ano
        # Caso não haja checkpoint, buscar ano da primeira operação em letra de cambio
        else:
            ano_mais_recente = OperacaoLetraCambio.objects.filter(investidor=investidor).order_by('-data')[0].data.year
            
        ano_mais_recente = min(ano_mais_recente, ano_maximo)
        # Gerar checkpoints a partir do ano seguinte a esse ano mais recente
        for ano in xrange(ano_mais_recente, datetime.date.today().year+1):
            # Para checkpoints no ano mais recente
            for checkpoint in CheckpointLetraCambio.objects.filter(operacao__investidor=investidor, ano=ano_mais_recente):
                gerar_checkpoint_lc(checkpoint.operacao, ano)
        
#             # Para compras feitas entre o ano mais recente e o atual
#             for operacao in OperacaoLetraCambio.objects.filter(investidor=investidor, data__year__gte=ano_mais_recente)
        
        # Repetir o processo para divisões
        if CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__divisao__investidor=investidor, ano__lt=datetime.date.today().year).exists():
            ano_mais_recente = CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__divisao__investidor=investidor, ano__lt=datetime.date.today().year).order_by('-ano')[0].ano
        # Caso não haja checkpoint, buscar ano da primeira operação em letra de cambio
        else:
            ano_mais_recente = OperacaoLetraCambio.objects.filter(investidor=investidor).order_by('-data')[0].data.year
            
        ano_mais_recente = min(ano_mais_recente, ano_maximo)
        # Gerar checkpoints a partir do ano seguinte a esse ano mais recente
        for ano in xrange(ano_mais_recente, datetime.date.today().year+1):
            # Para checkpoints no ano mais recente
            for checkpoint in CheckpointDivisaoLetraCambio.objects.filter(divisao_operacao__operacao__investidor=investidor, ano=ano_mais_recente):
                gerar_checkpoint_divisao_lc(checkpoint.divisao_operacao, ano)
                
    # LCI/LCA
    # Verificar se usuário possui operações em LCI/LCA
    if OperacaoLetraCredito.objects.filter(investidor=investidor).exists():
        # Buscar ano mais recente de checkpoints anterior ao ano atual
        if CheckpointLetraCredito.objects.filter(operacao__investidor=investidor, ano__lt=datetime.date.today().year).exists():
            ano_mais_recente = CheckpointLetraCredito.objects.filter(operacao__investidor=investidor, ano__lt=datetime.date.today().year).order_by('-ano')[0].ano
        # Caso não haja checkpoint, buscar ano da primeira operação em letra de cambio
        else:
            ano_mais_recente = OperacaoLetraCredito.objects.filter(investidor=investidor).order_by('-data')[0].data.year
            
        ano_mais_recente = min(ano_mais_recente, ano_maximo)
        # Gerar checkpoints a partir do ano seguinte a esse ano mais recente
        for ano in xrange(ano_mais_recente, datetime.date.today().year+1):
            # Para checkpoints no ano mais recente
            for checkpoint in CheckpointLetraCredito.objects.filter(operacao__investidor=investidor, ano=ano_mais_recente):
                gerar_checkpoint_lci_lca(checkpoint.operacao, ano)
        
#             # Para compras feitas entre o ano mais recente e o atual
#             for operacao in OperacaoLetraCredito.objects.filter(investidor=investidor, data__year__gte=ano_mais_recente)
        
        # Repetir o processo para divisões
        if CheckpointDivisaoLCI_LCA.objects.filter(divisao_operacao__divisao__investidor=investidor, ano__lt=datetime.date.today().year).exists():
            ano_mais_recente = CheckpointDivisaoLCI_LCA.objects.filter(divisao_operacao__divisao__investidor=investidor, ano__lt=datetime.date.today().year).order_by('-ano')[0].ano
        # Caso não haja checkpoint, buscar ano da primeira operação em letra de cambio
        else:
            ano_mais_recente = OperacaoLetraCredito.objects.filter(investidor=investidor).order_by('-data')[0].data.year
            
        ano_mais_recente = min(ano_mais_recente, ano_maximo)
        # Gerar checkpoints a partir do ano seguinte a esse ano mais recente
        for ano in xrange(ano_mais_recente, datetime.date.today().year+1):
            # Para checkpoints no ano mais recente
            for checkpoint in CheckpointDivisaoLCI_LCA.objects.filter(divisao_operacao__operacao__investidor=investidor, ano=ano_mais_recente):
                gerar_checkpoint_divisao_lci_lca(checkpoint.divisao_operacao, ano)
                
def buscar_acoes_investidor_na_data(investidor, data=None, destinacao=''):
    """
    Busca as ações que o investidor possui na da especificada
    
    Parâmetros: Investidor
                Data da posição
                Destinação (Buy and Hold, Trading ou ambos)
    Retorno: Lista com as ações que o investidor possui posição
    """
    # Preparar data
    if data == None:
        data = datetime.date.today()
        
    if destinacao not in ['', 'B', 'T']:
        raise ValueError
    # Buscar proventos em ações
    acoes_operadas = OperacaoAcao.objects.filter(investidor=investidor, data__lte=data).values_list('acao', flat=True) if destinacao == '' \
            else OperacaoAcao.objects.filter(investidor=investidor, data__lte=data, destinacao=destinacao).values_list('acao', flat=True)
    
    # Remover ações repetidas
    acoes_operadas = list(set(acoes_operadas))
    
    proventos_em_acoes = list(set(AcaoProvento.objects.filter(provento__acao__in=acoes_operadas, provento__data_pagamento__lte=data) \
                                  .values_list('acao_recebida', flat=True)))
    
    # Adicionar ações recebidas pelo investidor
    acoes_investidor = list(set(acoes_operadas + proventos_em_acoes))
    
    return acoes_investidor

def buscar_ultimas_operacoes(investidor, quantidade_operacoes):
    """
    Busca as últimas operações feitas pelo investidor, ordenadas por data decrescente
    
    Parâmetros: Investidor
                Quantidade de operações a ser retornada
    Retorno: Lista com as operações ordenadas por data
    """
    # Juntar todas as operações em uma lista
    operacoes_fii = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_td = OperacaoTitulo.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_acoes = OperacaoAcao.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_lc = OperacaoLetraCambio.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_lci_lca = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_cri_cra = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_debentures = OperacaoDebenture.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_fundo_investimento = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    operacoes_criptomoedas = OperacaoCriptomoeda.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    outros_investimentos = Investimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-data')[:quantidade_operacoes]
    
    lista_operacoes = sorted(chain(operacoes_fii, operacoes_td, operacoes_acoes, operacoes_lci_lca, operacoes_cdb_rdb, 
                                   operacoes_cri_cra, operacoes_debentures, operacoes_fundo_investimento, operacoes_criptomoedas, 
                                   outros_investimentos, operacoes_lc),
                             key=attrgetter('data'), reverse=True)
    
    ultimas_operacoes = lista_operacoes[:min(quantidade_operacoes, len(lista_operacoes))]
    
    return ultimas_operacoes

def buscar_operacoes_no_periodo(investidor, data_inicial, data_final=datetime.date.today()):
#     from bagogold.cdb_rdb.models import OperacaoCDB_RDB
    """
    Busca as operações feitas pelo investidor, ordenadas por data crescente, no período especificado
    
    Parâmetros: Investidor
                Data inicial
                Data final
    Retorno: Lista com as operações ordenadas por data
    """
    # Juntar todas as operações em uma lista
    operacoes_fii = OperacaoFII.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    operacoes_td = OperacaoTitulo.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    operacoes_acoes = OperacaoAcao.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    operacoes_lc = OperacaoLetraCambio.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_lci_lca = OperacaoLetraCredito.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_cri_cra = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_criptomoeda = OperacaoCriptomoeda.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    operacoes_debentures = OperacaoDebenture.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_fundo_investimento = OperacaoFundoInvestimento.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    outros_investimentos = Investimento.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    
    lista_operacoes = sorted(chain(operacoes_fii, operacoes_td, operacoes_acoes, operacoes_lci_lca, operacoes_cdb_rdb, 
                                   operacoes_cri_cra, operacoes_criptomoeda, operacoes_debentures, operacoes_fundo_investimento, 
                                   operacoes_lc, outros_investimentos),
                            key=attrgetter('data'))
    
    return lista_operacoes

def buscar_totais_atuais_investimentos(investidor, data_atual=None):
    """
    Traz os totais de investimento do investidor em data especificada
    Parâmetros: Investidor
                Data
    Retorno: Totais atuais {investimento: total}
    """
    # Preparar data
    if data_atual == None:
        data_atual = datetime.date.today()
        
    totais_atuais = {'Ações': Decimal(0), 'CDB/RDB': Decimal(0), 'CRI/CRA': Decimal(0), 'Criptomoedas': Decimal(0), 'Debêntures': Decimal(0), 
                     'FII': Decimal(0), 'Fundos de Inv.': Decimal(0), 'LCI/LCA': Decimal(0), 'Outros inv.': Decimal(0), 
                     'Letras de Câmbio': Decimal(0),'Tesouro Direto': Decimal(0), }
    
    # Ações
    acoes_investidor = buscar_acoes_investidor_na_data(investidor, data_atual)
    # Cálculo de quantidade
#     for acao in Acao.objects.filter(id__in=acoes_investidor):
#         acao_qtd = quantidade_acoes_ate_dia(investidor, acao.ticker, data_atual, considerar_trade=True)
#         if acao_qtd > 0:
#             if ValorDiarioAcao.objects.filter(acao__ticker=acao.ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
#                 acao_valor = ValorDiarioAcao.objects.filter(acao__ticker=acao.ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_unitario
#             else:
#                 acao_valor = HistoricoAcao.objects.filter(acao__ticker=acao.ticker).order_by('-data')[0].preco_unitario
#             totais_atuais['Ações'] += (acao_qtd * acao_valor)
    lista_acoes = list(Acao.objects.filter(id__in=acoes_investidor))
    qtd_acoes = {acao.id: quantidade_acoes_ate_dia(investidor, acao.ticker, data_atual, considerar_trade=True) for acao in lista_acoes}
    lista_valores_diarios = ValorDiarioAcao.objects.filter(acao__in=lista_acoes, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('acao__id', '-data_hora').distinct('acao__id')
    lista_historicos = HistoricoAcao.objects.filter(acao__in=lista_acoes, data__lte=data_atual).order_by('acao__id', '-data').distinct('acao__id')
    lista_valores = {valor.acao_id: valor.preco_unitario for valor in lista_valores_diarios}
    for historico in lista_historicos:
        if historico.acao_id not in lista_valores.keys():
            lista_valores[historico.acao_id] = historico.preco_unitario
    totais_atuais['Ações'] += sum([qtd_acoes[acao_id] * lista_valores[acao_id] for acao_id in qtd_acoes.keys() if qtd_acoes[acao_id] > 0])
    totais_atuais['Ações'] += calcular_poupanca_prov_acao_ate_dia(investidor, data_atual)

    # CDB / RDB
    cdbs_rdbs = calcular_valor_cdb_rdb_ate_dia(investidor, data_atual)
    for total_cdb_rdb in cdbs_rdbs.values():
        totais_atuais['CDB/RDB'] += total_cdb_rdb
        
    # CRI / CRA
    cri_cra = qtd_cri_cra_ate_dia(investidor, data_atual)
    for cri_cra_id in cri_cra.keys():
        valor_atual = calcular_valor_um_cri_cra_na_data(CRI_CRA.objects.get(id=cri_cra_id, investidor=investidor)).quantize(Decimal('.01'))
        totais_atuais['CRI/CRA'] += (cri_cra[cri_cra_id] * valor_atual)
        
    # Criptomoedas
    qtd_criptomoedas = calcular_qtd_moedas_ate_dia(investidor, data_atual)
    moedas = Criptomoeda.objects.filter(id__in=qtd_criptomoedas.keys())
    # Buscar valor das criptomoedas em posse do investidor
    valores_criptomoedas = {valor_diario.criptomoeda.ticker: valor_diario.valor for valor_diario in ValorDiarioCriptomoeda.objects.filter(criptomoeda__in=moedas, moeda='BRL').select_related('criptomoeda')}
    for moeda in moedas:
        totais_atuais['Criptomoedas'] += qtd_criptomoedas[moeda.id] * valores_criptomoedas[moeda.ticker]
    
    # Debêntures
    debentures = calcular_qtd_debentures_ate_dia(investidor, data_atual)
    for debenture_id in debentures.keys():
        valor_atual = HistoricoValorDebenture.objects.filter(debenture__id=debenture_id).order_by('-data')[0].valor_total()
        totais_atuais['Debêntures'] += (debentures[debenture_id] * valor_atual)
        
    # Fundos de investimento imobiliário
    fiis = calcular_qtd_fiis_ate_dia(investidor, data_atual)
    # Buscar valores diários e históricos
    ultimos_valores_diarios = {ticker: valor for ticker, valor in \
                               ValorDiarioFII.objects.filter(fii__ticker__in=fiis, data_hora__date=datetime.date.today()).order_by('fii__id', '-data_hora') \
                               .distinct('fii__id').values_list('fii__ticker', 'preco_unitario')}    
    ultimos_historicos = {ticker: valor for ticker, valor in HistoricoFII.objects.filter(fii__ticker__in=fiis, data__lte=data_atual).order_by('fii__ticker', '-data') \
                          .distinct('fii__ticker').values_list('fii__ticker', 'preco_unitario')}
    
    for ticker in fiis:
        if ticker in ultimos_valores_diarios:
            totais_atuais['FII'] += (fiis[ticker] * ultimos_valores_diarios[ticker])
        else:
            totais_atuais['FII'] += (fiis[ticker] * ultimos_historicos[ticker])
    totais_atuais['FII'] += calcular_poupanca_prov_fii_ate_dia(investidor, data_atual)
        
    # Fundos de investimento
    fundo_investimento_valores = calcular_valor_fundos_investimento_ate_dia(investidor, data_atual)
    for valor in fundo_investimento_valores.values():
        totais_atuais['Fundos de Inv.'] += valor
            
    # Letras de crédito
    letras_cambio = calcular_valor_lc_ate_dia(investidor, data_atual)
    for total_lc in letras_cambio.values():
        totais_atuais['Letras de Câmbio'] += total_lc
            
    # Letras de crédito
    letras_credito = calcular_valor_lci_lca_ate_dia(investidor, data_atual)
    for total_lci_lca in letras_credito.values():
        totais_atuais['LCI/LCA'] += total_lci_lca
    
    # Outros investimentos
    outros_investimentos = calcular_valor_outros_investimentos_ate_data(investidor, data_atual)
    for valor_investimento in outros_investimentos.values():
        totais_atuais['Outros inv.'] += valor_investimento
    
    # Tesouro Direto
    titulos = quantidade_titulos_ate_dia(investidor, data_atual)
    for titulo_id in titulos.keys():
        if ValorDiarioTitulo.objects.filter(titulo__id=titulo_id, data_hora__date=data_atual).exists():
            td_valor = ValorDiarioTitulo.objects.filter(titulo__id=titulo_id, data_hora__date=data_atual).order_by('-data_hora')[0].preco_venda
        else:
            td_valor = HistoricoTitulo.objects.filter(titulo__id=titulo_id).order_by('-data')[0].preco_venda
        totais_atuais['Tesouro Direto'] += (titulos[titulo_id] * td_valor)
    
    # Arredondar todos os valores para 2 casas decimais
    for chave, valor in totais_atuais.items():
        totais_atuais[chave] = valor.quantize(Decimal('0.01'))
    
    return totais_atuais

def buscar_proventos_a_receber(investidor, fonte_provento=''):
    """
    Retorna proventos que o investidor irá receber futuramente, já passada a data EX
    Parâmetros: Investidor
                Fonte do provento ('F' = FII, 'A' = Ações, '' = Ambos)
    Retorno:    Lista de proventos
    """
    proventos_a_receber = list()
    
    data_atual = datetime.date.today()
    
    # Buscar proventos em ações
    if fonte_provento != 'F':
        acoes_investidor = buscar_acoes_investidor_na_data(investidor)
        
#         for acao in Acao.objects.filter(id__in=acoes_investidor):
        proventos_a_pagar = Provento.objects.filter(acao__id__in=acoes_investidor, data_ex__lte=data_atual, data_pagamento__gte=data_atual, tipo_provento__in=['D', 'J']).select_related('acao')
        for provento in proventos_a_pagar:
            qtd_acoes = quantidade_acoes_ate_dia(investidor, provento.acao.ticker, provento.data_ex - datetime.timedelta(days=1), considerar_trade=True) 
            if qtd_acoes > 0:
                provento.quantia_a_receber = (qtd_acoes * provento.valor_unitario) if provento.tipo_provento == 'D' else (qtd_acoes * provento.valor_unitario * Decimal(0.85))
                proventos_a_receber.append(provento)
          
    if fonte_provento != 'A':
        # Buscar proventos em FIIs          
        fiis_investidor = OperacaoFII.objects.filter(investidor=investidor, data__lte=datetime.date.today()).values_list('fii', flat=True)
        
        # Remover FIIs repetidos
        fiis_investidor = list(set(fiis_investidor))
        
#         for fii in FII.objects.filter(id__in=fiis_investidor):
        proventos_a_pagar = ProventoFII.objects.filter(fii__id__in=fiis_investidor, data_ex__lte=data_atual, data_pagamento__gte=data_atual).select_related('fii')
        for provento in proventos_a_pagar:
            qtd_fiis = calcular_qtd_fiis_ate_dia_por_ticker(investidor, provento.data_ex - datetime.timedelta(days=1), provento.fii.ticker)
            if qtd_fiis > 0:
                provento.quantia_a_receber = (qtd_fiis * provento.valor_unitario)
                proventos_a_receber.append(provento)
    
    # Arredondar valores
    for provento in proventos_a_receber:
        provento.quantia_a_receber = provento.quantia_a_receber.quantize(Decimal('0.01'))
     
    return proventos_a_receber

def buscar_proventos_a_receber_data_ex_futura(investidor):
    """
    Retorna proventos que o investidor irá receber futuramente, não passada a data EX
    Parâmetros: Investidor
    Retorno:    Lista de proventos
    """
    proventos_a_receber = list()
    
    acoes_investidor = buscar_acoes_investidor_na_data(investidor)
    
    data_atual = datetime.date.today()
    
#     for acao in Acao.objects.filter(id__in=acoes_investidor):
    proventos_a_pagar = Provento.objects.filter(acao__id__in=acoes_investidor, data_ex__gt=data_atual, tipo_provento__in=['D', 'J']).select_related('acao')
    for provento in proventos_a_pagar:
        qtd_acoes = quantidade_acoes_ate_dia(investidor, provento.acao.ticker, data_atual, considerar_trade=True) 
        if qtd_acoes > 0:
            provento.quantia_a_receber = (qtd_acoes * provento.valor_unitario) if provento.tipo_provento == 'D' else (qtd_acoes * provento.valor_unitario * Decimal(0.85))
            proventos_a_receber.append(provento)
          
    # Buscar proventos em FIIs          
    fiis_investidor = OperacaoFII.objects.filter(investidor=investidor, data__lte=datetime.date.today()).values_list('fii', flat=True)
    
    # Remover FIIs repetidos
    fiis_investidor = list(set(fiis_investidor))
    
#     for fii in FII.objects.filter(id__in=fiis_investidor):
    proventos_a_pagar = ProventoFII.objects.filter(fii__id__in=fiis_investidor, data_ex__gt=data_atual).select_related('fii')
    for provento in proventos_a_pagar:
        qtd_fiis = calcular_qtd_fiis_ate_dia_por_ticker(investidor, data_atual, provento.fii.ticker)
        if qtd_fiis > 0:
            provento.quantia_a_receber = (qtd_fiis * provento.valor_unitario)
            proventos_a_receber.append(provento)
    
    # Arredondar valores
    for provento in proventos_a_receber:
        provento.quantia_a_receber = provento.quantia_a_receber.quantize(Decimal('0.01'))
     
    return proventos_a_receber


def user_blocked(user):
    """ Testa se usuário está bloqueado """
    # Verifica se última tentativa foi feita a no máximo 10 minutos
    return (LoginIncorreto.objects.filter(user=user).count() >= 6 and 
        (timezone.now() - LoginIncorreto.objects.filter(user=user).order_by('-horario')[0].horario).total_seconds() < 10 * 60)
    