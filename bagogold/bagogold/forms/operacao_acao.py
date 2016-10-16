# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao, \
    UsoProventosOperacaoAcao
from decimal import Decimal
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
        js = ('js/bagogold/calculo_emolumentos.js', 
              'js/bagogold/acoes.js',)
    
    def clean_preco_unitario(self):
        preco_unitario = Decimal(self.cleaned_data['preco_unitario'])
        if preco_unitario <= Decimal(0):
            raise forms.ValidationError('Preço unitário deve ser maior que 0')
        return preco_unitario
    
class UsoProventosOperacaoAcaoForm(forms.ModelForm):


    class Meta:
        model = UsoProventosOperacaoAcao
        fields = ('qtd_utilizada', )
        
    def __init__(self, *args, **kwargs):
        super(UsoProventosOperacaoAcaoForm, self).__init__(*args, **kwargs)
        self.fields['qtd_utilizada'].required = False
            
    def clean(self):
        data = super(UsoProventosOperacaoAcaoForm, self).clean()
        if data.get('qtd_utilizada') is not None:
            if data.get('qtd_utilizada') < 0:
                raise forms.ValidationError('Quantidade de proventos utilizada não pode ser negativa')
            qtd_utilizada = str(data.get('qtd_utilizada'))
            qtd_utilizada = qtd_utilizada.replace(",", ".")
            qtd_utilizada = Decimal(qtd_utilizada)
            data['qtd_utilizada'] = qtd_utilizada
        else:
            data['qtd_utilizada'] = 0

        return data