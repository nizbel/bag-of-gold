# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.cri_cra.forms.cri_cra import CRI_CRAForm, \
    DataRemuneracaoCRI_CRAForm, DataRemuneracaoCRI_CRAFormSet, \
    DataAmortizacaoCRI_CRAFormSet
from bagogold.cri_cra.models.cri_cra import CRI_CRA, DataRemuneracaoCRI_CRA, \
    DataAmortizacaoCRI_CRA
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, NON_FIELD_ERRORS
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
import datetime

TIPO_CRI = '1'
TIPO_CRA = '2'

@login_required
def detalhar_cri_cra(request, id_cri_cra):
    investidor = request.user.investidor
    
    cri_cra = CRI_CRA.objects.get(id=id_cri_cra)
    if cri_cra.investidor != investidor:
        raise PermissionDenied
    
#     historico_porcentagem = HistoricoPorcentagemCDB_RDB.objects.filter(cdb_rdb=cdb_rdb)
#     historico_carencia = HistoricoCarenciaCDB_RDB.objects.filter(cdb_rdb=cdb_rdb)
#     
#     # Inserir dados do investimento
#     if cdb_rdb.tipo == 'R':
#         cdb_rdb.tipo = 'RDB'
#     elif cdb_rdb.tipo == 'C':
#         cdb_rdb.tipo = 'CDB'
#     cdb_rdb.carencia_atual = cdb_rdb.carencia_atual()
#     cdb_rdb.porcentagem_atual = cdb_rdb.porcentagem_atual()
#     
#     # Preparar estatísticas zeradas
#     cdb_rdb.total_investido = Decimal(0)
#     cdb_rdb.saldo_atual = Decimal(0)
#     cdb_rdb.total_ir = Decimal(0)
#     cdb_rdb.total_iof = Decimal(0)
#     cdb_rdb.lucro = Decimal(0)
#     cdb_rdb.lucro_percentual = Decimal(0)
#     
#     operacoes = OperacaoCDB_RDB.objects.filter(investimento=cdb_rdb).order_by('data')
#     # Contar total de operações já realizadas 
#     cdb_rdb.total_operacoes = len(operacoes)
#     # Remover operacoes totalmente vendidas
#     operacoes = [operacao for operacao in operacoes if operacao.qtd_disponivel_venda() > 0]
#     if operacoes:
#         historico_di = HistoricoTaxaDI.objects.filter(data__range=[operacoes[0].data, datetime.date.today()])
#         for operacao in operacoes:
#             # Total investido
#             cdb_rdb.total_investido += operacao.qtd_disponivel_venda()
#             
#             # Saldo atual
#             taxas = historico_di.filter(data__gte=operacao.data).values('taxa').annotate(qtd_dias=Count('taxa'))
#             taxas_dos_dias = {}
#             for taxa in taxas:
#                 taxas_dos_dias[taxa['taxa']] = taxa['qtd_dias']
#             operacao.atual = calcular_valor_atualizado_com_taxas(taxas_dos_dias, operacao.qtd_disponivel_venda(), operacao.porcentagem())
#             cdb_rdb.saldo_atual += operacao.atual
#             
#             # Calcular impostos
#             qtd_dias = (datetime.date.today() - operacao.data).days
#             # IOF
#             operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.quantidade)
#             # IR
#             if qtd_dias <= 180:
#                 operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.quantidade - operacao.iof)
#             elif qtd_dias <= 360:
#                 operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.quantidade - operacao.iof)
#             elif qtd_dias <= 720:
#                 operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.quantidade - operacao.iof)
#             else: 
#                 operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.quantidade - operacao.iof)
#             cdb_rdb.total_ir += operacao.imposto_renda
#             cdb_rdb.total_iof += operacao.iof
#     
#         # Pegar outras estatísticas
#         str_auxiliar = str(cdb_rdb.saldo_atual.quantize(Decimal('.0001')))
#         cdb_rdb.saldo_atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#         
#         cdb_rdb.lucro = cdb_rdb.saldo_atual - cdb_rdb.total_investido
#         cdb_rdb.lucro_percentual = cdb_rdb.lucro / cdb_rdb.total_investido * 100
#     try: 
#         cdb_rdb.dias_proxima_retirada = (min(operacao.data + datetime.timedelta(days=operacao.carencia()) for operacao in operacoes if \
#                                              (operacao.data + datetime.timedelta(days=operacao.carencia())) > datetime.date.today()) - datetime.date.today()).days
#     except ValueError:
#         cdb_rdb.dias_proxima_retirada = 0
    
    
    return TemplateResponse(request, 'cdb_rdb/detalhar_cdb_rdb.html', {'cri_cra': cri_cra})

@login_required
def editar_cri_cra(request, id_cri_cra):
    investidor = request.user.investidor
    cri_cra = CRI_CRA.objects.get(pk=id_cri_cra)
    
    if cri_cra.investidor != investidor:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_cri_cra = CRI_CRAForm(request.POST, instance=cri_cra)
             
            if form_cri_cra.is_valid():
                cri_cra.save()
                messages.success(request, 'CRI/CRA editado com sucesso')
                return HttpResponseRedirect(reverse('detalhar_cri_cra', kwargs={'id': cri_cra.id}))
                 
        # TODO verificar o que pode acontecer na exclusão
        elif request.POST.get("delete"):
            cri_cra.delete()
            messages.success(request, 'CRI/CRA excluído com sucesso')
            return HttpResponseRedirect(reverse('listar_cri_cra'))
  
    else:
        form_cri_cra = CRI_CRAForm(instance=cri_cra)
            
    return TemplateResponse(request, 'cdb_rdb/editar_cri_cra.html', {'form_cri_cra': form_cri_cra})  
    
    
# @login_required
# def editar_operacao_cri_cra(request, id_cri_cra):
#     investidor = request.user.investidor
#     
#     operacao_cdb_rdb = OperacaoCDB_RDB.objects.get(pk=id)
#     if operacao_cdb_rdb.investidor != investidor:
#         raise PermissionDenied
#     
#     # Testa se investidor possui mais de uma divisão
#     varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
#     
#     # Preparar formset para divisoes
#     DivisaoFormSet = inlineformset_factory(OperacaoCDB_RDB, DivisaoOperacaoCDB_RDB, fields=('divisao', 'quantidade'),
#                                             extra=1, formset=DivisaoOperacaoCDB_RDBFormSet)
#     
#     if request.method == 'POST':
#         form_operacao_cdb_rdb = OperacaoCDB_RDBForm(request.POST, instance=operacao_cdb_rdb, investidor=investidor)
#         formset_divisao = DivisaoFormSet(request.POST, instance=operacao_cdb_rdb, investidor=investidor) if varias_divisoes else None
#         
#         if request.POST.get("save"):
#             if form_operacao_cdb_rdb.is_valid():
#                 operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
#                 formset_divisao = DivisaoFormSet(request.POST, instance=operacao_cdb_rdb, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
#                 if varias_divisoes:
#                     if formset_divisao.is_valid():
#                         operacao_cdb_rdb.save()
#                         if operacao_cdb_rdb.tipo_operacao == 'V':
#                             if not OperacaoVendaCDB_RDB.objects.filter(operacao_venda=operacao_cdb_rdb):
#                                 operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
#                                 operacao_venda_cdb_rdb.save()
#                             else: 
#                                 operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb)
#                                 if operacao_venda_cdb_rdb.operacao_compra != operacao_compra:
#                                     operacao_venda_cdb_rdb.operacao_compra = operacao_compra
#                                     operacao_venda_cdb_rdb.save()
#                         formset_divisao.save()
#                         messages.success(request, 'Operação editada com sucesso')
#                         return HttpResponseRedirect(reverse('historico_cdb_rdb'))
#                     for erro in formset_divisao.non_form_errors():
#                         messages.error(request, erro)
#                         
#                 else:
#                     operacao_cdb_rdb.save()
#                     if operacao_cdb_rdb.tipo_operacao == 'V':
#                         if not OperacaoVendaCDB_RDB.objects.filter(operacao_venda=operacao_cdb_rdb):
#                             operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
#                             operacao_venda_cdb_rdb.save()
#                         else: 
#                             operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb)
#                             if operacao_venda_cdb_rdb.operacao_compra != operacao_compra:
#                                 operacao_venda_cdb_rdb.operacao_compra = operacao_compra
#                                 operacao_venda_cdb_rdb.save()
#                     divisao_operacao = DivisaoOperacaoCDB_RDB.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_cdb_rdb)
#                     divisao_operacao.quantidade = operacao_cdb_rdb.quantidade
#                     divisao_operacao.save()
#                     messages.success(request, 'Operação editada com sucesso')
#                     return HttpResponseRedirect(reverse('historico_cdb_rdb'))
#             for erros in form_operacao_cdb_rdb.errors.values():
#                 for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
#                     messages.error(request, erro.message)
# #                         print '%s %s'  % (divisao_cdb_rdb.quantidade, divisao_cdb_rdb.divisao)
#                 
#         elif request.POST.get("delete"):
#             # Testa se operação a excluir não é uma operação de compra com vendas já registradas
#             if not OperacaoVendaCDB_RDB.objects.filter(operacao_compra=operacao_cdb_rdb):
#                 divisao_cdb_rdb = DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao_cdb_rdb)
#                 for divisao in divisao_cdb_rdb:
#                     divisao.delete()
#                 if operacao_cdb_rdb.tipo_operacao == 'V':
#                     OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb).delete()
#                 operacao_cdb_rdb.delete()
#                 messages.success(request, 'Operação excluída com sucesso')
#                 return HttpResponseRedirect(reverse('historico_cdb_rdb'))
#             else:
#                 messages.error(request, 'Não é possível excluir operação de compra que já tenha vendas registradas')
#  
#     else:
#         form_operacao_cdb_rdb = OperacaoCDB_RDBForm(instance=operacao_cdb_rdb, initial={'operacao_compra': operacao_cdb_rdb.operacao_compra_relacionada(),}, \
#                                                     investidor=investidor)
#         formset_divisao = DivisaoFormSet(instance=operacao_cdb_rdb, investidor=investidor)
#             
#     return TemplateResponse(request, 'cdb_rdb/editar_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})  

    
@login_required
def historico(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
#     operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
#     # Verifica se não há operações
#     if not operacoes:
#         return TemplateResponse(request, 'cdb_rdb/historico.html', {'dados': {}})
#     
#     # Prepara o campo valor atual
#     for operacao in operacoes:
#         operacao.atual = operacao.quantidade
#         if operacao.tipo_operacao == 'C':
#             operacao.tipo = 'Compra'
#             operacao.taxa = operacao.porcentagem()
#         else:
#             operacao.tipo = 'Venda'
#     
#     # Pegar data inicial
#     data_inicial = operacoes.order_by('data')[0].data
#     
#     # Pegar data final
#     data_final = max(HistoricoTaxaDI.objects.filter().order_by('-data')[0].data, datetime.date.today())
#     
#     data_iteracao = data_inicial
#     
#     total_gasto = 0
#     total_patrimonio = 0
#     
#     # Gráfico de acompanhamento de gastos vs patrimonio
#     graf_gasto_total = list()
#     graf_patrimonio = list()
# 
#     while data_iteracao <= data_final:
#         try:
#             taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
#         except:
#             taxa_do_dia = 0
#             
#         # Calcular o valor atualizado do patrimonio diariamente
#         total_patrimonio = 0
#         
#         # Processar operações
#         for operacao in operacoes:     
#             if (operacao.data <= data_iteracao):     
#                 # Verificar se se trata de compra ou venda
#                 if operacao.tipo_operacao == 'C':
#                         if (operacao.data == data_iteracao):
#                             operacao.total = operacao.quantidade
#                             total_gasto += operacao.total
#                         if taxa_do_dia > 0:
#                             # Calcular o valor atualizado para cada operacao
#                             operacao.atual = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa)
#                         # Arredondar na última iteração
#                         if (data_iteracao == data_final):
#                             str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
#                             operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#                         total_patrimonio += operacao.atual
#                         
#                 elif operacao.tipo_operacao == 'V':
#                     if (operacao.data == data_iteracao):
#                         operacao.total = operacao.quantidade
#                         total_gasto -= operacao.total
#                         # Remover quantidade da operação de compra
#                         operacao_compra_id = operacao.operacao_compra_relacionada().id
#                         for operacao_c in operacoes:
#                             if (operacao_c.id == operacao_compra_id):
#                                 # Configurar taxa para a mesma quantidade da compra
#                                 operacao.taxa = operacao_c.taxa
#                                 operacao.atual = (operacao.quantidade/operacao_c.quantidade) * operacao_c.atual
#                                 operacao_c.atual -= operacao.atual
#                                 str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
#                                 operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#                                 break
#                 
#         if len(operacoes.filter(data=data_iteracao)) > 0 or data_iteracao == data_final:
#             graf_gasto_total += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_gasto)]]
#             graf_patrimonio += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_patrimonio)]]
#         
#         # Proximo dia útil
#         proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
#         if len(proximas_datas) > 0:
#             data_iteracao = proximas_datas[0].data
#         elif data_iteracao < data_final:
#             data_iteracao = data_final
#         else:
#             break
# 
#     dados = {}
#     dados['total_gasto'] = total_gasto
#     dados['patrimonio'] = total_patrimonio
#     dados['lucro'] = total_patrimonio - total_gasto
#     dados['lucro_percentual'] = (total_patrimonio - total_gasto) / total_gasto * 100
#     
#     return TemplateResponse(request, 'cdb_rdb/historico.html', {'dados': dados, 'operacoes': operacoes, 
#                                                     'graf_gasto_total': graf_gasto_total, 'graf_patrimonio': graf_patrimonio})
    return TemplateResponse(request, 'cri_cra/historico.html', {})
    

@login_required
def inserir_cri_cra(request):
    investidor = request.user.investidor
    
    # Preparar formsets 
    DataRemuneracaoFormSet = inlineformset_factory(CRI_CRA, DataRemuneracaoCRI_CRA, fields=('data', 'cri_cra'), extra=1, can_delete=False,
                                                   formset=DataRemuneracaoCRI_CRAFormSet)
    DataAmortizacaoFormSet = inlineformset_factory(CRI_CRA, DataAmortizacaoCRI_CRA, form=LocalizedModelForm, fields=('data', 'percentual', 'cri_cra'),
                                                   extra=1, can_delete=False, formset=DataAmortizacaoCRI_CRAFormSet)
    amortizacao_integral_venc = False
    
    if request.method == 'POST':
        amortizacao_integral_venc = 'amortizacao_integral_venc' in request.POST.keys()
        print request.POST
        form_cri_cra = CRI_CRAForm(request.POST)
        formset_data_remuneracao = DataRemuneracaoFormSet(request.POST)
        formset_data_amortizacao = DataAmortizacaoFormSet(request.POST)
        if form_cri_cra.is_valid():
            try:
                with transaction.atomic():
                    cri_cra = form_cri_cra.save(commit=False)
                    cri_cra.investidor = investidor
                    cri_cra.save()
                    formset_data_remuneracao = DataRemuneracaoFormSet(request.POST, instance=cri_cra)
                    formset_data_amortizacao = DataAmortizacaoFormSet(request.POST, instance=cri_cra)
                    formset_data_remuneracao.forms[0].empty_permitted = False
                    if formset_data_remuneracao.is_valid():
                        if amortizacao_integral_venc:
                            formset_data_remuneracao.save()
                            messages.success(request, '%s criado com sucesso' % (cri_cra.descricao_tipo()))
                            return HttpResponseRedirect(reverse('cri_cra:listar_cri_cra'))
                        else:
                            formset_data_amortizacao = DataAmortizacaoFormSet(request.POST, instance=cri_cra)
                            formset_data_amortizacao.forms[0].empty_permitted = False
                            if formset_data_amortizacao.is_valid():
                                formset_data_remuneracao.save()
                                formset_data_amortizacao.save()
                                messages.success(request, '%s criado com sucesso' % (cri_cra.descricao_tipo()))
                                return HttpResponseRedirect(reverse('cri_cra:listar_cri_cra'))
                            
            except:
                # Erros de remuneração
                for erro in formset_data_remuneracao.non_form_errors():
                    messages.error(request, erro)
                # Erros de amortização
                for erro in formset_data_amortizacao.non_form_errors():
                    messages.error(request, erro)
        
        for erro in [erro for erro in form_cri_cra.non_field_errors()]:
            messages.error(request, erro)
            
    else:
        form_cri_cra = CRI_CRAForm()
        formset_data_remuneracao = DataRemuneracaoFormSet()
        formset_data_amortizacao = DataAmortizacaoFormSet()
    return TemplateResponse(request, 'cri_cra/inserir_cri_cra.html', {'form_cri_cra': form_cri_cra, 'formset_data_remuneracao': formset_data_remuneracao,
                                                                      'formset_data_amortizacao': formset_data_amortizacao, 'amortizacao_integral_venc': amortizacao_integral_venc})

@login_required
# def inserir_operacao_cri_cra(request):
#     investidor = request.user.investidor
#     
#     # Preparar formset para divisoes
#     DivisaoCDB_RDBFormSet = inlineformset_factory(OperacaoCDB_RDB, DivisaoOperacaoCDB_RDB, fields=('divisao', 'quantidade'), can_delete=False,
#                                             extra=1, formset=DivisaoOperacaoCDB_RDBFormSet)
#     
#     # Testa se investidor possui mais de uma divisão
#     varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
#     
#     if request.method == 'POST':
#         form_operacao_cdb_rdb = OperacaoCDB_RDBForm(request.POST, investidor=investidor)
#         formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(request.POST, investidor=investidor) if varias_divisoes else None
#         
#         # Validar CDB/RDB
#         if form_operacao_cdb_rdb.is_valid():
#             operacao_cdb_rdb = form_operacao_cdb_rdb.save(commit=False)
#             operacao_cdb_rdb.investidor = investidor
#             operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
#             formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(request.POST, instance=operacao_cdb_rdb, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
#                 
#             # Validar em caso de venda
#             if form_operacao_cdb_rdb.cleaned_data['tipo_operacao'] == 'V':
#                 operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
#                 # Caso de venda total do cdb/rdb
#                 if form_operacao_cdb_rdb.cleaned_data['quantidade'] == operacao_compra.quantidade:
#                     # Desconsiderar divisões inseridas, copiar da operação de compra
#                     operacao_cdb_rdb.save()
#                     for divisao_cdb_rdb in DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao_compra):
#                         divisao_cdb_rdb_venda = DivisaoOperacaoCDB_RDB(quantidade=divisao_cdb_rdb.quantidade, divisao=divisao_cdb_rdb.divisao, \
#                                                              operacao=operacao_cdb_rdb)
#                         divisao_cdb_rdb_venda.save()
#                     operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
#                     operacao_venda_cdb_rdb.save()
#                     messages.success(request, 'Operação inserida com sucesso')
#                     return HttpResponseRedirect(reverse('historico_cdb_rdb'))
#                 # Vendas parciais
#                 else:
#                     # Verificar se varias divisões
#                     if varias_divisoes:
#                         if formset_divisao_cdb_rdb.is_valid():
#                             operacao_cdb_rdb.save()
#                             formset_divisao_cdb_rdb.save()
#                             operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
#                             operacao_venda_cdb_rdb.save()
#                             messages.success(request, 'Operação inserida com sucesso')
#                             return HttpResponseRedirect(reverse('historico_cdb_rdb'))
#                         for erro in formset_divisao_cdb_rdb.non_form_errors():
#                                 messages.error(request, erro)
#                                 
#                     else:
#                         operacao_cdb_rdb.save()
#                         divisao_operacao = DivisaoOperacaoCDB_RDB(operacao=operacao_cdb_rdb, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_cdb_rdb.quantidade)
#                         divisao_operacao.save()
#                         operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
#                         operacao_venda_cdb_rdb.save()
#                         messages.success(request, 'Operação inserida com sucesso')
#                         return HttpResponseRedirect(reverse('historico_cdb_rdb'))
#             
#             # Compra
#             else:
#                 # Verificar se várias divisões
#                 if varias_divisoes:
#                     if formset_divisao_cdb_rdb.is_valid():
#                         operacao_cdb_rdb.save()
#                         formset_divisao_cdb_rdb.save()
#                         messages.success(request, 'Operação inserida com sucesso')
#                         return HttpResponseRedirect(reverse('historico_cdb_rdb'))
#                     for erro in formset_divisao_cdb_rdb.non_form_errors():
#                                 messages.error(request, erro)
#                                 
#                 else:
#                         operacao_cdb_rdb.save()
#                         divisao_operacao = DivisaoOperacaoCDB_RDB(operacao=operacao_cdb_rdb, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_cdb_rdb.quantidade)
#                         divisao_operacao.save()
#                         messages.success(request, 'Operação inserida com sucesso')
#                         return HttpResponseRedirect(reverse('historico_cdb_rdb'))
#                     
#         for erros in form_operacao_cdb_rdb.errors.values():
#             for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
#                 messages.error(request, erro.message)
#         for erro in formset_divisao_cdb_rdb.non_form_errors():
#             messages.error(request, erro)
# #                         print '%s %s'  % (divisao_cdb_rdb.quantidade, divisao_cdb_rdb.divisao)
#                 
#     else:
#         form_operacao_cdb_rdb = OperacaoCDB_RDBForm(investidor=investidor)
#         formset_divisao_cdb_rdb = DivisaoCDB_RDBFormSet(investidor=investidor)
#     return TemplateResponse(request, 'cdb_rdb/inserir_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cdb_rdb, 'formset_divisao_cdb_rdb': formset_divisao_cdb_rdb,
#                                                                         'varias_divisoes': varias_divisoes})

@login_required
def listar_cri_cra(request):
    investidor = request.user.investidor
    cri_cra = CRI_CRA.objects.filter(investidor=investidor)
    
    data_atual = datetime.date.today()
    for item in cri_cra:
        if DataRemuneracaoCRI_CRA.objects.filter(cri_cra=item, data__gt=data_atual).exists():
            item.proxima_data_remuneracao = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=item, data__gt=data_atual).order_by('data')[0].data
        else:
            item.proxima_data_remuneracao = None
    
    return TemplateResponse(request, 'cri_cra/listar_cri_cra.html', {'cri_cra': cri_cra})

@login_required
def painel(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
#     operacoes = OperacaoCDB_RDB.objects.filter(investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
#     if not operacoes:
#         dados = {}
#         dados['total_atual'] = Decimal(0)
#         dados['total_ir'] = Decimal(0)
#         dados['total_iof'] = Decimal(0)
#         dados['total_ganho_prox_dia'] = Decimal(0)
#         return TemplateResponse(request, 'cdb_rdb/painel.html', {'operacoes': {}})
#     
#     # Prepara o campo valor atual
#     for operacao in operacoes:
#         operacao.atual = operacao.quantidade
#         operacao.inicial = operacao.quantidade
#         if operacao.tipo_operacao == 'C':
#             operacao.tipo = 'Compra'
#             operacao.taxa = operacao.porcentagem()
#         else:
#             operacao.tipo = 'Venda'
#     
#     # Pegar data inicial
#     data_inicial = operacoes.order_by('data')[0].data
#     
#     # Pegar data final
#     data_final = HistoricoTaxaDI.objects.filter().order_by('-data')[0].data
#     
#     data_iteracao = data_inicial
#     
#     while data_iteracao <= data_final:
#         taxa_do_dia = HistoricoTaxaDI.objects.get(data=data_iteracao).taxa
#         
#         # Processar operações
#         for operacao in operacoes:     
#             if (operacao.data <= data_iteracao):     
#                 # Verificar se se trata de compra ou venda
#                 if operacao.tipo_operacao == 'C':
#                         # Calcular o valor atualizado para cada operacao
#                         operacao.atual = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa)
#                         # Arredondar na última iteração
#                         if (data_iteracao == data_final):
#                             str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
#                             operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#                         
#                 elif operacao.tipo_operacao == 'V':
#                     if (operacao.data == data_iteracao):
#                         operacao.inicial = operacao.quantidade
#                         # Remover quantidade da operação de compra
#                         operacao_compra_id = operacao.operacao_compra_relacionada().id
#                         for operacao_c in operacoes:
#                             if (operacao_c.id == operacao_compra_id):
#                                 # Configurar taxa para a mesma quantidade da compra
#                                 operacao.taxa = operacao_c.taxa
#                                 operacao.atual = (operacao.quantidade/operacao_c.quantidade) * operacao_c.atual
#                                 operacao_c.atual -= operacao.atual
#                                 operacao_c.inicial -= operacao.inicial
#                                 str_auxiliar = str(operacao.atual.quantize(Decimal('.0001')))
#                                 operacao.atual = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#                                 break
#                 
#         # Proximo dia útil
#         proximas_datas = HistoricoTaxaDI.objects.filter(data__gt=data_iteracao).order_by('data')
#         if len(proximas_datas) > 0:
#             data_iteracao = proximas_datas[0].data
#         else:
#             break
#     
#     # Remover operações que não estejam mais rendendo
#     operacoes = [operacao for operacao in operacoes if (operacao.atual > 0 and operacao.tipo_operacao == 'C')]
#     
#     total_atual = 0
#     total_ir = 0
#     total_iof = 0
#     total_ganho_prox_dia = 0
#     total_vencimento = 0
#     for operacao in operacoes:
#         # Calcular o ganho no dia seguinte, considerando taxa do dia anterior
#         operacao.ganho_prox_dia = calcular_valor_atualizado_com_taxa(taxa_do_dia, operacao.atual, operacao.taxa) - operacao.atual
#         str_auxiliar = str(operacao.ganho_prox_dia.quantize(Decimal('.0001')))
#         operacao.ganho_prox_dia = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#         total_ganho_prox_dia += operacao.ganho_prox_dia
#         
#         # Calcular impostos
#         qtd_dias = (datetime.date.today() - operacao.data).days
# #         print qtd_dias, calcular_iof_regressivo(qtd_dias)
#         # IOF
#         operacao.iof = Decimal(calcular_iof_regressivo(qtd_dias)) * (operacao.atual - operacao.inicial)
#         # IR
#         if qtd_dias <= 180:
#             operacao.imposto_renda =  Decimal(0.225) * (operacao.atual - operacao.inicial - operacao.iof)
#         elif qtd_dias <= 360:
#             operacao.imposto_renda =  Decimal(0.2) * (operacao.atual - operacao.inicial - operacao.iof)
#         elif qtd_dias <= 720:
#             operacao.imposto_renda =  Decimal(0.175) * (operacao.atual - operacao.inicial - operacao.iof)
#         else: 
#             operacao.imposto_renda =  Decimal(0.15) * (operacao.atual - operacao.inicial - operacao.iof)
#         
#         # Valor líquido
#         operacao.valor_liquido = operacao.atual - operacao.imposto_renda - operacao.iof
#         
#         # Estimativa para o valor do investimento na data de vencimento
#         qtd_dias_uteis_ate_vencimento = qtd_dias_uteis_no_periodo(data_final + datetime.timedelta(days=1), operacao.data_vencimento())
#         operacao.valor_vencimento = calcular_valor_atualizado_com_taxas({HistoricoTaxaDI.objects.get(data=data_final).taxa: qtd_dias_uteis_ate_vencimento},
#                                              operacao.atual, operacao.taxa)
#         str_auxiliar = str(operacao.valor_vencimento.quantize(Decimal('.0001')))
#         operacao.valor_vencimento = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#         
#         total_atual += operacao.atual
#         total_ir += operacao.imposto_renda
#         total_iof += operacao.iof
#         total_vencimento += operacao.valor_vencimento
#     
#     # Popular dados
#     dados = {}
#     dados['data_di_mais_recente'] = data_final
#     dados['total_atual'] = total_atual
#     dados['total_ir'] = total_ir
#     dados['total_iof'] = total_iof
#     dados['total_liquido'] = total_atual - total_ir - total_iof
#     dados['total_ganho_prox_dia'] = total_ganho_prox_dia
#     dados['total_vencimento'] = total_vencimento
#     
#     return TemplateResponse(request, 'cri_cra/painel.html', {'operacoes': operacoes, 'dados': dados})
    return TemplateResponse(request, 'cri_cra/painel.html', {})