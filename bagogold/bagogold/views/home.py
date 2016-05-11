# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao, HistoricoAcao, Provento, \
    ValorDiarioAcao
from bagogold.bagogold.models.fii import OperacaoFII, HistoricoFII, ProventoFII, \
    ValorDiarioFII
from bagogold.bagogold.models.lc import OperacaoLetraCredito, HistoricoTaxaDI
from bagogold.bagogold.models.td import OperacaoTitulo, HistoricoTitulo
from bagogold.bagogold.testTD import buscar_valores_diarios
from bagogold.bagogold.utils.lc import calcular_valor_lc_ate_dia
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from itertools import chain
from operator import attrgetter
import calendar
import datetime
import math

@login_required
def home(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    operacoes_fii = OperacaoFII.objects.exclude(data__isnull=True).order_by('data')
    if operacoes_fii:
        proventos_fii = ProventoFII.objects.exclude(data_ex__isnull=True).exclude(data_ex__gt=datetime.date.today()).filter(fii__in=operacoes_fii.values_list('fii', flat=True), data_ex__gt=operacoes_fii[0].data).order_by('data_ex')  
        for provento in proventos_fii:
            provento.data = provento.data_ex
    else:
        proventos_fii = list()
    
    operacoes_td = OperacaoTitulo.objects.exclude(data__isnull=True).order_by('data')
    
    operacoes_bh = OperacaoAcao.objects.filter(destinacao='B').exclude(data__isnull=True).order_by('data')
    proventos_bh = Provento.objects.exclude(data_ex__isnull=True).exclude(data_ex__gt=datetime.date.today()).filter(acao__in=operacoes_bh.values_list('acao', flat=True)).order_by('data_ex')
    for provento in proventos_bh:
        provento.data = provento.data_ex
        
    operacoes_lc = OperacaoLetraCredito.objects.exclude(data__isnull=True).order_by('data')  
    
    lista_operacoes = sorted(chain(proventos_fii, operacoes_fii, operacoes_td, proventos_bh,  operacoes_bh, operacoes_lc),
                            key=attrgetter('data'))
    # Pegar ano da primeira operacao feita
    ano_corrente = lista_operacoes[0].data.year
    
    datas_finais_ano = set()
    # Adicionar datas finais de cada ano
    for ano in range(ano_corrente, datetime.date.today().year):
        ultima_operacao = Object()
        ultima_operacao.data = datetime.date(ano, 12, 31)
        datas_finais_ano.add(ultima_operacao)
        
    # Adicionar data atual
    data_atual = Object()
    data_atual.data = datetime.date.today()
    datas_finais_ano.add(data_atual)
    
    # Adicionar datas para estatísticas
    datas_estatisticas = set()
    # Dia anterior
    data_dia_anterior = Object()
    data_dia_anterior.data = datetime.date.today() + datetime.timedelta(days=-1)
    data_dia_anterior.descricao = "1 dia"
    datas_estatisticas.add(data_dia_anterior)
    # 1 semana
    data_1_semana = Object()
    data_1_semana.data = datetime.date.today() + datetime.timedelta(days=-7)
    data_1_semana.descricao = "7 dias"
    datas_estatisticas.add(data_1_semana)
    # 30 dias
    data_30_dias = Object()
    data_30_dias.data = datetime.date.today() + datetime.timedelta(days=-30)
    data_30_dias.descricao = "30 dias"
    datas_estatisticas.add(data_30_dias)
    # 3 meses
    data_3_meses = Object()
    data_3_meses.data = datetime.date.today() + datetime.timedelta(days=-90)
    data_3_meses.descricao = "3 meses"
    datas_estatisticas.add(data_3_meses)
    # 1 semestre
    data_1_semestre = Object()
    data_1_semestre.data = datetime.date.today() + datetime.timedelta(days=-180)
    data_1_semestre.descricao = "1 semestre"
    datas_estatisticas.add(data_1_semestre)
    # 1 ano
    data_1_ano = Object()
    data_1_ano.data = datetime.date.today() + datetime.timedelta(days=-365)
    data_1_ano.descricao = "1 ano"
    datas_estatisticas.add(data_1_ano)
    
    lista_conjunta = sorted(chain(lista_operacoes, datas_finais_ano, datas_estatisticas),
                            key=attrgetter('data'))
    
    fii = {}
    acoes = {}
    titulos_td = {}
    letras_credito = {}
    total_proventos_fii = 0
    total_proventos_bh = 0
    
    patrimonio = {}
    patrimonio_anual = list()
    graf_patrimonio = list()
    estatisticas = list()
    
    for item in lista_conjunta:      
        # Atualizar lista de patrimonio atual ao trocar de ano
        if item.data.year != ano_corrente:
            if len(patrimonio_anual) > 0:
                diferenca = patrimonio['patrimonio_total'] - patrimonio_anual[len(patrimonio_anual) - 1][1]['patrimonio_total']
            else:
                diferenca = patrimonio['patrimonio_total']
            patrimonio_anual += [[ano_corrente, patrimonio, diferenca]]
            ano_corrente = item.data.year
        
        if isinstance(item, OperacaoAcao):  
            if item.acao.ticker not in acoes.keys():
                acoes[item.acao.ticker] = 0 
            if item.tipo_operacao == 'C':
                acoes[item.acao.ticker] += item.quantidade
                if len(item.usoproventosoperacaoacao_set.all()) > 0:
                    total_proventos_bh -= item.usoproventosoperacaoacao_set.all()[0].qtd_utilizada
                
            elif item.tipo_operacao == 'V':
                acoes[item.acao.ticker] -= item.quantidade
                total_venda = (item.quantidade * item.preco_unitario - \
                    item.emolumentos - item.corretagem)
                total_proventos_bh += total_venda
                
        elif isinstance(item, Provento):
            if item.data_pagamento <= datetime.date.today():
                if item.acao.ticker not in acoes.keys():
                    acoes[item.acao.ticker] = 0 
                if item.tipo_provento in ['D', 'J']:
                    total_recebido = acoes[item.acao.ticker] * item.valor_unitario
                    if item.acao.ticker == 'BBAS3':
                        print acoes[item.acao.ticker], item
                    if item.tipo_provento == 'J':
                        total_recebido = total_recebido * Decimal(0.85)
                    total_proventos_bh += total_recebido
                elif item.tipo_provento == 'A':
                    provento_acao = item.acaoprovento_set.all()[0]
                    if provento_acao.acao_recebida.ticker not in acoes.keys():
                        acoes[provento_acao.acao_recebida.ticker] = 0
                    acoes_recebidas = int((acoes[item.acao.ticker] * item.valor_unitario ) / 100 )
                    acoes[provento_acao.acao_recebida.ticker] += acoes_recebidas
                    if provento_acao.valor_calculo_frac > 0:
                        if provento_acao.data_pagamento_frac <= datetime.date.today():
                            total_proventos_bh += (((acoes[item.acao.ticker] * item.valor_unitario ) / 100 ) % 1 * provento_acao.valor_calculo_frac)
                
        elif isinstance(item, OperacaoTitulo):  
            if item.titulo not in titulos_td.keys():
                titulos_td[item.titulo] = 0
            if item.tipo_operacao == 'C':
                titulos_td[item.titulo] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                titulos_td[item.titulo] -= item.quantidade
                
        elif isinstance(item, OperacaoFII):
            if item.fii.ticker not in fii.keys():
                fii[item.fii.ticker] = 0    
            if item.tipo_operacao == 'C':
                fii[item.fii.ticker] += item.quantidade
                if len(item.usoproventosoperacaofii_set.all()) > 0:
                    total_proventos_fii -= float(item.usoproventosoperacaofii_set.all()[0].qtd_utilizada)
                
            elif item.tipo_operacao == 'V':
                fii[item.fii.ticker] -= item.quantidade
                
        elif isinstance(item, ProventoFII):
            if item.fii.ticker not in fii.keys():
                fii[item.fii.ticker] = 0    
            item.total = math.floor(fii[item.fii.ticker] * item.valor_unitario * 100) / 100
            total_proventos_fii += item.total
                
        elif isinstance(item, OperacaoLetraCredito):
            if item.letra_credito not in letras_credito.keys():
                letras_credito[item.letra_credito] = 0    
            if item.tipo_operacao == 'C':
                letras_credito[item.letra_credito] += item.quantidade
                
            elif item.tipo_operacao == 'V':
                letras_credito[item.letra_credito] -= item.quantidade
                
        # Se não cair em nenhum dos anteriores: item vazio para pegar ultimo dia util do ano
        patrimonio = {}
        patrimonio['patrimonio_total'] = 0

        # Rodar calculo de patrimonio
        # Acoes
        patrimonio['Ações'] = 0
        for acao in acoes.keys():
            # Verifica se valor foi preenchido com valor mais atual (válido apenas para data atual)
            preenchido = False
            if item.data == datetime.date.today():
                try:
                    valor_diario_mais_recente = ValorDiarioAcao.objects.filter(acao__ticker=acao).order_by('-data_hora')
                    if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
                        valor_acao = valor_diario_mais_recente[0].preco_unitario
                        preenchido = True
                except:
                    preenchido = False
            if (not preenchido):
                # Pegar último dia util com negociação da ação para calculo do patrimonio
                ultimo_dia_util = item.data
                while not HistoricoAcao.objects.filter(data=ultimo_dia_util, acao__ticker=acao):
                    ultimo_dia_util -= datetime.timedelta(days=1)
                valor_acao = HistoricoAcao.objects.get(acao__ticker=acao, data=ultimo_dia_util).preco_unitario
            patrimonio['Ações'] += (valor_acao * acoes[acao])
        patrimonio['patrimonio_total'] += patrimonio['Ações'] 
        
        # Proventos Acoes
        patrimonio['Proventos Ações'] = Decimal(int(total_proventos_bh * 100) / Decimal(100))
        patrimonio['patrimonio_total'] += patrimonio['Proventos Ações']
        
        # TD
        patrimonio['Tesouro Direto'] = 0
        for titulo in titulos_td.keys():
            if item.data is not datetime.date.today():
                ultimo_dia_util = item.data
                while not HistoricoTitulo.objects.filter(data=ultimo_dia_util, titulo=titulo):
                    ultimo_dia_util -= datetime.timedelta(days=1)
                patrimonio['Tesouro Direto'] += (titulos_td[titulo] * HistoricoTitulo.objects.get(data=ultimo_dia_util, titulo=titulo).preco_venda)
            else:
                for valor_diario in buscar_valores_diarios():
                    if valor_diario.titulo == titulo:
                        patrimonio['Tesouro Direto'] += (titulos_td[titulo] * valor_diario.preco_venda)
                        break
        patrimonio['patrimonio_total'] += patrimonio['Tesouro Direto'] 
            
        # FII
        patrimonio['FII'] = 0
        for papel in fii.keys():
            # Verifica se valor foi preenchido com valor mais atual (válido apenas para data atual)
            preenchido = False
            if item.data == datetime.date.today():
                try:
                    valor_diario_mais_recente = ValorDiarioFII.objects.filter(fii__ticker=papel).order_by('-data_hora')
                    if valor_diario_mais_recente and valor_diario_mais_recente[0].data_hora.date() == datetime.date.today():
                        valor_fii = valor_diario_mais_recente[0].preco_unitario
                        preenchido = True
                except:
                    preenchido= False
            if (not preenchido):
                # Pegar último dia util com negociação da ação para calculo do patrimonio
                ultimo_dia_util = item.data
                while not HistoricoFII.objects.filter(data=ultimo_dia_util, fii__ticker=papel):
                    ultimo_dia_util -= datetime.timedelta(days=1)
                valor_fii = HistoricoFII.objects.get(fii__ticker=papel, data=ultimo_dia_util).preco_unitario
            patrimonio['FII'] += (fii[papel] * valor_fii)
        patrimonio['patrimonio_total'] += patrimonio['FII']  
                
        # Proventos FII
        patrimonio['Proventos FII'] = Decimal(int(total_proventos_fii * 100) / Decimal(100))
        patrimonio['patrimonio_total'] += patrimonio['Proventos FII']
        
        # LC
        ultimo_dia_util = item.data
        while not HistoricoTaxaDI.objects.filter(data=ultimo_dia_util):
            ultimo_dia_util -= datetime.timedelta(days=1)
        patrimonio_lc = 0
        valores_letras_credito_dia = calcular_valor_lc_ate_dia(ultimo_dia_util)
        for valor in valores_letras_credito_dia.values():
            patrimonio_lc += valor
        patrimonio['Letras de Crédito'] = patrimonio_lc
        patrimonio['patrimonio_total'] += patrimonio['Letras de Crédito']
        
        # Preparar estatísticas
        for data_estatistica in datas_estatisticas:
            if item.data == data_estatistica.data: 
                if len(estatisticas) > 0 and estatisticas[len(estatisticas)-1][0] == data_estatistica.descricao:
                    estatisticas[len(estatisticas)-1] = [data_estatistica.descricao, float(patrimonio['patrimonio_total'])]
                else:
                    estatisticas += [[data_estatistica.descricao, float(patrimonio['patrimonio_total'])]]
             
        # Preparar data
        data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[len(graf_patrimonio)-1][0] == data_formatada:
            graf_patrimonio[len(graf_patrimonio)-1][1] = float(patrimonio['patrimonio_total'])
        else:
            graf_patrimonio += [[data_formatada, float(patrimonio['patrimonio_total'])]]
            
    # Adicionar ultimo valor ao dicionario de patrimonio anual
    if len(patrimonio_anual) > 0:
        diferenca = patrimonio['patrimonio_total'] - patrimonio_anual[len(patrimonio_anual) - 1][1]['patrimonio_total']
    else:
        diferenca = patrimonio['patrimonio_total']
    patrimonio_anual += [[ano_corrente, patrimonio, diferenca]]
    
    # Terminar estatísticas
    for index, estatistica in enumerate(estatisticas):
        estatisticas[index] = [estatistica[0], float(patrimonio['patrimonio_total']) - estatistica[1]]
            
    return render_to_response('home.html', {'graf_patrimonio': graf_patrimonio, 'patrimonio_anual': patrimonio_anual, 'estatisticas': estatisticas}, context_instance=RequestContext(request))