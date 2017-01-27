# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.debentures import OperacaoDebenture
from django import forms
from django.forms import widgets


ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoDebentureForm(LocalizedModelForm):
    
    class Meta:
        model = OperacaoDebenture
        fields = ('preco_unitario', 'quantidade', 'data', 'taxa', 'debenture', 'tipo_operacao')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/debenture.js',)
        
    def clean(self):
        data = super(OperacaoDebentureForm, self).clean()
        print data
        debenture = data.get('debenture')
        if debenture.data_fim and data.get('data') >= debenture.data_fim:
            raise forms.ValidationError('Operação deve ter sido realizado antes da data de fim da debênture')

        return data