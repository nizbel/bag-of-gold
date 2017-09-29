# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao, ValorDiarioAcao, \
    HistoricoAcao, AcaoProvento, Acao, Provento
from bagogold.bagogold.models.debentures import HistoricoValorDebenture, \
    OperacaoDebenture
from bagogold.bagogold.models.fii import OperacaoFII, ValorDiarioFII, \
    HistoricoFII, FII, ProventoFII
from bagogold.bagogold.models.investidores import LoginIncorreto
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo, ValorDiarioTitulo, \
    HistoricoTitulo
from bagogold.bagogold.utils.acoes import quantidade_acoes_ate_dia, \
    calcular_poupanca_prov_acao_ate_dia
from bagogold.cdb_rdb.utils import calcular_valor_cdb_rdb_ate_dia
from bagogold.bagogold.utils.debenture import calcular_qtd_debentures_ate_dia
from bagogold.bagogold.utils.fii import calcular_qtd_fiis_ate_dia_por_ticker, \
    calcular_qtd_fiis_ate_dia, calcular_poupanca_prov_fii_ate_dia
from bagogold.bagogold.utils.lc import calcular_valor_lc_ate_dia
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia
from bagogold.cri_cra.models.cri_cra import CRI_CRA, OperacaoCRI_CRA
from bagogold.cri_cra.utils.utils import qtd_cri_cra_ate_dia
from bagogold.cri_cra.utils.valorizacao import calcular_valor_um_cri_cra_na_data
from bagogold.criptomoeda.models import Criptomoeda, OperacaoCriptomoeda
from bagogold.criptomoeda.utils import calcular_qtd_moedas_ate_dia, \
    buscar_valor_criptomoedas_atual
from bagogold.fundo_investimento.models import OperacaoFundoInvestimento
from bagogold.fundo_investimento.utils import \
    calcular_valor_fundos_investimento_ate_dia
from bagogold.outros_investimentos.models import Investimento
from bagogold.outros_investimentos.utils import \
    calcular_valor_outros_investimentos_ate_data
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from itertools import chain
from operator import attrgetter
import datetime


def is_superuser(user):
    if user.is_superuser:
        return True
    raise PermissionDenied

def buscar_acoes_investidor_na_data(investidor, data=datetime.date.today(), destinacao=''):
    """
    Busca as ações que o investidor possui na da especificada
    Parâmetros: Investidor
                Data da posição
                DestinaçãO (Buy and Hold, Trading ou ambos)
    Retorno: Lista com as ações que o investidor possui posição
    """
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
    from bagogold.cdb_rdb.models import OperacaoCDB_RDB
    """
    Busca as últimas operações feitas pelo investidor, ordenadas por data decrescente
    Parâmetros: Investidor
                Quantidade de operações a ser retornada
    Retorno: Lista com as operações ordenadas por data
    """
    # Juntar todas as operações em uma lista
    operacoes_fii = OperacaoFII.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    operacoes_td = OperacaoTitulo.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    operacoes_acoes = OperacaoAcao.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    operacoes_lc = OperacaoLetraCredito.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  
    operacoes_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  
    operacoes_cri_cra = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor).exclude(data__isnull=True).order_by('data')  
    operacoes_debentures = OperacaoDebenture.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  
    operacoes_fundo_investimento = OperacaoFundoInvestimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    outros_investimentos = Investimento.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')
    
    lista_operacoes = sorted(chain(operacoes_fii, operacoes_td, operacoes_acoes, operacoes_lc, operacoes_cdb_rdb, 
                                   operacoes_cri_cra, operacoes_debentures, operacoes_fundo_investimento, outros_investimentos),
                            key=attrgetter('data'), reverse=True)
    
    ultimas_operacoes = lista_operacoes[:min(quantidade_operacoes, len(lista_operacoes))]
    
    return ultimas_operacoes

def buscar_operacoes_no_periodo(investidor, data_inicial, data_final):
    from bagogold.cdb_rdb.models import OperacaoCDB_RDB
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
    operacoes_lc = OperacaoLetraCredito.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_cdb_rdb = OperacaoCDB_RDB.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_cri_cra = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_criptomoeda = OperacaoCriptomoeda.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    operacoes_debentures = OperacaoDebenture.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')  
    operacoes_fundo_investimento = OperacaoFundoInvestimento.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    outros_investimentos = Investimento.objects.filter(investidor=investidor, data__range=[data_inicial, data_final]).order_by('data')
    
    lista_operacoes = sorted(chain(operacoes_fii, operacoes_td, operacoes_acoes, operacoes_lc, operacoes_cdb_rdb, 
                                   operacoes_cri_cra, operacoes_criptomoeda, operacoes_debentures, operacoes_fundo_investimento, 
                                   outros_investimentos),
                            key=attrgetter('data'))
    
    return lista_operacoes

def buscar_totais_atuais_investimentos(investidor):
    totais_atuais = {'Ações': Decimal(0), 'CDB/RDB': Decimal(0), 'CRI/CRA': Decimal(0), 'Criptomoedas': Decimal(0), 'Debêntures': Decimal(0), 
                     'FII': Decimal(0), 'Fundos de Inv.': Decimal(0), 'Letras de Crédito': Decimal(0), 'Outros inv.': Decimal(0), 
                     'Tesouro Direto': Decimal(0), }
    
    data_atual = datetime.date.today()
    
    # Ações
    acoes_investidor = buscar_acoes_investidor_na_data(investidor)
    # Cálculo de quantidade
    for acao in Acao.objects.filter(id__in=acoes_investidor):
        acao_qtd = quantidade_acoes_ate_dia(investidor, acao.ticker, data_atual, considerar_trade=True)
        if acao_qtd > 0:
            if ValorDiarioAcao.objects.filter(acao__ticker=acao.ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
                acao_valor = ValorDiarioAcao.objects.filter(acao__ticker=acao.ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_unitario
            else:
                acao_valor = HistoricoAcao.objects.filter(acao__ticker=acao.ticker).order_by('-data')[0].preco_unitario
            totais_atuais['Ações'] += (acao_qtd * acao_valor)
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
    valores_criptomoedas = buscar_valor_criptomoedas_atual([moeda.ticker for moeda in moedas])
    for moeda in moedas:
        totais_atuais['Criptomoedas'] += qtd_criptomoedas[moeda.id] * valores_criptomoedas[moeda.ticker]
    
    # Debêntures
    debentures = calcular_qtd_debentures_ate_dia(investidor, data_atual)
    for debenture_id in debentures.keys():
        valor_atual = HistoricoValorDebenture.objects.filter(debenture__id=debenture_id).order_by('-data')[0].valor_total()
        totais_atuais['Debêntures'] += (debentures[debenture_id] * valor_atual)
        
    # Fundos de investimento imobiliário
    fiis = calcular_qtd_fiis_ate_dia(investidor, data_atual)
    for ticker in fiis.keys():
        if ValorDiarioFII.objects.filter(fii__ticker=ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).exists():
            fii_valor = ValorDiarioFII.objects.filter(fii__ticker=ticker, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_unitario
        else:
            fii_valor = HistoricoFII.objects.filter(fii__ticker=ticker).order_by('-data')[0].preco_unitario
        totais_atuais['FII'] += (fiis[ticker] * fii_valor)
    totais_atuais['FII'] += calcular_poupanca_prov_fii_ate_dia(investidor, data_atual)
        
    # Fundos de investimento
    fundo_investimento_valores = calcular_valor_fundos_investimento_ate_dia(investidor, data_atual)
    for valor in fundo_investimento_valores.values():
        totais_atuais['Fundos de Inv.'] += valor
            
    # Letras de crédito
    letras_credito = calcular_valor_lc_ate_dia(investidor, data_atual)
    for total_lc in letras_credito.values():
        totais_atuais['Letras de Crédito'] += total_lc
    
    # Outros investimentos
    outros_investimentos = calcular_valor_outros_investimentos_ate_data(investidor, data_atual)
    for valor_investimento in outros_investimentos.values():
        totais_atuais['Outros inv.'] += valor_investimento
    
    # Tesouro Direto
    titulos = quantidade_titulos_ate_dia(investidor, data_atual)
    for titulo_id in titulos.keys():
        try:
            td_valor = ValorDiarioTitulo.objects.filter(titulo__id=titulo_id, data_hora__day=data_atual.day, data_hora__month=data_atual.month).order_by('-data_hora')[0].preco_venda
        except:
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
    
    # Buscar proventos em ações
    if fonte_provento != 'F':
        acoes_investidor = buscar_acoes_investidor_na_data(investidor)
        
        data_atual = datetime.date.today()
        
        for acao in Acao.objects.filter(id__in=acoes_investidor):
            proventos_a_pagar = Provento.objects.filter(acao=acao, data_ex__lte=data_atual, data_pagamento__gte=data_atual, tipo_provento__in=['D', 'J'])
            for provento in proventos_a_pagar:
                qtd_acoes = quantidade_acoes_ate_dia(investidor, acao.ticker, provento.data_ex - datetime.timedelta(days=1), considerar_trade=True) 
                if qtd_acoes > 0:
                    provento.quantia_a_receber = (qtd_acoes * provento.valor_unitario) if provento.tipo_provento == 'D' else (qtd_acoes * provento.valor_unitario * Decimal(0.85))
                    proventos_a_receber.append(provento)
          
    if fonte_provento != 'A':
        # Buscar proventos em FIIs          
        fiis_investidor = OperacaoFII.objects.filter(investidor=investidor, data__lte=datetime.date.today()).values_list('fii', flat=True)
        
        # Remover FIIs repetidos
        fiis_investidor = list(set(fiis_investidor))
        
        for fii in FII.objects.filter(id__in=fiis_investidor):
            proventos_a_pagar = ProventoFII.objects.filter(fii=fii, data_ex__lte=data_atual, data_pagamento__gte=data_atual)
            for provento in proventos_a_pagar:
                qtd_fiis = calcular_qtd_fiis_ate_dia_por_ticker(investidor, provento.data_ex - datetime.timedelta(days=1), fii.ticker)
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
    
    for acao in Acao.objects.filter(id__in=acoes_investidor):
        proventos_a_pagar = Provento.objects.filter(acao=acao, data_ex__gt=data_atual, tipo_provento__in=['D', 'J'])
        for provento in proventos_a_pagar:
            qtd_acoes = quantidade_acoes_ate_dia(investidor, acao.ticker, data_atual, considerar_trade=True) 
            if qtd_acoes > 0:
                provento.quantia_a_receber = (qtd_acoes * provento.valor_unitario) if provento.tipo_provento == 'D' else (qtd_acoes * provento.valor_unitario * Decimal(0.85))
                proventos_a_receber.append(provento)
          
    # Buscar proventos em FIIs          
    fiis_investidor = OperacaoFII.objects.filter(investidor=investidor, data__lte=datetime.date.today()).values_list('fii', flat=True)
    
    # Remover FIIs repetidos
    fiis_investidor = list(set(fiis_investidor))
    
    for fii in FII.objects.filter(id__in=fiis_investidor):
        proventos_a_pagar = ProventoFII.objects.filter(fii=fii, data_ex__gt=data_atual)
        for provento in proventos_a_pagar:
            qtd_fiis = calcular_qtd_fiis_ate_dia_por_ticker(investidor, data_atual, fii.ticker)
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