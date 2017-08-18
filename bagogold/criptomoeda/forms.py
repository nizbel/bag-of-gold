# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.criptomoeda.models import OperacaoCriptomoeda, Criptomoeda
from django import forms
from django.forms import widgets

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoCriptomoedaForm(LocalizedModelForm):
    escolhas_moeda = (('', 'R$ (Reais)'),)
    for criptomoeda in Criptomoeda.objects.all():
        escolhas_moeda += ((criptomoeda.id, '%s (%s)' % (criptomoeda.ticker, criptomoeda.nome)),)
    print escolhas_moeda
    moeda_utilizada = forms.ChoiceField(required=False, choices=escolhas_moeda)
    
    class Meta:
        model = OperacaoCriptomoeda
        fields = ('tipo_operacao', 'quantidade', 'valor', 'data', 'criptomoeda')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        labels = {'criptomoeda': 'Criptomoeda',}
    
    class Media:
        js = ('js/bagogold/form_operacao_criptomoeda.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoCriptomoedaForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['moeda_utilizada'].queryset = OperacaoCriptomoeda.objects.all()
