# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo
from django import forms
from django.forms import widgets


ESCOLHAS_CONSOLIDADO=(
        (True, "Sim"),
        (False, "Não"),
        )

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))
            
    
class OperacaoTituloForm(forms.ModelForm):
    
    class Meta:
        model = OperacaoTitulo
        fields = ('preco_unitario', 'quantidade', 'data', 'taxa_bvmf', 'taxa_custodia', 'tipo_operacao',
                  'titulo', 'consolidada',)
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),
                 'consolidada': widgets.Select(choices=ESCOLHAS_CONSOLIDADO),}

    def clean(self):
        dados = super(OperacaoTituloForm, self).clean()
        data = dados.get('data')
        data_vencimento = dados.get('titulo').data_vencimento
#         print '%s %s %s' % (data_ex, data_pagamento, data_ex < data_pagamento)
        if (data > data_vencimento):
            raise forms.ValidationError("Título não pode ter sido comprado após sua data de vencimento")
        return dados