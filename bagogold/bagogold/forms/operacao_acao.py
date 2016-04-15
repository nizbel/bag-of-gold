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
        js = ('js/bagogold/acoes.js',)
    
    def clean(self):
        data = super(OperacaoAcaoForm, self).clean()
        preco_unitario = str(data.get('preco_unitario'))
        preco_unitario = preco_unitario.replace(",", ".")
        preco_unitario = Decimal(preco_unitario)
        data['preco_unitario'] = preco_unitario

        return data

class UsoProventosOperacaoAcaoForm(forms.ModelForm):


    class Meta:
        model = UsoProventosOperacaoAcao
        fields = ('qtd_utilizada', )
            
    def clean(self):
        data = super(UsoProventosOperacaoAcaoForm, self).clean()
        if data.get('qtd_utilizada') is not None:
            qtd_utilizada = str(data.get('qtd_utilizada'))
            qtd_utilizada = qtd_utilizada.replace(",", ".")
            qtd_utilizada = Decimal(qtd_utilizada)
            data['qtd_utilizada'] = qtd_utilizada

        return data