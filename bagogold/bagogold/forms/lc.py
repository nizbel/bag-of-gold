# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import OperacaoLetraCredito, \
    HistoricoPorcentagemLetraCredito, LetraCredito, HistoricoCarenciaLetraCredito
from django import forms
from django.forms import widgets
import datetime


ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class LetraCreditoForm(forms.ModelForm):
    
    class Meta:
        model = LetraCredito
        fields = ('nome',)

class OperacaoLetraCreditoForm(forms.ModelForm):
    # Campo verificado apenas no caso de venda de operação de lc
    operacao_compra = forms.ModelChoiceField(label='Operação de compra',queryset=OperacaoLetraCredito.objects.filter(investidor=self.investidor, tipo_operacao='C'), required=False)
    
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
        # Remover operações que já tenham sido totalmente vendidas e a própria operação
        operacoes_compra_invalidas = [operacao_compra_invalida.id for operacao_compra_invalida in self.fields['operacao_compra'].queryset if operacao_compra_invalida.qtd_disponivel_venda() == 0] + \
            [self.instance.id] if self.instance.id != None else []
        # Manter operação de compra atual, caso seja edição de venda
        if self.instance.operacao_compra_relacionada():
            operacoes_compra_invalidas.remove(self.instance.operacao_compra_relacionada().id)
        self.fields['operacao_compra'].queryset = self.fields['operacao_compra'].queryset.exclude(id__in=operacoes_compra_invalidas)
    
    def clean_operacao_compra(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        print self.instance.id
        if tipo_operacao == 'V':
            operacao_compra = self.cleaned_data.get('operacao_compra')
            # Testar se operacao_compra é válido
            if operacao_compra is None:
                raise forms.ValidationError('Selecione operação de compra válida')
            quantidade = self.cleaned_data['quantidade']
            # Testar data, deve ser posterior a operação de compra relacionada
            if 'data' not in self.cleaned_data or self.cleaned_data['data'] == None:
                return None
            else:
                if self.cleaned_data["data"] < operacao_compra.data + datetime.timedelta(days=operacao_compra.carencia()):
                    raise forms.ValidationError('Data da venda deve ser posterior ao período de carência (%s)' % 
                                                ((operacao_compra.data + datetime.timedelta(days=operacao_compra.carencia())).strftime("%d/%m/%Y")))
            if quantidade > operacao_compra.qtd_disponivel_venda():
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
    
class HistoricoPorcentagemLetraCreditoForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoPorcentagemLetraCredito
        fields = ('porcentagem_di', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(HistoricoPorcentagemLetraCreditoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['letra_credito'].required = False
        self.fields['letra_credito'].queryset = LetraCredito.objects.filter(investidor=self.investidor)
        
        def clean_letra_credito(self):
            
        
class HistoricoCarenciaLetraCreditoForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoCarenciaLetraCredito
        fields = ('carencia', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'carencia': 'Período de carência (em dias)',}
    
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(HistoricoCarenciaLetraCreditoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['letra_credito'].required = False
        self.fields['letra_credito'].queryset = LetraCredito.objects.filter(investidor=self.investidor)
        
