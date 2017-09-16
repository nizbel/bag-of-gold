# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.outros_investimentos.models import Investimento, Rendimento
from django import forms
from django.forms import widgets

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class InvestimentoForm(LocalizedModelForm):
    class Meta:
        model = Investimento
        fields = ('nome', 'descricao', 'quantidade', 'data')
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(InvestimentoForm, self).__init__(*args, **kwargs)

class RendimentoForm(LocalizedModelForm):
    class Meta:
        model = Rendimento
        fields = ('investimento', 'valor', 'data')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'})}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(RendimentoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['investimento'].queryset = CDB_RDB.objects.filter(investidor=self.investidor)
        