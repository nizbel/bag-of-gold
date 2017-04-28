# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.lc import OperacaoLetraCredito, \
    HistoricoPorcentagemLetraCredito, LetraCredito, HistoricoCarenciaLetraCredito, \
    OperacaoVendaLetraCredito
from django import forms
from django.forms import widgets
import datetime


ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class LetraCreditoForm(LocalizedModelForm):
    
    class Meta:
        model = LetraCredito
        fields = ('nome',)

class OperacaoLetraCreditoForm(LocalizedModelForm):
    # Campo verificado apenas no caso de venda de operação de lc
    operacao_compra = forms.ModelChoiceField(label='Operação de compra',queryset=OperacaoLetraCredito.objects.filter(tipo_operacao='C'), required=False)
    
    class Meta:
        model = OperacaoLetraCredito
        fields = ('tipo_operacao', 'quantidade', 'data', 'operacao_compra',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/lc.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoLetraCreditoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['letra_credito'].required = False
        self.fields['letra_credito'].queryset = LetraCredito.objects.filter(investidor=self.investidor)
        self.fields['operacao_compra'].queryset = OperacaoLetraCredito.objects.filter(investidor=self.investidor, tipo_operacao='C')
        # Remover operações que já tenham sido totalmente vendidas e a própria operação
        operacoes_compra_invalidas = [operacao_compra_invalida.id for operacao_compra_invalida in self.fields['operacao_compra'].queryset if operacao_compra_invalida.qtd_disponivel_venda() <= 0] + \
            ([self.instance.id] if self.instance.id != None else [])
        # Manter operação de compra atual, caso seja edição de venda
        if self.instance.operacao_compra_relacionada():
            operacoes_compra_invalidas.remove(self.instance.operacao_compra_relacionada().id)
        self.fields['operacao_compra'].queryset = self.fields['operacao_compra'].queryset.exclude(id__in=operacoes_compra_invalidas)
    
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