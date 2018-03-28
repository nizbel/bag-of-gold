# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.lci_lca.models import OperacaoLetraCredito, \
    HistoricoPorcentagemLetraCredito, LetraCredito, HistoricoCarenciaLetraCredito, \
    OperacaoVendaLetraCredito
from django import forms
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from django.db.models.functions import Coalesce
from django.db.models.query_utils import Q
from django.forms import widgets
import datetime


ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class LetraCreditoForm(LocalizedModelForm):
    
    class Meta:
        model = LetraCredito
        fields = ('nome',)

class OperacaoLetraCreditoForm(LocalizedModelForm):
    # Campo verificado apenas no caso de venda de operação de lci_lca
    operacao_compra = forms.ModelChoiceField(label='Operação de compra', queryset=OperacaoLetraCredito.objects.none(), required=False)
    
    class Meta:
        model = OperacaoLetraCredito
        fields = ('tipo_operacao', 'quantidade', 'data', 'operacao_compra',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/form_operacao_lci_lca.min.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoLetraCreditoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['letra_credito'].required = False
        self.fields['letra_credito'].queryset = LetraCredito.objects.filter(investidor=self.investidor)
        # Manter operação de compra atual, caso seja edição de venda
        if self.instance.operacao_compra_relacionada():
            query_operacao_compra = OperacaoLetraCredito.objects.filter(investidor=self.investidor, tipo_operacao='C').annotate( \
                qtd_vendida=Coalesce(Sum(F('operacao_compra__operacao_venda__quantidade')), 0)).filter(Q(qtd_vendida__lt=F('quantidade')) \
                                                                                                   | Q(id=self.instance.operacao_compra_relacionada().id))
        else:
            query_operacao_compra = OperacaoLetraCredito.objects.filter(investidor=self.investidor, tipo_operacao='C').annotate( \
                qtd_vendida=Coalesce(Sum(F('operacao_compra__operacao_venda__quantidade')), 0)).exclude(qtd_vendida=F('quantidade'))
        self.fields['operacao_compra'].queryset = query_operacao_compra.order_by('data')
    
    def clean_operacao_compra(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            operacao_compra = self.cleaned_data.get('operacao_compra')
            # Testar se operacao_compra é válido
            if operacao_compra is None:
                raise forms.ValidationError('Selecione operação de compra válida')
            # Testar data, deve ser posterior a operação de compra relacionada
            if 'data' not in self.cleaned_data or self.cleaned_data['data'] == None:
                return None
            else:
                if self.cleaned_data["data"] < operacao_compra.data + datetime.timedelta(days=operacao_compra.carencia()):
                    raise forms.ValidationError('Data da venda deve ser posterior ao período de carência (%s)' % 
                                                ((operacao_compra.data + datetime.timedelta(days=operacao_compra.carencia())).strftime("%d/%m/%Y")))
            # Testar quantidade
            quantidade = self.cleaned_data['quantidade']
            if quantidade > operacao_compra.qtd_disponivel_venda(desconsiderar_vendas=[self.instance]):
                raise forms.ValidationError('Não é possível vender mais do que o disponível na operação de compra')
            return operacao_compra
        return None

    def clean_letra_credito(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            if self.cleaned_data.get('operacao_compra'):
                letra_credito = self.cleaned_data.get('operacao_compra').letra_credito
                return letra_credito
        else:
            letra_credito = self.cleaned_data.get('letra_credito')
            if letra_credito is None:
                raise forms.ValidationError('Insira letra de crédito válida')
            return letra_credito
        return None
    
    def clean(self):
        data = super(OperacaoLetraCreditoForm, self).clean()
        # Testa se não se trata de uma edição de compra para venda
        if data.get('tipo_operacao') == 'V' and self.instance.tipo_operacao == 'C':
            # Verificar se já há vendas registradas para essa compra, se sim, lançar erro
            if OperacaoVendaLetraCredito.objects.filter(operacao_compra=self.instance):
                raise forms.ValidationError('Não é possível alterar tipo de operação pois já há vendas registradas para essa compra')
            
class HistoricoPorcentagemLetraCreditoForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoPorcentagemLetraCredito
        fields = ('porcentagem_di', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.letra_credito = kwargs.pop('letra_credito')
        except:
            self.letra_credito = None
        # first call parent's constructor
        super(HistoricoPorcentagemLetraCreditoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['letra_credito'].queryset = LetraCredito.objects.filter(investidor=self.investidor)
        if self.letra_credito:
            self.fields['letra_credito'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_data(self):
        data = self.cleaned_data['data']
        # Verifica se o registro é da data incial, e se foi feita alteração
        if self.inicial and data:
            raise forms.ValidationError('Data inicial não pode ser alterada')
        elif not self.inicial and not data:
            raise forms.ValidationError('Data é obrigatória')
        return data
        
    def clean_letra_credito(self):
        letra_credito = self.cleaned_data['letra_credito']
        if letra_credito.investidor != self.investidor:
            raise forms.ValidationError('Letra de Crédito inválida')
        if hasattr(self.instance, 'letra_credito') and letra_credito != self.instance.letra_credito:
            raise forms.ValidationError('Letra de Crédito não deve ser alterada')
        return letra_credito
    
    def clean_porcentagem_di(self):
        porcentagem_di = self.cleaned_data['porcentagem_di']
        if porcentagem_di <= 0:
            raise forms.ValidationError('Porcentagem deve ser maior que zero')
        return porcentagem_di
    
    def clean(self):
        cleaned_data = super(HistoricoPorcentagemLetraCreditoForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoPorcentagemLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de porcentagem para essa data')
        return cleaned_data
        
class HistoricoCarenciaLetraCreditoForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoCarenciaLetraCredito
        fields = ('carencia', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'carencia': 'Período de carência',}
    
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.letra_credito = kwargs.pop('letra_credito')
        except:
            self.letra_credito = None
        # first call parent's constructor
        super(HistoricoCarenciaLetraCreditoForm, self).__init__(*args, **kwargs)
        self.fields['letra_credito'].queryset = LetraCredito.objects.filter(investidor=self.investidor)
        if self.letra_credito:
            self.fields['letra_credito'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_carencia(self):
        carencia = self.cleaned_data['carencia']
        if carencia <= 0:
            raise forms.ValidationError('Carência deve ser de pelo menos 1 dia')
        return carencia
    
    def clean_data(self):
        data = self.cleaned_data['data']
        # Verifica se o registro é da data incial, e se foi feita alteração
        if self.inicial and data:
            raise forms.ValidationError('Data inicial não pode ser alterada')
        elif not self.inicial and not data:
            raise forms.ValidationError('Data é obrigatória')
        return data
        
    def clean_letra_credito(self):
        letra_credito = self.cleaned_data['letra_credito']
        if letra_credito.investidor != self.investidor:
            raise forms.ValidationError('Letra de Crédito inválida')
        if hasattr(self.instance, 'letra_credito') and letra_credito != self.instance.letra_credito:
            raise forms.ValidationError('Letra de Crédito não deve ser alterada')
        return letra_credito
    
    def clean(self):
        cleaned_data = super(HistoricoCarenciaLetraCreditoForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoCarenciaLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de carência para essa data')
        return cleaned_data
    
class HistoricoVencimentoLetraCreditoForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoVencimentoLetraCredito
        fields = ('vencimento', 'data', 'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'vencimento': 'Período de vencimento',
                  'letra_credito': 'LCI/LCA'}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.letra_credito = kwargs.pop('letra_credito')
        except:
            self.letra_credito = None
        super(HistoricoVencimentoLetraCreditoForm, self).__init__(*args, **kwargs)
        if self.letra_credito:
            self.fields['letra_credito'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
    
    def clean_vencimento(self):
        vencimento = self.cleaned_data['vencimento']
        if vencimento <= 0:
            raise forms.ValidationError('Período de vencimento deve ser de pelo menos 1 dia')
        return vencimento
    
    def clean_letra_credito(self):
        letra_credito = self.cleaned_data['letra_credito']
        if letra_credito.investidor != self.investidor:
            raise forms.ValidationError('LCI/LCA inválida')
        if hasattr(self.instance, 'letra_credito') and letra_credito != self.instance.letra_credito:
            raise forms.ValidationError('LCI/LCA não deve ser alterada')
        return letra_credito
    
    def clean_data(self):
        data = self.cleaned_data['data']
        # Verifica se o registro é da data incial, e se foi feita alteração
        if self.inicial and data:
            raise forms.ValidationError('Data inicial não pode ser alterada')
        elif not self.inicial and not data:
            raise forms.ValidationError('Data é obrigatória')
        return data
    
    def clean(self):
        cleaned_data = super(HistoricoVencimentoLetraCreditoForm, self).clean()
        cleaned_data.get('letra_credito')
        # Testar se já existe algum histórico para o investimento na data
        if not self.inicial and cleaned_data.get('data') and HistoricoVencimentoLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Já existe uma alteração de vencimento para essa data')
        
        # Testes para datas iniciais
        if self.inicial:
            # Verificar carência inicial e todas as carências até próxima alteração de vencimento
            carencia_inicial = HistoricoCarenciaLetraCredito.objects.get(letra_credito=cleaned_data.get('letra_credito'), data__isnull=True).carencia
            if carencia_inicial > cleaned_data.get('vencimento'):
                raise forms.ValidationError('Carência inicial está maior do que período de vencimento inicial')
            elif HistoricoVencimentoLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data__isnull=False).exists():
                # Verificar alterações de carência entre o vencimento inicial e a próxima alteração
                proximo_vencimento = HistoricoVencimentoLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data__isnull=False).order_by('data')[0]
                for carencia_periodo in HistoricoCarenciaLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data__lt=proximo_vencimento.data):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de carência a partir da data dessa alteração de vencimento
                for carencia_periodo in HistoricoCarenciaLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito')):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            
        # Testes para datas não iniciais
        else:
            # Verificar carência vigente, e alterações de carência ao longo do período que esse novo vencimento estiver vigente
            carencia_vigente = cleaned_data.get('letra_credito').carencia_na_data(cleaned_data.get('data'))
            if carencia_vigente > cleaned_data.get('vencimento'):
                raise forms.ValidationError('Carência na data de início está maior do que o período de vencimento')
            # Testar se período de vencimento será menor que algum período de carência vigente
            if HistoricoVencimentoLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data__gt=cleaned_data.get('data')).exists():
                # Verificar alterações de carência entre a data dessa alteração de vencimento e a próxima
                proximo_vencimento = HistoricoVencimentoLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data__gt=cleaned_data.get('data')).order_by('data')[0]
                for carencia_periodo in HistoricoCarenciaLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data__range=[cleaned_data.get('data') + datetime.timedelta(days=1), 
                                                                                                                   proximo_vencimento.data - datetime.timedelta(days=1)]):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
            else:
                # Verificar alterações de carência a partir da data dessa alteração de vencimento
                for carencia_periodo in HistoricoCarenciaLetraCredito.objects.filter(letra_credito=cleaned_data.get('letra_credito'), data__gt=cleaned_data.get('data')):
                    if carencia_periodo.carencia > cleaned_data.get('vencimento'):
                        raise forms.ValidationError('Carência vigente em %s está maior do que o período de vencimento' % (carencia_periodo.data.strftime('%d/%m/%Y')))
        
                
        return cleaned_data