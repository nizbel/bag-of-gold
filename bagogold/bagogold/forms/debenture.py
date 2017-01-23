# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.debentures import OperacaoDebenture
from django.forms import widgets


ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoDebentureForm(LocalizedModelForm):
    
    class Meta:
        model = OperacaoDebenture
        fields = ('preco_unitario', 'quantidade', 'data', 'taxa', 'debenture')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/debenture.js',)
        
