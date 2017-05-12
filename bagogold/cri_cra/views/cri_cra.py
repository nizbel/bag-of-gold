# -*- coding: utf-8 -*-

from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.divisoes import DivisaoOperacaoCRI_CRAFormSet
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.divisoes import Divisao, DivisaoOperacaoCRI_CRA
from bagogold.bagogold.models.lc import HistoricoTaxaDI
from bagogold.bagogold.models.taxas_indexacao import HistoricoTaxaSelic
from bagogold.bagogold.models.td import HistoricoIPCA
from bagogold.bagogold.utils.lc import calcular_valor_atualizado_com_taxas
from bagogold.bagogold.utils.misc import qtd_dias_uteis_no_periodo, \
    formatar_zeros_a_direita_apos_2_casas_decimais
from bagogold.cri_cra.forms.cri_cra import CRI_CRAForm, \
    DataRemuneracaoCRI_CRAForm, DataRemuneracaoCRI_CRAFormSet, \
    DataAmortizacaoCRI_CRAFormSet, OperacaoCRI_CRAForm
from bagogold.cri_cra.models.cri_cra import CRI_CRA, DataRemuneracaoCRI_CRA, \
    DataAmortizacaoCRI_CRA, OperacaoCRI_CRA
from bagogold.cri_cra.utils.utils import qtd_cri_cra_ate_dia_para_certificado, \
    calcular_valor_cri_cra_ate_dia
from bagogold.cri_cra.utils.valorizacao import calcular_valor_um_cri_cra_na_data
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
import calendar
import datetime

@login_required
@adiciona_titulo_descricao('Detalhar CRI/CRA', 'Detalha informações de rendimento e posição do investidor para um CRI/CRA')
def detalhar_cri_cra(request, id_cri_cra):
    investidor = request.user.investidor
    
    cri_cra = CRI_CRA.objects.get(id=id_cri_cra)
    if cri_cra.investidor != investidor:
        raise PermissionDenied
    
    # Formatar valor de emissão
    cri_cra.valor_emissao = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(cri_cra.valor_emissao))
    
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
     
    operacoes = OperacaoCRI_CRA.objects.filter(cri_cra=cri_cra).order_by('data').annotate(valor_operacao=F('preco_unitario')*F('quantidade'))
    # Preparar estatísticas zeradas
    cri_cra.total_investido = operacoes.filter(tipo_operacao='C') \
        .aggregate(valor_total=Sum('valor_operacao'))['valor_total'] or Decimal(0)
    cri_cra.valor_atual = calcular_valor_um_cri_cra_na_data(cri_cra)
    cri_cra.total_atual = quantidade_cri_cra_na_data_para_certificado(cri_cra) * cri_cra.valor_atual
    cri_cra.total_vendas = operacoes.filter(tipo_operacao='V') \
        .aggregate(valor_total=Sum('valor_operacao'))['valor_total'] or Decimal(0)
    cri_cra.total_taxas = operacoes.aggregate(total_taxas=Sum('taxa'))['total_taxas'] or Decimal(0)
    cri_cra.lucro = cri_cra.total_atual + cri_cra.total_vendas - cri_cra.total_investido - cri_cra.total_taxas
    cri_cra.lucro_percentual = Decimal(0) if cri_cra.total_investido == Decimal(0) else \
        cri_cra.lucro / cri_cra.total_investido
     
    # Contar total de operações já realizadas 
    cri_cra.total_operacoes = len(operacoes)
    
    # TODO preencher estatísticas totais
    
    return TemplateResponse(request, 'cri_cra/detalhar_cri_cra.html', {'cri_cra': cri_cra, 'datas_remuneracao': datas_remuneracao, 
                                                                       'datas_amortizacao': datas_amortizacao})

@login_required
@adiciona_titulo_descricao('Editar CRI/CRA', 'Altera dados de um CRI/CRA')
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
                        cri_cra = form_cri_cra.save(commit=False)
                        formset_data_remuneracao = DataRemuneracaoFormSet(request.POST, instance=cri_cra)
                        formset_data_amortizacao = DataAmortizacaoFormSet(request.POST, instance=cri_cra)
                        formset_data_remuneracao.forms[0].empty_permitted = False
                        if formset_data_remuneracao.is_valid():
                            if amortizacao_integral_venc:
                                cri_cra.save()
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
                                    cri_cra.save()
                                    formset_data_remuneracao.save()
                                    formset_data_amortizacao.save()
                                    messages.success(request, '%s editado com sucesso' % (cri_cra.descricao_tipo()))
                                    return HttpResponseRedirect(reverse('cri_cra:detalhar_cri_cra', kwargs={'id_cri_cra': cri_cra.id}))

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
                try:
                    with transaction.atomic():
                        for data in DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cri_cra):
                            data.delete()
                        for data in DataAmortizacaoCRI_CRA.objects.filter(cri_cra=cri_cra):
                            data.delete()
                        cri_cra.delete()
                        messages.success(request, 'CRI/CRA excluído com sucesso')
                        return HttpResponseRedirect(reverse('cri_cra:listar_cri_cra'))
                except:
                    form_cri_cra = CRI_CRAForm(instance=cri_cra)
                    formset_data_remuneracao = DataRemuneracaoFormSet(instance=cri_cra)
                    formset_data_amortizacao = DataAmortizacaoFormSet(instance=cri_cra)
                    messages.error(request, 'Houve um erro na exclusão')
            else:
                form_cri_cra = CRI_CRAForm(instance=cri_cra)
                formset_data_remuneracao = DataRemuneracaoFormSet(instance=cri_cra)
                formset_data_amortizacao = DataAmortizacaoFormSet(instance=cri_cra)
                messages.error(request, 'Não é possível excluir o %s pois já existem operações cadastradas' % (cri_cra.descricao_tipo()))
  
    else:
        form_cri_cra = CRI_CRAForm(instance=cri_cra)
        formset_data_remuneracao = DataRemuneracaoFormSet(instance=cri_cra)
        formset_data_amortizacao = DataAmortizacaoFormSet(instance=cri_cra)
    return TemplateResponse(request, 'cri_cra/editar_cri_cra.html', {'form_cri_cra': form_cri_cra, 'formset_data_remuneracao': formset_data_remuneracao,
                                                                      'formset_data_amortizacao': formset_data_amortizacao, 
                                                                      'amortizacao_integral_venc': cri_cra.amortizacao_integral_vencimento()})
    
    
@login_required
@adiciona_titulo_descricao('Editar operação em CRI/CRA', 'Altera valores de uma operação de compra/venda em CRI/CRA')
def editar_operacao_cri_cra(request, id_operacao):
    investidor = request.user.investidor
      
    operacao_cri_cra = OperacaoCRI_CRA.objects.get(pk=id_operacao)
    if operacao_cri_cra.cri_cra.investidor != investidor:
        raise PermissionDenied
      
    # Testa se investidor possui mais de uma divisão
    varias_divisoes = len(Divisao.objects.filter(investidor=investidor)) > 1
      
    # Preparar formset para divisoes
    DivisaoCRI_CRAFormSet = inlineformset_factory(OperacaoCRI_CRA, DivisaoOperacaoCRI_CRA, form=LocalizedModelForm, fields=('divisao', 'quantidade'),
                                            extra=0, formset=DivisaoOperacaoCRI_CRAFormSet)
      
    if request.method == 'POST':
        form_operacao_cri_cra = OperacaoCRI_CRAForm(request.POST, instance=operacao_cri_cra, investidor=investidor)
        formset_divisao = DivisaoCRI_CRAFormSet(request.POST, instance=operacao_cri_cra, investidor=investidor) if varias_divisoes else None
          
        if request.POST.get("save"):
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
                                messages.success(request, 'Operação editada com sucesso')
                                return HttpResponseRedirect(reverse('cri_cra:historico_cri_cra'))
                            for erro in formset_divisao.non_form_errors():
                                messages.error(request, erro)
                              
                        else:
                            operacao_cri_cra.save()
                            divisao_operacao = DivisaoOperacaoCRI_CRA.objects.get(divisao=investidor.divisaoprincipal.divisao, operacao=operacao_cri_cra)
                            divisao_operacao.quantidade = operacao_cri_cra.quantidade
                            divisao_operacao.save()
                            messages.success(request, 'Operação editada com sucesso')
                            return HttpResponseRedirect(reverse('cri_cra:historico_cri_cra'))
                except:
                    pass
                         
            for erro in [erro for erro in form_operacao_cri_cra.non_field_errors()]:
                messages.error(request, erro)
                  
        elif request.POST.get("delete"):
            # Testa se operação a excluir não deixará operações de venda excedendo a posição do investidor
            if operacao_cri_cra.tipo_operacao == 'V' or qtd_cri_cra_ate_dia_para_certificado(operacao_cri_cra.cri_cra) - operacao_cri_cra.quantidade > 0:
                try:
                    with transaction.atomic():
                        divisao_cri_cra = DivisaoOperacaoCRI_CRA.objects.filter(operacao=operacao_cri_cra)
                        for divisao in divisao_cri_cra:
                            divisao.delete()
                        operacao_cri_cra.delete()
                        messages.success(request, 'Operação excluída com sucesso')
                        return HttpResponseRedirect(reverse('cri_cra:historico_cri_cra'))
                except:
                    form_operacao_cri_cra = OperacaoCRI_CRAForm(instance=operacao_cri_cra, investidor=investidor)
                    formset_divisao = DivisaoFormSet(instance=operacao_cri_cra, investidor=investidor)
                    messages.error(request, 'Houve um erro na exclusão')
            else:
                form_operacao_cri_cra = OperacaoCRI_CRAForm(instance=operacao_cri_cra, investidor=investidor)
                formset_divisao = DivisaoFormSet(instance=operacao_cri_cra, investidor=investidor)
                messages.error(request, 'Operação não pode ser excluída pois posição do investidor no %s seria negativa' % (operacao_cri_cra.cri_cra.descricao_tipo()))
   
    else:
        form_operacao_cri_cra = OperacaoCRI_CRAForm(instance=operacao_cri_cra, investidor=investidor)
        formset_divisao = DivisaoCRI_CRAFormSet(instance=operacao_cri_cra, investidor=investidor)
              
    return TemplateResponse(request, 'cri_cra/editar_operacao_cri_cra.html', {'form_operacao_cri_cra': form_operacao_cri_cra, 'formset_divisao': formset_divisao, 'varias_divisoes': varias_divisoes})  

    
@adiciona_titulo_descricao('Histórico de CRI/CRA', 'Histórico de operações de compra/venda em CRI/CRA')
def historico(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'cri_cra/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
        
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor).exclude(data__isnull=True).order_by('data') 
    # Verifica se não há operações
    if not operacoes:
        return TemplateResponse(request, 'cri_cra/historico.html', {'dados': {}, 'operacoes': list(), 
                                                    'graf_investido_total': list(), 'graf_patrimonio': list()})
     
    # Pegar data inicial
    historico_di = HistoricoTaxaDI.objects.filter(data__gte=operacoes[0].data)
     
    total_investido = 0
     
    # Gráfico de acompanhamento de investimentos vs patrimonio
    graf_investido_total = list()
    graf_patrimonio = list()
    
    qtd_certificados = {}
    
    for operacao in operacoes:
        if operacao.cri_cra not in qtd_certificados.keys():
            qtd_certificados[operacao.cri_cra] = 0
        
        total_patrimonio = 0
        
        if operacao.tipo_operacao == 'C':
            operacao.tipo = 'Compra'
            operacao.total = -(operacao.taxa + operacao.quantidade * operacao.preco_unitario)
            total_investido += operacao.total
            qtd_certificados[operacao.cri_cra] += operacao.quantidade
        
        elif operacao.tipo_operacao == 'V':
            operacao.tipo = 'Venda'
            operacao.total = (operacao.quantidade * operacao.preco_unitario - operacao.taxa)
            total_investido -= operacao.total
            qtd_certificados[operacao.cri_cra] -= operacao.quantidade
        
        for cri_cra in qtd_certificados.keys():
            if qtd_certificados[cri_cra] > 0:
                total_patrimonio += qtd_certificados[cri_cra] * calcular_valor_um_cri_cra_na_data(operacao.cri_cra, operacao.data)
        
        graf_investido_total += [[str(calendar.timegm(operacao.data.timetuple()) * 1000), float(-total_investido)]]
        graf_patrimonio += [[str(calendar.timegm(operacao.data.timetuple()) * 1000), float(total_patrimonio)]]
    
    # Adicionar data mais atual
    data_atual = datetime.date.today()
    if str(calendar.timegm(data_atual.timetuple()) * 1000) not in [data for data, _ in graf_patrimonio]:
        total_patrimonio = 0
        for cri_cra in qtd_certificados.keys():
            if qtd_certificados[cri_cra] > 0:
                total_patrimonio += qtd_certificados[cri_cra] * calcular_valor_um_cri_cra_na_data(operacao.cri_cra, data_atual)
        
        graf_investido_total += [[str(calendar.timegm(data_atual.timetuple()) * 1000), float(-total_investido)]]
        graf_patrimonio += [[str(calendar.timegm(data_atual.timetuple()) * 1000), float(total_patrimonio)]]
    
    dados = {}
    dados['total_investido'] = -total_investido
    dados['patrimonio'] = total_patrimonio
    dados['lucro'] = total_patrimonio + total_investido
    if total_investido != 0:
        dados['lucro_percentual'] = (total_patrimonio + total_investido) / -total_investido * 100
    else:
        dados['lucro_percentual'] = 0
        
    return TemplateResponse(request, 'cri_cra/historico.html', {'dados': dados, 'operacoes': operacoes, 
                                                    'graf_investido_total': graf_investido_total, 'graf_patrimonio': graf_patrimonio})
    

@login_required
@adiciona_titulo_descricao('Inserir CRI/CRA', 'Insere um CRI/CRA na lista de Certificados de Recebimento do investidor')
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
                    formset_data_remuneracao = DataRemuneracaoFormSet(request.POST, instance=cri_cra)
                    formset_data_amortizacao = DataAmortizacaoFormSet(request.POST, instance=cri_cra)
                    formset_data_remuneracao.forms[0].empty_permitted = False
                    if formset_data_remuneracao.is_valid():
                        if amortizacao_integral_venc:
                            cri_cra.save()
                            formset_data_remuneracao.save()
                            messages.success(request, '%s criado com sucesso' % (cri_cra.descricao_tipo()))
                            return HttpResponseRedirect(reverse('cri_cra:listar_cri_cra'))
                        else:
                            formset_data_amortizacao.forms[0].empty_permitted = False
                            if formset_data_amortizacao.is_valid():
                                cri_cra.save()
                                formset_data_remuneracao.save()
                                formset_data_amortizacao.save()
                                messages.success(request, '%s criado com sucesso' % (cri_cra.descricao_tipo()))
                                return HttpResponseRedirect(reverse('cri_cra:listar_cri_cra'))

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
@adiciona_titulo_descricao('Inserir operação em CRI/CRA', 'Insere uma operação de compra/venda em CRI/CRA')
def inserir_operacao_cri_cra(request):
    investidor = request.user.investidor
     
    # Preparar formset para divisoes
    DivisaoCRI_CRAFormSet = inlineformset_factory(OperacaoCRI_CRA, DivisaoOperacaoCRI_CRA, form=LocalizedModelForm, fields=('divisao', 'quantidade'), can_delete=False,
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
            except:
                pass
                     
        for erro in [erro for erro in form_operacao_cri_cra.non_field_errors()]:
            messages.error(request, erro)
                  
    else:
        form_operacao_cri_cra = OperacaoCRI_CRAForm(investidor=investidor)
        formset_divisao = DivisaoCRI_CRAFormSet(investidor=investidor)
    return TemplateResponse(request, 'cri_cra/inserir_operacao_cri_cra.html', {'form_operacao_cri_cra': form_operacao_cri_cra, 'formset_divisao': formset_divisao,
                                                                         'varias_divisoes': varias_divisoes})

@adiciona_titulo_descricao('Listar CRI/CRA', 'Lista de Certificados de Recebíveis cadastrados pelo investidor')
def listar_cri_cra(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'cri_cra/listar_cri_cra.html', {'cri_cra': list()})
        
    cri_cra = CRI_CRA.objects.filter(investidor=investidor)
    
    data_atual = datetime.date.today()
    for item in cri_cra:
        if DataRemuneracaoCRI_CRA.objects.filter(cri_cra=item, data__gt=data_atual).exists():
            item.proxima_data_remuneracao = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=item, data__gt=data_atual).order_by('data')[0].data
        else:
            item.proxima_data_remuneracao = None
    
    return TemplateResponse(request, 'cri_cra/listar_cri_cra.html', {'cri_cra': cri_cra})

@adiciona_titulo_descricao('Painel de CRI/CRA', 'Posição atual do investidor em CRI/CRA')
def painel(request):
    if request.user.is_authenticated():
        investidor = request.user.investidor
    else:
        return TemplateResponse(request, 'cri_cra/painel.html', {'cri_cra': list(), 'dados': {}})
                                                                         
    # Processa primeiro operações de venda (V), depois compra (C)
    operacoes = OperacaoCRI_CRA.objects.filter(cri_cra__investidor=investidor).exclude(data__isnull=True).order_by('-tipo_operacao', 'data') 
    if not operacoes:
        dados = {}
        dados['total_investido'] = Decimal(0)
        dados['total_valor_atual'] = Decimal(0)
        dados['total_rendimento_ate_vencimento'] = Decimal(0)
        return TemplateResponse(request, 'cri_cra/painel.html', {'cri_cra': {}, 'dados': dados})

    # Quantidade de debêntures do investidor
    cri_cra = {}
    
    # Prepara o campo valor atual
    for operacao in operacoes:
        if operacao.cri_cra.id not in cri_cra.keys():
            cri_cra[operacao.cri_cra.id] = operacao.cri_cra
            cri_cra[operacao.cri_cra.id].quantidade = 0
            cri_cra[operacao.cri_cra.id].preco_medio = 0
        if operacao.tipo_operacao == 'C':
            cri_cra[operacao.cri_cra.id].preco_medio = (cri_cra[operacao.cri_cra.id].preco_medio * cri_cra[operacao.cri_cra.id].quantidade \
                + operacao.quantidade * operacao.preco_unitario + operacao.taxa)/(cri_cra[operacao.cri_cra.id].quantidade + operacao.quantidade)
            cri_cra[operacao.cri_cra.id].quantidade += operacao.quantidade
        else:
            cri_cra[operacao.cri_cra.id].preco_medio = (cri_cra[operacao.cri_cra.id].preco_medio * cri_cra[operacao.cri_cra.id].quantidade \
                - operacao.quantidade * operacao.preco_unitario + operacao.taxa)/(cri_cra[operacao.cri_cra.id].quantidade - operacao.quantidade)
            cri_cra[operacao.cri_cra.id].quantidade -= operacao.quantidade
    
    # Remover cri_cra com quantidade zerada
    for cri_cra_id in cri_cra.keys():
        if cri_cra[cri_cra_id].quantidade == 0:
            del cri_cra[cri_cra_id]
    
    total_investido = Decimal(0)
    total_valor_atual = Decimal(0)
    total_rendimento_ate_vencimento = Decimal(0)
    
    ultima_taxa_di = HistoricoTaxaDI.objects.all().order_by('-data')[0]
    ultima_taxa_selic = HistoricoTaxaSelic.objects.all().order_by('-data')[0]
    ultima_taxa_ipca = HistoricoIPCA.objects.all().order_by('-ano', '-mes')[0]
    
    for cri_cra_id in cri_cra.keys():
        cri_cra[cri_cra_id].total_investido = cri_cra[cri_cra_id].quantidade * cri_cra[cri_cra_id].preco_medio
        total_investido += cri_cra[cri_cra_id].total_investido
        
        cri_cra[cri_cra_id].valor_atual = calcular_valor_um_cri_cra_na_data(cri_cra[cri_cra_id])
        cri_cra[cri_cra_id].total_atual = cri_cra[cri_cra_id].valor_atual * cri_cra[cri_cra_id].quantidade
        total_valor_atual += cri_cra[cri_cra_id].total_atual
        
        # Próxima remuneração
        if DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cri_cra[cri_cra_id], data__gt=datetime.date.today()).exists():
            cri_cra[cri_cra_id].data_prox_remuneracao = DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cri_cra[cri_cra_id], data__gt=datetime.date.today()).order_by('data')[0].data
            qtd_dias_uteis = qtd_dias_uteis_no_periodo(datetime.date.today(), cri_cra[cri_cra_id].data_prox_remuneracao)
            # TODO adicionar outros indexadores
            if cri_cra[cri_cra_id].tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_DI:
                cri_cra[cri_cra_id].valor_prox_remuneracao = calcular_valor_atualizado_com_taxas({Decimal(ultima_taxa_di.taxa): qtd_dias_uteis},
                                                                                                           cri_cra[cri_cra_id].total_atual, 
                                                                                                           cri_cra[cri_cra_id].porcentagem) - cri_cra[cri_cra_id].total_investido
        else:
            cri_cra[cri_cra_id].data_prox_remuneracao = None
            cri_cra[cri_cra_id].valor_prox_remuneracao = Decimal(0)
        
        # Calcular valor estimado no vencimento
        qtd_dias_uteis_ate_vencimento = qtd_dias_uteis_no_periodo(datetime.date.today(), cri_cra[cri_cra_id].data_vencimento)
        if cri_cra[cri_cra_id].tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_PREFIXADO:
            taxa_anual_pre_mais_juros = cri_cra[cri_cra_id].porcentagem + cri_cra[cri_cra_id].taxa_juros_atual()
            taxa_mensal_pre_mais_juros = pow(1 + taxa_anual_pre_mais_juros/100, Decimal(1)/12) - 1
            taxa_diaria_pre_mais_juros = pow(1 + taxa_mensal_pre_mais_juros, Decimal(1)/12) - 1
            cri_cra[cri_cra_id].valor_rendimento_ate_vencimento = cri_cra[cri_cra_id].total_investido * pow(1 + taxa_diaria_pre_mais_juros, qtd_dias_uteis_ate_vencimento)
        elif cri_cra[cri_cra_id].tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_IPCA:
            # Transformar taxa mensal em anual para somar aos juros da cri_cra
            ipca_anual = pow(1 + ultima_taxa_ipca.valor * (cri_cra[cri_cra_id].porcentagem/100) /Decimal(100), Decimal(12)) - 1
            taxa_mensal_ipca_mais_juros = pow(1 + (ipca_anual + cri_cra[cri_cra_id].taxa_juros_atual())/Decimal(100), Decimal(1)/12) - 1
            taxa_diaria_ipca_mais_juros = pow(1 + taxa_mensal_ipca_mais_juros, Decimal(1)/30) - 1
            cri_cra[cri_cra_id].valor_rendimento_ate_vencimento = cri_cra[cri_cra_id].total_investido * pow(1 + taxa_diaria_ipca_mais_juros, qtd_dias_uteis_ate_vencimento)
        elif cri_cra[cri_cra_id].tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_DI:
            cri_cra[cri_cra_id].valor_rendimento_ate_vencimento = calcular_valor_atualizado_com_taxas({Decimal(ultima_taxa_di.taxa): qtd_dias_uteis_ate_vencimento},
                                                                                                           cri_cra[cri_cra_id].total_atual, 
                                                                                                           cri_cra[cri_cra_id].porcentagem)
        elif cri_cra[cri_cra_id].tipo_indexacao == CRI_CRA.TIPO_INDEXACAO_SELIC:
            # Transformar SELIC em anual para adicionar juros
            selic_mensal = pow(1 + ultima_taxa_selic.taxa, 30) - 1
            selic_anual = pow(1 + selic_mensal, 12) - 1
            taxa_anual_selic_mais_juros = selic_anual * (cri_cra[cri_cra_id].porcentagem / 100) + cri_cra[cri_cra_id].taxa_juros_atual() / 100
            taxa_mensal_selic_mais_juros = pow(1 + taxa_anual_selic_mais_juros, Decimal(1)/12) - 1
            taxa_diaria_selic_mais_juros = pow(1 + taxa_mensal_selic_mais_juros, Decimal(1)/30) - 1
            cri_cra[cri_cra_id].valor_rendimento_ate_vencimento = cri_cra[cri_cra_id].total_investido * pow(1 + taxa_diaria_selic_mais_juros, qtd_dias_uteis_ate_vencimento)
            
        total_rendimento_ate_vencimento += cri_cra[cri_cra_id].valor_rendimento_ate_vencimento
    
    # Popular dados
    dados = {}
    dados['total_investido'] = total_investido
    dados['total_valor_atual'] = total_valor_atual
    dados['total_rendimento_ate_vencimento'] = total_rendimento_ate_vencimento

    return TemplateResponse(request, 'cri_cra/painel.html', {'cri_cra': cri_cra, 'dados': dados})

@adiciona_titulo_descricao('Sobre CRI/CRA', 'Detalha o que são Certificados de Recebíveis')
def sobre(request):
    data_atual = datetime.date.today()
    historico_di = HistoricoTaxaDI.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3))
    graf_historico_di = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(valor_historico.taxa)] for valor_historico in historico_di]
        
    historico_ipca = HistoricoIPCA.objects.filter(ano__gte=(data_atual.year-3)).exclude(mes__lt=data_atual.month, ano=data_atual.year-3)
    graf_historico_ipca = [[str(calendar.timegm(valor_historico.data().timetuple()) * 1000), float(valor_historico.valor)] for valor_historico in historico_ipca]
    
    historico_selic = HistoricoTaxaSelic.objects.filter(data__gte=data_atual.replace(year=data_atual.year-3))
    graf_historico_selic = [[str(calendar.timegm(valor_historico.data.timetuple()) * 1000), float(pow(valor_historico.taxa_diaria, 252) - 1)*100] for valor_historico in historico_selic]
    
    if request.user.is_authenticated():
        total_atual = Decimal(sum(calcular_valor_cri_cra_ate_dia(request.user.investidor).values())).quantize(Decimal('0.01'))
    else:
        total_atual = 0
    
    
    return TemplateResponse(request, 'cri_cra/sobre.html', {'graf_historico_di': graf_historico_di, 'graf_historico_ipca': graf_historico_ipca, 
                                                               'graf_historico_selic': graf_historico_selic, 'total_atual': total_atual})