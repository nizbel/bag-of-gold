# -*- coding: utf-8 -*-
from bagogold.bagogold.models.fundo_investimento import FundoInvestimento, \
    OperacaoFundoInvestimento, HistoricoCarenciaFundoInvestimento, HistoricoValorCotas
from django import forms
from django.forms import widgets

ESCOLHAS_TIPO_PRAZO=(('L', 'Longo prazo'), 
                            ('C', 'Curto prazo'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class FundoInvestimentoForm(forms.ModelForm):
    class Meta:
        model = FundoInvestimento
        fields = ('nome', 'tipo_prazo', 'descricao')
        widgets={'tipo_prazo': widgets.Select(choices=ESCOLHAS_TIPO_PRAZO),}

class OperacaoFundoInvestimentoForm(forms.ModelForm):
    
    class Meta:
        model = OperacaoFundoInvestimento
        fields = ('tipo_operacao', 'quantidade_cotas', 'valor', 'data', 'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        labels = {'fundo_investimento': 'Fundo de investimento',}
        
    class Media:
        js = ('js/bagogold/fundo_investimento.js',)
        
class HistoricoValorCotasForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoValorCotas
        fields = ('valor_cota', 'data',
                  'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
class HistoricoCarenciaFundoInvestimentoForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoCarenciaFundoInvestimento
        fields = ('carencia', 'data',
                  'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'carencia': 'Período de carência (em dias)',}