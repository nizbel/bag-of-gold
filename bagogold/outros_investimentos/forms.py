# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.outros_investimentos.models import Investimento, \
    OperacaoInvestimento
from django import forms
from django.forms import widgets

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class InvestimentoForm(LocalizedModelForm):
    class Meta:
        model = Investimento
        fields = ('nome', 'descricao',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(InvestimentoForm, self).__init__(*args, **kwargs)

class OperacaoInvestimentoForm(LocalizedModelForm):
    class Meta:
        model = OperacaoInvestimento
        fields = ('tipo_operacao', 'quantidade', 'investimento', 'data')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
    
    class Media:
        js = ('js/bagogold/form_operacao_investimento.js',)
        
    def clean(self):
        data = super(OperacaoInvestimentoForm, self).clean()
