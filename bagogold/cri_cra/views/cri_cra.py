# -*- coding: utf-8 -*-

from bagogold.bagogold.forms.divisoes import DivisaoOperacaoCRI_CRAFormSet
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoCRI_CRA
from bagogold.cri_cra.forms.cri_cra import CRI_CRAForm, \
    DataRemuneracaoCRI_CRAForm, DataRemuneracaoCRI_CRAFormSet, \
    DataAmortizacaoCRI_CRAFormSet, OperacaoCRI_CRAForm
from bagogold.cri_cra.models.cri_cra import CRI_CRA, DataRemuneracaoCRI_CRA, \
    DataAmortizacaoCRI_CRA, OperacaoCRI_CRA
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
import datetime
from bagogold.bagogold.models.lc import HistoricoTaxaDI

TIPO_CRI = '1'
TIPO_CRA = '2'

@login_required
def detalhar_cri_cra(request, id_cri_cra):
    investidor = request.user.investidor
    
    cri_cra = CRI_CRA.objects.get(id=id_cri_cra)
    if cri_cra.investidor != investidor:
        raise PermissionDenied
    
    datas_remuneracao = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cri_cra)
    datas_amortizacao = DataAmortizacaoCRI_CRA.objects.filter(cri_cra=cri_cra)
    if DataAmortizacaoCRI_CRA.objects.filter(cri_cra=cri_cra).exists():
        datas_amortizacao = DataAmortizacaoCRI_CRA.objects.filter(cri_cra=cri_cra)
    else:
        datas_amortizacao = [DataAmortizacaoCRI_CRA(cri_cra=cri_cra, data=cri_cra.data_vencimento, percentual=Decimal(100))]
    
    # Data pŕoxima remuneração
    if DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cri_cra, data__gt=datetime.date.today()).exists():
        cri_cra.proxima_data_remuneracao = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cri_cra, data__gt=datetime.date.today()).order_by('data')[0].data
    else:
        cri_cra.proxima_data_remuneracao = None
     
    # Preparar estatísticas zeradas
    cri_cra.total_investido = Decimal(0)
    cri_cra.saldo_atual = Decimal(0)
    cri_cra.total_ir = Decimal(0)
    cri_cra.total_iof = Decimal(0)
    cri_cra.lucro = Decimal(0)
    cri_cra.lucro_percentual = Decimal(0)
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
    
    
    return TemplateResponse(request, 'cri_cra/detalhar_cri_cra.html', {'cri_cra': cri_cra, 'datas_remuneracao': datas_remuneracao, 
                                                                       'datas_amortizacao': datas_amortizacao})

@login_required
def editar_cri_cra(request, id_cri_cra):
    investidor = request.user.investidor
    cri_cra = CRI_CRA.objects.get(pk=id_cri_cra)
    
    if cri_cra.investidor != investidor:
        raise PermissionDenied
    
    # Preparar formsets 
    DataRemuneracaoFormSet = inlineformset_factory(CRI_CRA, DataRemuneracaoCRI_CRA, fields=('data', 'cri_cra'), extra=1, validate_min=1,
                                                   formset=DataRemuneracaoCRI_CRAFormSet)
    DataAmortizacaoFormSet = inlineformset_factory(CRI_CRA, DataAmortizacaoCRI_CRA, form=LocalizedModelForm, fields=('data', 'percentual', 'cri_cra'),
                                                   extra=1, formset=DataAmortizacaoCRI_CRAFormSet)
    
    if request.method == 'POST':
        if request.POST.get("save"):
            amortizacao_integral_venc = 'amortizacao_integral_venc' in request.POST.keys()
            form_cri_cra = CRI_CRAForm(request.POST, instance=cri_cra)
            formset_data_remuneracao = DataRemuneracaoFormSet(request.POST, instance=cri_cra)
            formset_data_amortizacao = DataAmortizacaoFormSet(request.POST, instance=cri_cra)
            if form_cri_cra.is_valid():
                try:
                    with transaction.atomic():
                        cri_cra = form_cri_cra.save()
                        formset_data_remuneracao = DataRemuneracaoFormSet(request.POST, instance=cri_cra)
                        formset_data_amortizacao = DataAmortizacaoFormSet(request.POST, instance=cri_cra)
                        formset_data_remuneracao.forms[0].empty_permitted = False
                        if formset_data_remuneracao.is_valid():
                            if amortizacao_integral_venc:
                                formset_data_remuneracao.save()
                                # Verifica se foi marcado como amortização integral no vencimento porém já possuia amortizações anteriormente
                                if DataAmortizacaoCRI_CRA.objects.filter(cri_cra=cri_cra).exists():
                                    for data in DataAmortizacaoCRI_CRA.objects.filter(cri_cra=cri_cra).exists():
                                        data.delete()
                                
                                messages.success(request, '%s editado com sucesso' % (cri_cra.descricao_tipo()))
                                return HttpResponseRedirect(reverse('cri_cra:detalhar_cri_cra', kwargs={'id_cri_cra': cri_cra.id}))
                            else:
                                formset_data_amortizacao.forms[0].empty_permitted = False
                                if formset_data_amortizacao.is_valid():
                                    formset_data_remuneracao.save()
                                    formset_data_amortizacao.save()
                                    messages.success(request, '%s editado com sucesso' % (cri_cra.descricao_tipo()))
                                    return HttpResponseRedirect(reverse('cri_cra:detalhar_cri_cra', kwargs={'id_cri_cra': cri_cra.id}))
                        raise ValueError('Validações falharam')

                except:
                    pass
                # Erros de remuneração
                for erro in formset_data_remuneracao.non_form_errors():
                    messages.error(request, erro)
                # Erros de amortização
                for erro in formset_data_amortizacao.non_form_errors():
                    messages.error(request, erro)
                    
            for erro in [erro for erro in form_cri_cra.non_field_errors()]:
                messages.error(request, erro)
            
        # Pode excluir desde que não haja operações cadastradas para o investimento
        elif request.POST.get("delete"):
            if not OperacaoCRI_CRA.objects.filter(cri_cra=cri_cra).exists():
                for data in DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cri_cra):
                    data.delete()
                for data in DataAmortizacaoCRI_CRA.objects.filter(cri_cra=cri_cra):
                    data.delete()
                cri_cra.delete()
                messages.success(request, 'CRI/CRA excluído com sucesso')
                return HttpResponseRedirect(reverse('listar_cri_cra'))
            else:
                form_cri_cra = CRI_CRAForm(instance=cri_cra)
                formset_data_remuneracao = DataRemuneracaoFormSet(instance=cri_cra)
                formset_data_amortizacao = DataAmortizacaoFormSet(instance=cri_cra)
                messages.error(request, u'Não é possível excluir o %s pois já existem operações cadastradas' % (cri_cra.descricao_tipo()))
  
    else:
        form_cri_cra = CRI_CRAForm(instance=cri_cra)
        formset_data_remuneracao = DataRemuneracaoFormSet(instance=cri_cra)
        formset_data_amortizacao = DataAmortizacaoFormSet(instance=cri_cra)
    return TemplateResponse(request, 'cri_cra/editar_cri_cra.html', {'form_cri_cra': form_cri_cra, 'formset_data_remuneracao': formset_data_remuneracao,
                                                                      'formset_data_amortizacao': formset_data_amortizacao, 
                                                                      'amortizacao_integral_venc': cri_cra.amortizacao_integral_vencimento()})
    
    
@login_required
def editar_operacao_cri_cra(request, id_operacao):
    investidor = request.user.investidor
     
    operacao_cri_cra = OperacaoCRI_CRA.objects.get(pk=id_operacao)
    if operacao_cri_cra.cri_cra.investidor != investidor:
        raise PermissionDenied
     
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
     
    # Preparar formset para divisoes
    DivisaoFormSet = inlineformset_factory(OperacaoCRI_CRA, DivisaoOperacaoCRI_CRA, fields=('divisao', 'quantidade'),
                                            extra=1, formset=DivisaoOperacaoCRI_CRAFormSet)
     
    if request.method == 'POST':
        form_operacao_cri_cra = OperacaoCRI_CRAForm(request.POST, instance=operacao_cri_cra, investidor=investidor)
        formset_divisao = DivisaoFormSet(request.POST, instance=operacao_cri_cra, investidor=investidor) if varias_divisoes else None
         
        if request.POST.get("save"):
            if form_operacao_cri_cra.is_valid():
                operacao_compra = form_operacao_cdb_rdb.cleaned_data['operacao_compra']
                formset_divisao = DivisaoFormSet(request.POST, instance=operacao_cdb_rdb, operacao_compra=operacao_compra, investidor=investidor) if varias_divisoes else None
                if varias_divisoes:
                    if formset_divisao.is_valid():
                        operacao_cdb_rdb.save()
                        if operacao_cdb_rdb.tipo_operacao == 'V':
                            if not OperacaoVendaCDB_RDB.objects.filter(operacao_venda=operacao_cdb_rdb):
                                operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                                operacao_venda_cdb_rdb.save()
                            else: 
                                operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb)
                                if operacao_venda_cdb_rdb.operacao_compra != operacao_compra:
                                    operacao_venda_cdb_rdb.operacao_compra = operacao_compra
                                    operacao_venda_cdb_rdb.save()
                        formset_divisao.save()
                        messages.success(request, 'Operação editada com sucesso')
                        return HttpResponseRedirect(reverse('historico_cdb_rdb'))
                    for erro in formset_divisao.non_form_errors():
                        messages.error(request, erro)
                         
                else:
                    operacao_cdb_rdb.save()
                    if operacao_cdb_rdb.tipo_operacao == 'V':
                        if not OperacaoVendaCDB_RDB.objects.filter(operacao_venda=operacao_cdb_rdb):
                            operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB(operacao_compra=operacao_compra, operacao_venda=operacao_cdb_rdb)
                            operacao_venda_cdb_rdb.save()
                        else: 
                            operacao_venda_cdb_rdb = OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb)
                            if operacao_venda_cdb_rdb.operacao_compra != operacao_compra:
                                operacao_venda_cdb_rdb.operacao_compra = operacao_compra
                                operacao_venda_cdb_rdb.save()
                    divisao_operacao = DivisaoOperacaoCDB_RDB.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_cdb_rdb)
                    divisao_operacao.quantidade = operacao_cdb_rdb.quantidade
                    divisao_operacao.save()
                    messages.success(request, 'Operação editada com sucesso')
                    return HttpResponseRedirect(reverse('historico_cdb_rdb'))
            for erros in form_operacao_cdb_rdb.errors.values():
                for erro in [erro for erro in erros.data if not isinstance(erro, ValidationError)]:
                    messages.error(request, erro.message)
#                         print '%s %s'  % (divisao_cdb_rdb.quantidade, divisao_cdb_rdb.divisao)
                 
        elif request.POST.get("delete"):
            # Testa se operação a excluir não é uma operação de compra com vendas já registradas
            if not OperacaoVendaCDB_RDB.objects.filter(operacao_compra=operacao_cdb_rdb):
                divisao_cdb_rdb = DivisaoOperacaoCDB_RDB.objects.filter(operacao=operacao_cdb_rdb)
                for divisao in divisao_cdb_rdb:
                    divisao.delete()
                if operacao_cdb_rdb.tipo_operacao == 'V':
                    OperacaoVendaCDB_RDB.objects.get(operacao_venda=operacao_cdb_rdb).delete()
                operacao_cdb_rdb.delete()
                messages.success(request, 'Operação excluída com sucesso')
                return HttpResponseRedirect(reverse('historico_cdb_rdb'))
  
    else:
        form_operacao_cri_cra = OperacaoCRI_CRAForm(instance=operacao_cri_cra, investidor=investidor)
        formset_divisao = DivisaoFormSet(instance=operacao_cri_cra, investidor=investidor)
             
    return TemplateResponse(request, 'cdb_rdb/editar_operacao_cdb_rdb.html', {'form_operacao_cdb_rdb': form_operacao_cri_cra, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})  

    
@login_required
def historico(request):
    investidor = request.user.investidor
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor).exclude(data__isnull=True).order_by('data') 
    # Verifica se não há operações
    if not operacoes:
        return TemplateResponse(request, 'cri_cra/historico.html', {'dados': {}})
     
    # Prepara o campo valor atual
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
        else:
            operacao.tipo = 'Venda'
     
    # Pegar data inicial
    historico_di = HistoricoTaxaDI.objects.filter(data__gte=operacoes[0].data)
     
    total_investido = 0
    total_patrimonio = 0
     
    for operacao in operacoes:
        if operacao.tipo_operacao == 'C':
            total_investido += operacao.taxa + operacao.quantidade * operacao.preco_unitario
        if operacao.tipo_operacao == 'V':
            total_investido -= (operacao.quantidade * operacao.preco_unitario - operacao.taxa)
            
            
            
     
    # Gráfico de acompanhamento de investimentos vs patrimonio
    graf_investido_total = list()
    graf_patrimonio = list()
 
#             graf_investido_total += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_investido)]]
#             graf_patrimonio += [[str(calendar.timegm(data_iteracao.timetuple()) * 1000), float(total_patrimonio)]]
 
    dados = {}
    dados['total_investido'] = total_investido
    dados['patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio - total_investido
    dados['lucro_percentual'] = (total_patrimonio - total_investido) / total_investido * 100
     
    return TemplateResponse(request, 'cri_cra/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_investido_total': graf_investido_total, 'graf_patrimonio': graf_patrimonio})
    

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
                            formset_data_amortizacao.forms[0].empty_permitted = False
                            if formset_data_amortizacao.is_valid():
                                formset_data_remuneracao.save()
                                formset_data_amortizacao.save()
                                messages.success(request, '%s criado com sucesso' % (cri_cra.descricao_tipo()))
                                return HttpResponseRedirect(reverse('cri_cra:listar_cri_cra'))
                    raise ValueError('Validações falharam')

            except:
                pass
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
def inserir_operacao_cri_cra(request):
    investidor = request.user.investidor
     
    # Preparar formset para divisoes
    DivisaoCRI_CRAFormSet = inlineformset_factory(OperacaoCRI_CRA, DivisaoOperacaoCRI_CRA, fields=('divisao', 'quantidade'), can_delete=False,
                                            extra=1, formset=DivisaoOperacaoCRI_CRAFormSet)
     
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
     
    if request.method == 'POST':
        form_operacao_cri_cra = OperacaoCRI_CRAForm(request.POST, investidor=investidor)
        formset_divisao = DivisaoCRI_CRAFormSet(request.POST, investidor=investidor) if varias_divisoes else None
         
        # Validar CRI/CRA
        if form_operacao_cri_cra.is_valid():
            try:
                with transaction.atomic():
                    operacao_cri_cra = form_operacao_cri_cra.save(commit=False)
                    operacao_cri_cra.investidor = investidor
                    formset_divisao = DivisaoCRI_CRAFormSet(request.POST, instance=operacao_cri_cra, investidor=investidor) if varias_divisoes else None
                     
                    # Verificar se várias divisões
                    if varias_divisoes:
                        if formset_divisao.is_valid():
                            operacao_cri_cra.save()
                            formset_divisao.save()
                            messages.success(request, 'Operação inserida com sucesso')
                            return HttpResponseRedirect(reverse('cri_cra:historico_cri_cra'))
                        for erro in formset_divisao.non_form_errors():
                            messages.error(request, erro)
                                     
                    else:
                        operacao_cri_cra.save()
                        divisao_operacao = DivisaoOperacaoCRI_CRA(operacao=operacao_cri_cra, divisao=investidor.divisaoprincipal.divisao, quantidade=operacao_cri_cra.quantidade)
                        divisao_operacao.save()
                        messages.success(request, 'Operação inserida com sucesso')
                        return HttpResponseRedirect(reverse('cri_cra:historico_cri_cra'))
                    raise ValueError('Validações falharam')
            except:
                pass
                     
        for erro in [erro for erro in form_operacao_cri_cra.non_field_errors()]:
            messages.error(request, erro)
                  
    else:
        form_operacao_cri_cra = OperacaoCRI_CRAForm(investidor=investidor)
        formset_divisao = DivisaoCRI_CRAFormSet(investidor=investidor)
    return TemplateResponse(request, 'cri_cra/inserir_operacao_cri_cra.html', {'form_operacao_cri_cra': form_operacao_cri_cra, 'formset_divisao': formset_divisao,
                                                                         'varias_divisoes': varias_divisoes})

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