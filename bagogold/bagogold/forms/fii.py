# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fii import FII, OperacaoFII, ProventoFII, \
    UsoProventosOperacaoFII
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
        
    def clean(self):
        data = super(OperacaoFIIForm, self).clean()
        if data.get('consolidada') is True:
            if data.get('data') is None:
                raise forms.ValidationError('Operações consolidadas precisam de uma data definida')

        return data
    
    
class UsoProventosOperacaoFIIForm(forms.ModelForm):


    class Meta:
        model = UsoProventosOperacaoFII
        fields = ('qtd_utilizada', )
            
    def clean(self):
        data = super(UsoProventosOperacaoFIIForm, self).clean()
        if data.get('qtd_utilizada') is not None:
            if data.get('qtd_utilizada') < 0:
                raise forms.ValidationError('Quantidade de proventos utilizada não pode ser negativa')
            qtd_utilizada = str(data.get('qtd_utilizada'))
            qtd_utilizada = qtd_utilizada.replace(",", ".")
            qtd_utilizada = float(qtd_utilizada)
            data['qtd_utilizada'] = qtd_utilizada

        return data