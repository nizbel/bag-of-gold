# -*- coding: utf-8 -*-
from bagogold.models.acoes import OperacaoAcao
from django import forms
from django.forms import widgets


ESCOLHAS_CONSOLIDADO=(
        (True, "Sim"),
        (False, "Não"),
        )

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoAcaoForm(forms.ModelForm):


    class Meta:
        model = OperacaoAcao
        fields = ('preco_unitario', 'quantidade', 'data', 'corretagem', 'emolumentos', 'tipo_operacao',
                  'acao', 'consolidada')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),
                 'consolidada': widgets.Select(choices=ESCOLHAS_CONSOLIDADO),}
        
    class Media:
        js = ('js/acoes.js',)
    
    def clean(self):
        data = super(OperacaoAcaoForm, self).clean()
        preco_unitario = str(data.get('preco_unitario'))
        preco_unitario = preco_unitario.replace(",", ".")
        preco_unitario = float(preco_unitario)
        data['preco_unitario'] = preco_unitario

        return data
