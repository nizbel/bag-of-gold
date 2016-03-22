# -*- coding: utf-8 -*-
from bagogold.models.fii import FII, OperacaoFII, ProventoFII
from django import forms
from django.forms import widgets


ESCOLHAS_CONSOLIDADO=(
        (True, "Sim"),
        (False, "Não"),
        )

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class FIIForm(forms.ModelForm):


    class Meta:
        model = FII
        fields = ('ticker', )
        
        
class ProventoFIIForm(forms.ModelForm):


    class Meta:
        model = ProventoFII
        fields = ('valor_unitario', 'data_ex', 'data_pagamento', 'fii', )
        widgets={'data_ex': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'data_pagamento': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
    
    
class OperacaoFIIForm(forms.ModelForm):
    
    class Meta:
        model = OperacaoFII
        fields = ('preco_unitario', 'quantidade', 'data', 'corretagem', 'emolumentos', 'tipo_operacao',
                  'fii', 'consolidada')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),
                 'consolidada': widgets.Select(choices=ESCOLHAS_CONSOLIDADO),}
        
    class Media:
        js = ('js/acoes.js',)
    
    
