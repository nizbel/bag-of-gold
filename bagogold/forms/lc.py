# -*- coding: utf-8 -*-
from bagogold.models.lc import OperacaoLetraCredito, \
    HistoricoPorcentagemLetraCredito
from django import forms
from django.forms import widgets


ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoLetraCreditoForm(forms.ModelForm):
    
    class Meta:
        model = OperacaoLetraCredito
        fields = ('quantidade', 'data', 'tipo_operacao',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    
    
class HistoricoPorcentagemLetraCreditoForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoPorcentagemLetraCredito
        fields = ('porcentagem_di', 'data',
                  'letra_credito')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}