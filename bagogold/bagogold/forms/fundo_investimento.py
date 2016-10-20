# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fundo_investimento import FundoInvestimento, \
    OperacaoFundoInvestimento, HistoricoCarenciaFundoInvestimento, \
    HistoricoValorCotas
from django import forms
from django.forms import widgets
import datetime

ESCOLHAS_TIPO_PRAZO=(('L', 'Longo prazo'), 
                            ('C', 'Curto prazo'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class FundoInvestimentoForm(forms.ModelForm):
    class Meta:
        model = FundoInvestimento
        fields = ('nome', 'tipo_prazo', 'descricao', 'taxa_adm')
        widgets={'tipo_prazo': widgets.Select(choices=ESCOLHAS_TIPO_PRAZO),}

class OperacaoFundoInvestimentoForm(forms.ModelForm):
    
    class Meta:
        model = OperacaoFundoInvestimento
        fields = ('tipo_operacao', 'quantidade', 'valor', 'data', 'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        labels = {'fundo_investimento': 'Fundo de investimento',}
    
    class Media:
        js = ('js/bagogold/fundo_investimento.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoFundoInvestimentoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['fundo_investimento'].queryset = FundoInvestimento.objects.filter(investidor=self.investidor)
        
class HistoricoValorCotasForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoValorCotas
        fields = ('valor_cota', 'data',
                  'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
    def clean_data(self):
        data = self.cleaned_data['data']
        if data > datetime.date.today():
            raise forms.ValidationError('Data não pode ser posterior a data atual')
        
        return data
            
        
class HistoricoCarenciaFundoInvestimentoForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoCarenciaFundoInvestimento
        fields = ('carencia', 'data',
                  'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'carencia': 'Período de carência (em dias)',}