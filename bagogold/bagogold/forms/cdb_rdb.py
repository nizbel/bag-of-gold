# -*- coding: utf-8 -*-
from django import forms
from django.forms import widgets


ESCOLHAS_CDB_RDB=((1, 'CDB'), (2, 'RDB'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class CDBRDBForm(forms.Form):
    tipo = forms.ChoiceField(label='Tipo', widget=widgets.Select(choices=ESCOLHAS_CDB_RDB))
    nome = forms.CharField(label='Nome', max_length=50)
"""
class OperacaoCDBRDBForm(forms.ModelForm):
    # Campo verificado apenas no caso de venda de operação de lc
    operacao_compra = forms.ModelChoiceField(label='Operação de compra',queryset=OperacaoCDBRDB.objects.filter(tipo_operacao='C'), required=False)
    
    class Meta:
        model = OperacaoCDBRDB
        fields = ('tipo_operacao', 'quantidade', 'data', 'operacao_compra',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/lc.js',)
        
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(OperacaoCDBRDBForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['letra_credito'].required = False
#         if self.instance.pk is not None:
#             # Verificar se é uma compra
#             if self.instance.tipo_operacao == 'V':
#                 self.operacao_compra.v
    
    def clean_operacao_compra(self):
        print 'test'
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
    
    
class HistoricoPorcentagemCDBRDBForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoPorcentagemCDBRDB
        fields = ('porcentagem_di', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
class HistoricoCarenciaCDBRDBForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoCarenciaCDBRDB
        fields = ('carencia', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
"""        
