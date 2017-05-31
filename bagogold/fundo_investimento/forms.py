# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.fundo_investimento import FundoInvestimento, \
    OperacaoFundoInvestimento, HistoricoCarenciaFundoInvestimento, \
    HistoricoValorCotas
from bagogold.bagogold.utils.fundo_investimento import \
    calcular_qtd_cotas_ate_dia_por_fundo
from django import forms
from django.forms import widgets
import datetime

ESCOLHAS_TIPO_PRAZO=(('L', 'Longo prazo'), 
                            ('C', 'Curto prazo'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class FundoInvestimentoForm(LocalizedModelForm):
    class Meta:
        model = FundoInvestimento
        fields = ('nome', 'tipo_prazo', 'descricao', 'taxa_adm')
        widgets={'tipo_prazo': widgets.Select(choices=ESCOLHAS_TIPO_PRAZO),}

class OperacaoFundoInvestimentoForm(LocalizedModelForm):
    
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
        
    def clean(self):
        dados = super(OperacaoFundoInvestimentoForm, self).clean()
        data = dados.get('data')
        # Testa se não se trata de uma edição de compra para venda
        if dados.get('tipo_operacao') == 'V':
            if self.instance.tipo_operacao == 'C':
                # Verificar se já há vendas registradas para essa compra, se sim, lançar erro
                if calcular_qtd_cotas_ate_dia_por_fundo(self.investidor, self.instance.fundo_investimento.id, datetime.date.today()) - self.instance.quantidade < 0:
                    raise forms.ValidationError('Não é possível alterar tipo de operação pois a quantidade atual para o fundo %s seria negativa' % (self.instance.fundo_investimento))
            # Verifica se é possível vender o título apontado
            if calcular_qtd_cotas_ate_dia_por_fundo(self.investidor, dados.get('fundo_investimento').id, data) < dados.get('quantidade'):
                raise forms.ValidationError('Não é possível vender a quantidade informada para o fundo %s' % (dados.get('fundo_investimento')))
        
class HistoricoValorCotasForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoValorCotas
        fields = ('valor_cota', 'data',
                  'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoFundoInvestimentoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['fundo_investimento'].queryset = FundoInvestimento.objects.filter(investidor=self.investidor)
        
    def clean_data(self):
        data = self.cleaned_data['data']
        if data > datetime.date.today():
            raise forms.ValidationError('Data não pode ser posterior a data atual')
        
        return data
            
        
class HistoricoCarenciaFundoInvestimentoForm(LocalizedModelForm):
    
    class Meta:
        model = HistoricoCarenciaFundoInvestimento
        fields = ('carencia', 'data',
                  'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        labels = {'carencia': 'Período de carência (em dias)',}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.fundo_investimento = kwargs.pop('fundo_investimento')
        except:
            self.fundo_investimento = None
        # first call parent's constructor
        super(HistoricoCarenciaFundoInvestimentoForm, self).__init__(*args, **kwargs)
        self.fields['fundo_investimento'].queryset = FundoInvestimento.objects.filter(investidor=self.investidor)
        if self.fundo_investimento:
            self.fields['fundo_investimento'].disabled = True
        if self.inicial:
            self.fields['data'].disabled = True
        
        def clean_fundo_investimento(self):
            if self.cleaned_data['fundo_investimento'].investidor != self.investidor:
                raise forms.ValidationError('Fundo de investimento inválido')
            return self.cleaned_data['fundo_investimento']
        
        def clean_carencia(self):
            carencia = self.cleaned_data['carencia']
            if carencia <= 0:
                raise forms.ValidationError('Carência deve ser de pelo menos 1 dia')
            return carencia