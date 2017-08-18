# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.criptomoeda.models import OperacaoCriptomoeda, Criptomoeda
from django import forms
from django.forms import widgets

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoCriptomoedaForm(LocalizedModelForm):
    moeda_utilizada = forms.ChoiceField(required=False)
    
    class Meta:
        model = OperacaoCriptomoeda
        fields = ('tipo_operacao', 'quantidade', 'valor', 'data', 'criptomoeda', 'taxa')
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
        escolhas_moeda = (('', 'R$ (Reais)'),)
        for criptomoeda in Criptomoeda.objects.all():
            escolhas_moeda += ((criptomoeda.id, '%s (%s)' % (criptomoeda.ticker, criptomoeda.nome)),)
        self.fields['moeda_utilizada'].choices = escolhas_moeda
        self.fields['criptomoeda'].choices = escolhas_moeda[1:]

    def clean(self):
        data = super(OperacaoCriptomoedaForm, self).clean()
        # Testa se a moeda utilizada para operação e a moeda adquirida/vendida na operação são diferentes
        print data.get('criptomoeda').id, data.get('moeda_utilizada'), data.get('criptomoeda').id == int(data.get('moeda_utilizada')), data.get('moeda_utilizada').isdigit()
        if data.get('moeda_utilizada').isdigit() and data.get('criptomoeda').id == int(data.get('moeda_utilizada')):
            raise forms.ValidationError('A moeda utilizada deve ser diferente da moeda comprada/vendida')