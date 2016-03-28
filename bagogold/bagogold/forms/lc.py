# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import OperacaoLetraCredito, \
    HistoricoPorcentagemLetraCredito, LetraCredito, HistoricoCarenciaLetraCredito
from django import forms
from django.forms import widgets


ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class LetraCreditoForm(forms.ModelForm):
    
    class Meta:
        model = LetraCredito
        fields = ('nome',)

class OperacaoLetraCreditoForm(forms.ModelForm):
    # Campo verificado apenas no caso de venda de operação de lc
    operacao_compra = forms.ModelChoiceField(queryset=OperacaoLetraCredito.objects.filter(tipo_operacao='C'), required=False)
    
    class Meta:
        model = OperacaoLetraCredito
        fields = ('operacao_compra', 'quantidade', 'data', 'tipo_operacao',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/lc.js',)
        
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(OperacaoLetraCreditoForm, self).__init__(*args, **kwargs)
        print dir(self.fields)
        self.fields.keys = ['tipo_operacao', 'quantidade', 'data', 'operacao_compra', 'letra_credito']
        # there's a `fields` property now
        self.fields['letra_credito'].required = False
    
    def clean_operacao_compra(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            operacao_compra = self.cleaned_data.get('operacao_compra')
            # Testar se operacao_compra é válido
            if operacao_compra is None:
                raise forms.ValidationError('Selecione operação de compra válida')
            quantidade = self.cleaned_data['quantidade']
            if quantidade > operacao_compra.qtd_disponivel_venda():
                raise forms.ValidationError('Não é possível vender mais do que o disponível na operação de compra')
            return operacao_compra
        return None

    def clean_letra_credito(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            letra_credito = self.cleaned_data.get('operacao_compra').letra_credito
        else:
            letra_credito = self.cleaned_data.get('letra_credito')
        if letra_credito is None:
            raise forms.ValidationError('Insira letra de crédito válida')
              
        return letra_credito
    
    
class HistoricoPorcentagemLetraCreditoForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoPorcentagemLetraCredito
        fields = ('porcentagem_di', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
class HistoricoCarenciaLetraCreditoForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoCarenciaLetraCredito
        fields = ('carencia', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
