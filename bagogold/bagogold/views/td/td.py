# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoTDFormSet
from bagogold.bagogold.forms.td import OperacaoTituloForm
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD, Divisao
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.models.lc import LetraCredito, HistoricoTaxaDI
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic
from bagogold.bagogold.models.td import OperacaoTitulo, HistoricoTitulo, \
    ValorDiarioTitulo, Titulo, HistoricoIPCA
from bagogold.bagogold.utils.fii import \
    calcular_rendimento_proventos_fii_12_meses, \
    calcular_variacao_percentual_fii_por_periodo
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas
from bagogold.bagogold.utils.td import calcular_imposto_venda_td, \
    buscar_data_valor_mais_recente, quantidade_titulos_ate_dia, \
    quantidade_titulos_ate_dia_por_titulo, calcular_valor_td_ate_dia
from copy import deepcopy
from decimal import Decimal, ROUND_DOWN
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import F
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
import calendar
import datetime
import json
import math

@login_required
def buscar_titulos_validos_na_data(request):
    data = datetime.datetime.strptime(request.GET['dataEscolhida'], '%d/%m/%Y').date()
    tipo_operacao = request.GET['tipoOperacao']
    if tipo_operacao == 'C':
        lista_titulos_validos = list(Titulo.objects.filter(data_vencimento__gt=data).values_list('id', flat=True))
    else:
        lista_titulos_validos = list(quantidade_titulos_ate_dia(request.user.investidor, data).keys())
    return HttpResponse(json.dumps(lista_titulos_validos), content_type = "application/json") 

@adiciona_titulo_descricao('Acompanhamento de Tesouro Direto', 'Mostra o rendimento dos títulos do investidor '
    'para comparar com potenciais ganhos em outros investimentos')
def acompanhamento_td(request):
    # Objeto vazio para preenchimento
    class Object():
        pass
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'td/acompanhamento.html', {'titulos': {}, 'letras_credito': list(), 'fiis': list()})
    
    titulos = {}
    titulos_vendidos = {}
    
    for operacao in OperacaoTitulo.objects.filter(investidor=investidor).order_by('data'):
        # Verificar se se trata de compra
        if operacao.tipo_operacao == 'C':
            if operacao.titulo.id not in titulos.keys():
                titulos[operacao.titulo.id] = list()
                titulos_vendidos[operacao.titulo.id] = list()
            compra_titulo = Object()
            compra_titulo.nome = operacao.titulo.nome()
            compra_titulo.quantidade = operacao.quantidade
            compra_titulo.data = operacao.data
            compra_titulo.preco_unitario = operacao.preco_unitario 
            compra_titulo.total_gasto = operacao.quantidade * operacao.preco_unitario
            compra_titulo.data_vencimento = operacao.titulo.data_vencimento
            titulos[operacao.titulo.id].append(compra_titulo)
#             valor_atual = ValorDiarioTitulo.objects.filter(titulo__id=operacao.titulo.id).order_by('-data_hora')[0].preco_venda
#             print '%s comprado a %s valendo %s (%s (%s%%) de lucro)' % (operacao.titulo.nome(), operacao.preco_unitario, valor_atual, \
#                                                                       valor_atual - operacao.preco_unitario, (valor_atual - operacao.preco_unitario) / operacao.preco_unitario * 100)
        
        # Verificar se se trata de venda
        elif operacao.tipo_operacao == 'V':
#             print '%s vendido a %s' % (operacao.titulo.nome(), operacao.preco_unitario)
            lista_compras = titulos[operacao.titulo.id]
            lista_compras.sort(key=lambda x: x.preco_unitario)
            indice_operacao = 0
            while operacao.quantidade > 0:
                if lista_compras[indice_operacao].quantidade >= operacao.quantidade:
                    lista_compras[indice_operacao].quantidade -= operacao.quantidade
                    # Adicionar a titulos vendidos
                    venda_objeto = deepcopy(lista_compras[indice_operacao])
                    venda_objeto.quantidade = operacao.quantidade
                    venda_objeto.data_venda = operacao.data
                    venda_objeto.valor_atual = operacao.preco_unitario
                    venda_objeto.valor_taxas = operacao.taxa_bvmf + operacao.taxa_custodia
                    titulos_vendidos[operacao.titulo.id].append(venda_objeto)
                    break
                else:
                    operacao.quantidade -= lista_compras[indice_operacao].quantidade
                    # Adicionar a titulos vendidos
                    venda_objeto = deepcopy(lista_compras[indice_operacao])
                    venda_objeto.quantidade = lista_compras[indice_operacao].quantidade
                    venda_objeto.data_venda = operacao.data
                    venda_objeto.valor_atual = operacao.preco_unitario
                    # Apenas soma o valor da taxa na última venda
                    venda_objeto.valor_taxas = 0
                    titulos_vendidos[operacao.titulo.id].append(venda_objeto)
                    # Remover quantidade do título nas operações vigentes
                    lista_compras[indice_operacao].quantidade = 0
                    indice_operacao += 1
            # Remover aqueles que foram completamente vendidos
            lista_compras = [x for x in lista_compras if x.quantidade > 0]
            titulos[operacao.titulo.id] = lista_compras
    
    # Dados de títulos ainda em posse do usuario                
    for titulo in titulos.keys():
        # Carregar data de vencimento do título
        data_vencimento = Titulo.objects.get(id=titulo).data_vencimento
        for operacao in titulos[titulo]:
            try:
                operacao.valor_atual = ValorDiarioTitulo.objects.filter(titulo__id=titulo, data_hora__date=datetime.date.today()).order_by('-data_hora')[0].preco_venda
            except:
                operacao.valor_atual = HistoricoTitulo.objects.filter(titulo__id=titulo).order_by('-data')[0].preco_venda
            operacao.variacao = operacao.valor_atual - operacao.preco_unitario
            operacao.variacao_percentual = operacao.variacao / operacao.preco_unitario * 100
            # Definir quantidade de dias já passados, mínimo de 1 considerando uma operação de hoje
            qtd_dias = max((datetime.date.today() - operacao.data).days, 1)
            # Pegar a taxa diária
            operacao.variacao_percentual_mensal = math.pow(1 + operacao.variacao_percentual/100, float(1)/qtd_dias) - 1
            # Pegar a taxa mensal
            operacao.variacao_percentual_mensal = (math.pow(1 + operacao.variacao_percentual_mensal, 30) - 1) * 100
            # Pegar a taxa anual
            operacao.variacao_percentual_anual = (math.pow(1 + operacao.variacao_percentual_mensal/100, 12) - 1) * 100
            operacao.valor_total_atual = operacao.valor_atual * operacao.quantidade
            if operacao.valor_total_atual > operacao.total_gasto:
                operacao.lucro = operacao.valor_total_atual - operacao.total_gasto - calcular_imposto_venda_td(qtd_dias, operacao.valor_total_atual, operacao.valor_total_atual - operacao.total_gasto)
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
            else:
                operacao.lucro = operacao.valor_total_atual - operacao.total_gasto
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
            
            # Quantidade de dias esperado é a quantidade de dias entre a data atual e a data de vencimento
            qtd_dias_esperado = (data_vencimento - datetime.date.today()).days
            # Pegar quantidade de dias entre a compra e o vencimento
            qtd_dias_entre_compra_vencimento = qtd_dias + qtd_dias_esperado
            # Valor esperado é a quantidade que ainda vai render caso investidor espere até o dia do vencimento
            valor_esperado = (Decimal(1000) * operacao.quantidade) - calcular_imposto_venda_td(qtd_dias_entre_compra_vencimento, Decimal(1000) * operacao.quantidade, \
                                                                                               (Decimal(1000) * operacao.quantidade) - operacao.total_gasto) - (operacao.total_gasto + operacao.lucro)
            rendimento_esperado = math.pow(1 + (valor_esperado / (operacao.total_gasto + operacao.lucro) * 100)/100, float(1)/qtd_dias_esperado) - 1
            rendimento_esperado = (math.pow(1 + rendimento_esperado, 30) - 1) * 100
            operacao.rendimento_esperado = (math.pow(1 + rendimento_esperado/100, 12) - 1) * 100
    
    # Data de 12 meses atrás
    data_12_meses = datetime.date.today() - datetime.timedelta(days=365)

    letras_credito = list(LetraCredito.objects.filter(investidor=investidor))
    historico_di = HistoricoTaxaDI.objects.filter(data__range=[data_12_meses, datetime.date.today()]).values('taxa').annotate(qtd_dias=Count('taxa'))
    # Comparativo com letras de crédito
    for lc in letras_credito:
        # Calcular rendimento atual
        lc.taxa_atual = lc.porcentagem_di_atual()
        lc.rendimento_atual = calcular_valor_atualizado_com_taxas({HistoricoTaxaDI.objects.filter(data__isnull=False).order_by('-data')[0].taxa: 252}, Decimal(100),
                                                                  lc.taxa_atual).quantize(Decimal('.01'), ROUND_DOWN) - 100
        # Calcular rendimento real dos últimos 12 meses
        lc.rendimento_12_meses = 1000
        # Definir taxas dos dias para o cálculo
        taxas_dos_dias = {}
        for taxa_quantidade in historico_di:
            taxas_dos_dias[taxa_quantidade['taxa']] = taxa_quantidade['qtd_dias']

        # Calcular
        lc.rendimento_12_meses = calcular_valor_atualizado_com_taxas(taxas_dos_dias, lc.rendimento_12_meses, lc.taxa_atual).quantize(Decimal('.01'), ROUND_DOWN)
        lc.rendimento_12_meses = (lc.rendimento_12_meses - 1000) / 10
    letras_credito.sort(key=lambda x: x.rendimento_atual, reverse=True)
        
    fiis = list(FII.objects.all())
    for fii in fiis:
        fii.rendimento_prov = calcular_rendimento_proventos_fii_12_meses(fii)
        if fii.rendimento_prov > 0:
            fii.variacao_12_meses = calcular_variacao_percentual_fii_por_periodo(fii, data_12_meses, datetime.date.today())
#             print type(fii.rendimento_prov)
    fiis = [fii for fii in fiis if fii.rendimento_prov > 0]
    fiis.sort(key=lambda x: x.rendimento_prov, reverse=True)
    
    return TemplateResponse(request, 'td/acompanhamento.html', {'titulos': titulos, 'letras_credito': letras_credito, 'fiis': fiis})

@adiciona_titulo_descricao('Detalhar título do Tesouro Direto', 'Informações sobre um título do Tesouro Direto')
def detalhar_titulo_td(request, titulo_id):
    titulo = get_object_or_404(Titulo, id=titulo_id)
    
    # TODO pegar valores e taxas atuais do título, se não estiver fechado
    if not titulo.titulo_vencido():
        if ValorDiarioTitulo.objects.filter(titulo=titulo).exists():
            valores = ValorDiarioTitulo.objects.filter(titulo=titulo).order_by('-data_hora')[0]
            titulo.preco_compra = valores.preco_compra
            titulo.taxa_compra = valores.taxa_compra
            titulo.preco_venda = valores.preco_venda
            titulo.taxa_venda = valores.taxa_venda
        else:
            ultimo_valor_historico = HistoricoTitulo.objects.filter(titulo=titulo).order_by('-data')[0]
            titulo.preco_compra = ultimo_valor_historico.preco_compra
            titulo.taxa_compra = ultimo_valor_historico.taxa_compra
            titulo.preco_venda = ultimo_valor_historico.preco_venda
            titulo.taxa_venda = ultimo_valor_historico.taxa_venda
    
    data_final = datetime.date.today() if titulo.data_vencimento > datetime.date.today() else titulo.data_vencimento
    historico = HistoricoTitulo.objects.filter(titulo=titulo, data__gte=data_final.replace(year=data_final.year-1)).order_by('-data')
    
    dados = {'total_operacoes': 0, 'qtd_titulos_atual': Decimal(0), 'total_atual': Decimal(0), 'total_lucro': Decimal(0), 'lucro_percentual': Decimal(0)}
    if request.user.is_authenticated():
        investidor = request.user.investidor
        
        # TODO Considerar vendas parciais de titulos
        dados['total_operacoes'] = OperacaoTitulo.objects.filter(titulo=titulo, investidor=investidor).count()
        if not titulo.titulo_vencido():
            dados['qtd_titulos_atual'] = quantidade_titulos_ate_dia_por_titulo(investidor, titulo_id)
            dados['total_atual'] = dados['qtd_titulos_atual'] * titulo.preco_venda
            preco_medio = (OperacaoTitulo.objects.filter(titulo=titulo, investidor=investidor, tipo_operacao='C').annotate(valor_investido=F('quantidade') * F('preco_unitario')) \
                .aggregate(total_investido=Sum('valor_investido'))['total_investido'] or Decimal(0)) / (OperacaoTitulo.objects.filter(titulo=titulo, investidor=investidor, tipo_operacao='C') \
                .aggregate(total_titulos=Sum('quantidade'))['total_titulos'] or 1)
            dados['total_lucro'] = dados['total_atual'] - dados['qtd_titulos_atual'] * preco_medio
            dados['lucro_percentual'] = (titulo.preco_venda - preco_medio) / (preco_medio or 1) if dados['qtd_titulos_atual'] > 0 else 0
            # TODO Adicionar IR e IOF

    return TemplateResponse(request, 'td/detalhar_titulo.html', {'titulo': titulo, 'dados': dados, 'historico': historico})

@login_required
@adiciona_titulo_descricao('Editar operação em Tesouro Direto', 'Editar valores de uma operação de compra/venda em Tesouro Direto')
def editar_operacao_td(request, operacao_id):
    investidor = request.user.investidor
    
    operacao_td = get_object_or_404(OperacaoTitulo, id=operacao_id)
    # Verifica se a operação é do investidor, senão, jogar erro de permissão
    if operacao_td.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoTitulo, DivisaoOperacaoTD, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoTDFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_operacao_td = OperacaoTituloForm(request.POST, instance=operacao_td, investidor=investidor)
            formset_divisao = DivisaoFormSet(request.POST, instance=operacao_td, investidor=investidor) if varias_divisoes else None
            
            if form_operacao_td.is_valid():
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_td.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação alterada com sucesso')
                        return HttpResponseRedirect(reverse('td:historico_td'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                
                else:
                    operacao_td.save()
                    divisao_operacao = DivisaoOperacaoTD.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_td)
                    divisao_operacao.quantidade = operacao_td.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('td:historico_td'))
            for erro in [erro for erro in form_operacao_td.non_field_errors()]:
                messages.error(request, erro)
                    
        elif request.POST.get("delete"):
            # Verifica se, em caso de compra, a quantidade de títulos do investidor não fica negativa
            if operacao_td.tipo_operacao == 'C' and quantidade_titulos_ate_dia_por_titulo(investidor, operacao_td.titulo.id, datetime.date.today()) - operacao_td.quantidade < 0:
                messages.error(request, 'Operação de compra não pode ser apagada pois quantidade atual para o título %s seria negativa' % (operacao_td.titulo))
            else:
                divisao_td = DivisaoOperacaoTD.objects.filter(operacao=operacao_td)
                for divisao in divisao_td:
                    divisao.delete()
                operacao_td.delete()
                messages.success(request, 'Operação apagada com sucesso')
                return HttpResponseRedirect(reverse('td:historico_td'))

    else:
        form_operacao_td = OperacaoTituloForm(instance=operacao_td, investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=operacao_td, investidor=investidor)
            
    return TemplateResponse(request, 'td/editar_operacao_td.html', {'form_operacao_td': form_operacao_td, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})   

    
@adiciona_titulo_descricao('Histórico de Tesouro Direto', 'Histórico de operações de compra/venda em Tesouro Direto')
def historico_td(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'td/historico.html', {'dados': {}, 'operacoes': list(), 'graf_total_venc': list(),
                                                     'graf_gasto_total': list(), 'graf_patrimonio': list()})
    
    operacoes = OperacaoTitulo.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('data')  
    for operacao in operacoes:
        operacao.valor_unitario = operacao.preco_unitario
    
    qtd_titulos = {}
    total_gasto = 0
    total_patrimonio = 0
    
    # Gráfico de acompanhamento de gastos vs patrimonio
    graf_gasto_total = list()
    graf_patrimonio = list()
    graf_total_venc = list()
    
    for item in operacoes:          
        if isinstance(item, OperacaoTitulo):
            if item.titulo not in qtd_titulos.keys():
                qtd_titulos[item.titulo] = 0
            # Verificar se se trata de compra ou venda
            if item.tipo_operacao == 'C':
                item.tipo = 'Compra'
                item.total = -1 * (item.quantidade * item.preco_unitario + \
                item.taxa_bvmf + item.taxa_custodia)
                total_gasto += item.total
                qtd_titulos[item.titulo] += item.quantidade
                total_patrimonio = 0
                qtd_total_titulos = 0
                for titulo in qtd_titulos.keys():
                    qtd_total_titulos += qtd_titulos[titulo]
                    if not item.data == datetime.date.today():
                        total_patrimonio += (qtd_titulos[titulo] * HistoricoTitulo.objects.filter(data__lte=item.data, titulo=titulo).order_by('-data')[0].preco_venda)
                    else:
                        # Buscar valor mais atual de valor diário, se existir
                        if ValorDiarioTitulo.objects.filter(titulo=item.titulo, data_hora__date=item.data).order_by('-data_hora'):
                            valor_diario = ValorDiarioTitulo.objects.filter(titulo=item.titulo, data_hora__date=item.data).order_by('-data_hora')[0]
                            total_patrimonio += (qtd_titulos[titulo] * valor_diario.preco_venda)
                            break
                        else:
                            # Se não há valor diário, buscar histórico mais atual mesmo
                            total_patrimonio += (qtd_titulos[titulo] * HistoricoTitulo.objects.filter(titulo=titulo).order_by('-data')[0].preco_venda)
                
            elif item.tipo_operacao == 'V':
                item.tipo = 'Venda'
                item.total = (item.quantidade * item.preco_unitario - \
                item.taxa_bvmf - item.taxa_custodia)
                total_gasto += item.total
                qtd_titulos[item.titulo] -= item.quantidade
                total_patrimonio = 0
                qtd_total_titulos = 0
                for titulo in qtd_titulos.keys():
                    qtd_total_titulos += qtd_titulos[titulo]
                    if item.data is not datetime.date.today():
                        total_patrimonio += (qtd_titulos[titulo] * HistoricoTitulo.objects.filter(data__lte=item.data, titulo=titulo).order_by('-data')[0].preco_venda)
                    else:
                        # Buscar valor mais atual de valor diário, se existir
                        if ValorDiarioTitulo.objects.filter(titulo=item.titulo, data_hora__date=item.data).order_by('-data_hora'):
                            valor_diario = ValorDiarioTitulo.objects.filter(titulo=item.titulo, data_hora__date=item.data).order_by('-data_hora')[0]
                            total_patrimonio += (qtd_titulos[titulo] * valor_diario.preco_venda)
                            break
                        else:
                            # Se não há valor diário, buscar histórico mais atual mesmo
                            total_patrimonio += (qtd_titulos[titulo] * HistoricoTitulo.objects.filter(titulo=titulo).order_by('-data')[0].preco_venda)
        
        # Formatar data para inserir nos gráficos
        data_formatada = str(calendar.timegm(item.data.timetuple()) * 1000)        
        # Patrimônio
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_formatada:
            graf_patrimonio[len(graf_patrimonio)-1][1] = float(total_patrimonio)
        else:
            graf_patrimonio += [[data_formatada, float(total_patrimonio)]]
            
        # Total gasto
        if len(graf_gasto_total) > 0 and graf_gasto_total[-1][0] == data_formatada:
            graf_gasto_total[len(graf_gasto_total)-1][1] = float(-total_gasto)
        else:
            graf_gasto_total += [[data_formatada, float(-total_gasto)]]
            
        # Calcular o total a receber no vencimento com base nas quantidades
        total_vencimento_atual = 0
        for titulo in qtd_titulos.keys():
            if qtd_titulos[titulo] > 0:
#                 print titulo, titulo.valor_vencimento()
                total_vencimento_atual += qtd_titulos[titulo] * titulo.valor_vencimento(data=item.data)
        # Verifica se altera ultima posicao do grafico ou adiciona novo registro
        if len(graf_total_venc) > 0 and graf_total_venc[-1][0] == data_formatada:
            graf_total_venc[len(graf_total_venc)-1][1] = float(total_vencimento_atual)
        else:
            graf_total_venc += [[data_formatada, float(total_vencimento_atual)]]
            
    # Adicionar valor mais atual para todos os gráficos
    data_mais_atual_formatada = str(calendar.timegm(datetime.datetime.now().timetuple()) * 1000)  
    # Total gasto
    if len(graf_gasto_total) > 0 and graf_gasto_total[-1][0] == data_mais_atual_formatada:
        graf_gasto_total[len(graf_gasto_total)-1][1] = float(-total_gasto)
    else:
        graf_gasto_total += [[data_mais_atual_formatada, float(-total_gasto)]]
        
    patrimonio_atual = 0
    total_vencimento_atual = 0
    for titulo in qtd_titulos.keys():
        if qtd_titulos[titulo] > 0:
#             print '%s %s' % (titulo, qtd_titulos[titulo])
            # Calcular o patrimonio com base nas quantidades de títulos
            valores_diarios_titulo = ValorDiarioTitulo.objects.filter(titulo=titulo).order_by('-data_hora')
            if not valores_diarios_titulo or valores_diarios_titulo[0].data_hora.day != datetime.date.today().day:
                patrimonio_atual += (qtd_titulos[titulo] * HistoricoTitulo.objects.filter(titulo=titulo).order_by('-data')[0].preco_venda)
            else:
                patrimonio_atual += (qtd_titulos[titulo] * valores_diarios_titulo[0].preco_venda)
            
            # Calcular o total a receber no vencimento com base nas quantidades
            total_vencimento_atual += qtd_titulos[titulo] * titulo.valor_vencimento()
    # Patrimônio
    if len(graf_patrimonio) > 0 and graf_patrimonio[-1][0] == data_mais_atual_formatada:
        graf_patrimonio[len(graf_patrimonio)-1][1] = float(patrimonio_atual)
    else:
        graf_patrimonio += [[data_mais_atual_formatada, float(patrimonio_atual)]]
        
    # Total vencimento
    if len(graf_total_venc) > 0 and graf_total_venc[-1][0] == data_mais_atual_formatada:
        graf_total_venc[len(graf_total_venc)-1][1] = float(total_vencimento_atual)
    else:
        graf_total_venc += [[data_mais_atual_formatada, float(total_vencimento_atual)]]
        
    dados = {}
    dados['total_venc_atual'] = total_vencimento_atual
    dados['total_gasto'] = -total_gasto
    dados['patrimonio'] = patrimonio_atual
    dados['lucro'] = patrimonio_atual + total_gasto
    if total_gasto == 0:
        dados['lucro_percentual'] = 0
    else:
        dados['lucro_percentual'] = (patrimonio_atual + total_gasto) / -total_gasto * 100
    
    # Pegar valores correntes dos títulos no site do Tesouro
    
    return TemplateResponse(request, 'td/historico.html', {'dados': dados, 'operacoes': operacoes, 'graf_total_venc': graf_total_venc,
                                                     'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio})
    
    
@login_required
@adiciona_titulo_descricao('Inserir operação em Tesouro Direto', 'Inserir registro de operação de compra/venda em Tesouro Direto')
def inserir_operacao_td(request):
    investidor = request.user.investidor
    
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoTitulo, DivisaoOperacaoTD, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoTDFormSet)
    
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
    
    if request.method == 'POST':
        form_operacao_td = OperacaoTituloForm(request.POST, investidor=investidor)
        formset_divisao = DivisaoFormSet(request.POST, investidor=investidor) if varias_divisoes else None
        
        # Validar título
        if form_operacao_td.is_valid():
            operacao_td = form_operacao_td.save(commit=False)
            operacao_td.investidor = investidor
            
            # Testar se várias divisões
            if varias_divisoes:
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_td, investidor=investidor)
                if formset_divisao.is_valid():
                    operacao_td.save()
                    formset_divisao.save()
                    messages.success(request, 'Operação inserida com sucesso')
                    return HttpResponseRedirect(reverse('td:historico_td'))
                for erro in formset_divisao.non_form_errors():
                    messages.error(request, erro)
            else:
                operacao_td.save()
                divisao_operacao = DivisaoOperacaoTD(operacao=operacao_td, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_td.quantidade)
                divisao_operacao.save()
                messages.success(request, 'Operação inserida com sucesso')
                return HttpResponseRedirect(reverse('td:historico_td'))
            
        for erro in [erro for erro in form_operacao_td.non_field_errors()]:
            messages.error(request, erro)
                    
    else:
        form_operacao_td = OperacaoTituloForm(investidor=investidor)
        formset_divisao = DivisaoFormSet(investidor=investidor)
            
    return TemplateResponse(request, 'td/inserir_operacao_td.html', {'form_operacao_td': form_operacao_td, 'formset_divisao': formset_divisao,
                                                              'varias_divisoes': varias_divisoes})

@adiciona_titulo_descricao('Listar títulos do Tesouro Direto', 'Lista títulos que já foram, ou são, negociados no Tesouro Direto')
def listar_titulos_td(request):
    # TODO preparar filtros
    titulos = Titulo.objects.all()
    
    for titulo in titulos:
        if not titulo.titulo_vencido():
            if ValorDiarioTitulo.objects.filter(titulo=titulo).exists():
                valores = ValorDiarioTitulo.objects.filter(titulo=titulo).order_by('-data_hora')[0]
                titulo.preco_compra = valores.preco_compra
                titulo.taxa_compra = valores.taxa_compra
                titulo.preco_venda = valores.preco_venda
                titulo.taxa_venda = valores.taxa_venda
            else:
                ultimo_valor_historico = HistoricoTitulo.objects.filter(titulo=titulo).order_by('-data')[0]
                titulo.preco_compra = ultimo_valor_historico.preco_compra
                titulo.taxa_compra = ultimo_valor_historico.taxa_compra
                titulo.preco_venda = ultimo_valor_historico.preco_venda
                titulo.taxa_venda = ultimo_valor_historico.taxa_venda

    return TemplateResponse(request, 'td/listar_titulos.html', {'titulos': titulos})

@adiciona_titulo_descricao('Painel de Tesouro Direto', 'Mostra a posição atual do investidor em Tesouro Direto')
def painel(request):
    # Objeto vazio para preenchimento
    class Object():
        pass
    
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'td/painel.html', {'titulos': list(), 'titulos_vendidos': list(), 'dados': {}})
    
    titulos = {}
    titulos_vendidos = {}
    
    total_atual = 0
    total_lucro = 0
    
    for operacao in OperacaoTitulo.objects.filter(investidor=investidor).order_by('data'):
        # Verificar se se trata de compra
        if operacao.tipo_operacao == 'C':
            if operacao.titulo.id not in titulos.keys():
                titulos[operacao.titulo.id] = list()
                titulos_vendidos[operacao.titulo.id] = list()
            compra_titulo = Object()
            compra_titulo.nome = operacao.titulo.nome()
            compra_titulo.quantidade = operacao.quantidade
            compra_titulo.data = operacao.data
            compra_titulo.preco_unitario = operacao.preco_unitario 
            compra_titulo.total_gasto = operacao.quantidade * operacao.preco_unitario
            titulos[operacao.titulo.id].append(compra_titulo)
#             valor_atual = ValorDiarioTitulo.objects.filter(titulo__id=operacao.titulo.id).order_by('-data_hora')[0].preco_venda
#             print '%s comprado a %s valendo %s (%s (%s%%) de lucro)' % (operacao.titulo.nome(), operacao.preco_unitario, valor_atual, \
#                                                                       valor_atual - operacao.preco_unitario, (valor_atual - operacao.preco_unitario) / operacao.preco_unitario * 100)
        
        # Verificar se se trata de venda
        elif operacao.tipo_operacao == 'V':
#             print '%s vendido a %s' % (operacao.titulo.nome(), operacao.preco_unitario)
            lista_compras = titulos[operacao.titulo.id]
            lista_compras.sort(key=lambda x: x.preco_unitario)
            indice_operacao = 0
            while operacao.quantidade > 0:
                if lista_compras[indice_operacao].quantidade >= operacao.quantidade:
                    lista_compras[indice_operacao].quantidade -= operacao.quantidade
                    # Adicionar a titulos vendidos
                    venda_objeto = deepcopy(lista_compras[indice_operacao])
                    venda_objeto.quantidade = operacao.quantidade
                    venda_objeto.data_venda = operacao.data
                    venda_objeto.valor_atual = operacao.preco_unitario
                    venda_objeto.valor_taxas = operacao.taxa_bvmf + operacao.taxa_custodia
                    titulos_vendidos[operacao.titulo.id].append(venda_objeto)
                    break
                else:
                    operacao.quantidade -= lista_compras[indice_operacao].quantidade
                    # Adicionar a titulos vendidos
                    venda_objeto = deepcopy(lista_compras[indice_operacao])
                    venda_objeto.quantidade = lista_compras[indice_operacao].quantidade
                    venda_objeto.data_venda = operacao.data
                    venda_objeto.valor_atual = operacao.preco_unitario
                    # Apenas soma o valor da taxa na última venda
                    venda_objeto.valor_taxas = 0
                    titulos_vendidos[operacao.titulo.id].append(venda_objeto)
                    # Remover quantidade do título nas operações vigentes
                    lista_compras[indice_operacao].quantidade = 0
                    indice_operacao += 1
            # Remover aqueles que foram completamente vendidos
            lista_compras = [x for x in lista_compras if x.quantidade > 0]
            titulos[operacao.titulo.id] = lista_compras
    
    # Dados de títulos ainda em posse do usuario                
    for titulo in titulos.keys():
        for operacao in titulos[titulo]:
            try:
                operacao.valor_atual = ValorDiarioTitulo.objects.filter(titulo__id=titulo, data_hora__date=datetime.date.today()).order_by('-data_hora')[0].preco_venda
            except:
                operacao.valor_atual = HistoricoTitulo.objects.filter(titulo__id=titulo).order_by('-data')[0].preco_venda
            operacao.variacao = operacao.valor_atual - operacao.preco_unitario
            operacao.variacao_percentual = operacao.variacao / operacao.preco_unitario * 100
            # Definir quantidade de dias já passados, mínimo de 1 considerando uma operação de hoje
            qtd_dias = max((datetime.date.today() - operacao.data).days, 1)
            # Pegar a taxa diária
            operacao.variacao_percentual_mensal = math.pow(1 + operacao.variacao_percentual/100, float(1)/qtd_dias) - 1
            # Pegar a taxa mensal
            operacao.variacao_percentual_mensal = (math.pow(1 + operacao.variacao_percentual_mensal, 30) - 1) * 100
            # Pegar a taxa anual
            operacao.variacao_percentual_anual = (math.pow(1 + operacao.variacao_percentual_mensal/100, 12) - 1) * 100
            operacao.valor_total_atual = operacao.valor_atual * operacao.quantidade
            total_atual += operacao.valor_total_atual
            if operacao.valor_total_atual > operacao.total_gasto:
                operacao.lucro = (operacao.valor_total_atual - operacao.total_gasto) - calcular_imposto_venda_td(qtd_dias, operacao.valor_total_atual, operacao.valor_total_atual - operacao.total_gasto)
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
            else:
                operacao.lucro = operacao.valor_total_atual - operacao.total_gasto
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
#             print '%s: %s ao preço %s valendo %s (%s (%s%%) de lucro)' % (titulo, operacao.quantidade, operacao.preco_unitario, valor_atual, \
#                                                                     valor_atual - operacao.preco_unitario, (valor_atual - operacao.preco_unitario) / operacao.preco_unitario * 100)
            total_lucro += operacao.lucro
            
            
    # Dados de títulos vendidos
    for titulo in titulos_vendidos.keys():
        for operacao in titulos_vendidos[titulo]:
#             print titulo
            operacao.variacao = operacao.valor_atual - operacao.preco_unitario
            operacao.variacao_percentual = operacao.variacao / operacao.preco_unitario * 100
            # Definir quantidade de dias já passados, mínimo de 1 considerando uma operação de hoje
            qtd_dias = max((datetime.date.today() - operacao.data).days, 1)
#             print operacao.variacao_percentual
#             print qtd_dias
            # Pegar a taxa diária
            operacao.variacao_percentual_mensal = math.pow(1 + operacao.variacao_percentual/100, float(1)/qtd_dias) - 1
#             print operacao.variacao_percentual_mensal
            # Pegar a taxa mensal percentual
            operacao.variacao_percentual_mensal = (math.pow(1 + operacao.variacao_percentual_mensal, 30) - 1) * 100
#             print operacao.variacao_percentual_mensal
            # Pegar a taxa anual percentual
            operacao.variacao_percentual_anual = (math.pow(1 + operacao.variacao_percentual_mensal/100, 12) - 1) * 100
            operacao.valor_total_atual = operacao.valor_atual * operacao.quantidade
            if operacao.valor_total_atual > operacao.total_gasto:
                operacao.lucro = (operacao.valor_total_atual - operacao.total_gasto) - calcular_imposto_venda_td(qtd_dias, operacao.valor_total_atual, operacao.valor_total_atual - operacao.total_gasto)
                operacao.lucro -= operacao.valor_taxas
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
            else:
                operacao.lucro = operacao.valor_total_atual - operacao.total_gasto - operacao.valor_taxas
                operacao.lucro_percentual = operacao.lucro / operacao.total_gasto * 100
    
    # Popular dados
    dados = {}
    dados['total_atual'] = total_atual
    dados['total_lucro'] = total_lucro
    dados['data_valor_mais_recente'] = buscar_data_valor_mais_recente()
    
    return TemplateResponse(request, 'td/painel.html', {'titulos': titulos, 'titulos_vendidos': titulos_vendidos, 'dados': dados})

@adiciona_titulo_descricao('Sobre Tesouro Direto', 'Detalha o que são títulos do Tesouro Direto')
def sobre(request):
    data_atual = datetime.date.today()
    historico_ipca = HistoricoIPCA.objects.filter(ano__gte=(data_atual.year-3)).exclude(mes__lt=data_atual.month, ano=data_atual.year-3)
    graf_historico_ipca = [[str(calendar.timegm(valor_historico.data().timetuple()) * 1000), float(valor_historico.valor)] for valor_historico in historico_ipca]
    
    historico_selic = HistoricoTaxaSelic.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3))
    graf_historico_selic = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(pow(valor_historico.taxa_diaria, 252) - 1)*100] for valor_historico in historico_selic]
    
    if request.user.is_authenticated():
        total_atual = Decimal(sum(calcular_valor_td_ate_dia(request.user.investidor).values())).quantize(Decimal('0.01'))
    else:
        total_atual = 0
    
    ultima_data_hora_atualizacao = ValorDiarioTitulo.objects.all().order_by('-data_hora')[0].data_hora
    ultimos_valores = ValorDiarioTitulo.objects.filter(data_hora=ultima_data_hora_atualizacao)
    
    return TemplateResponse(request, 'td/sobre.html', {'graf_historico_ipca': graf_historico_ipca, 'graf_historico_selic': graf_historico_selic,
                                                       'total_atual': total_atual, 'ultimos_valores': ultimos_valores, 'ultima_data_hora_atualizacao': ultima_data_hora_atualizacao})