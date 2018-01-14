# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.divisoes import Divisao
from bagogold.criptomoeda.models import OperacaoCriptomoeda, Criptomoeda, \
    TransferenciaCriptomoeda
from bagogold.criptomoeda.utils import \
    calcular_qtd_moedas_ate_dia_por_criptomoeda
from django import forms
from django.forms import widgets

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoCriptomoedaForm(LocalizedModelForm):
    moeda_utilizada = forms.ChoiceField(required=False)
    taxa = forms.DecimalField(min_value=0,  max_digits=21, decimal_places=12)
    taxa_moeda = forms.ChoiceField(required=False)
    
    class Meta:
        model = OperacaoCriptomoeda
        fields = ('tipo_operacao', 'quantidade', 'preco_unitario', 'data', 'criptomoeda',)
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        labels = {'criptomoeda': 'Criptomoeda'}
    
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
        self.fields['taxa_moeda'].choices = escolhas_moeda
        self.fields['taxa_moeda'].label = 'Moeda da taxa'

    def clean(self):
        data = super(OperacaoCriptomoedaForm, self).clean()
        # Taxas não podem ser maiores do que os valores movimentados na operação
        if data.get('taxa') >= data.get('quantidade'):
            raise forms.ValidationError('A taxa na moeda comprada/vendida deve ser menor que a quantidade comprada/vendida')
        # A taxa deve ser em alguma das moedas envolvidas na operação
        if data.get('taxa_moeda') not in [str(data.get('criptomoeda').id), data.get('moeda_utilizada')]:
            raise forms.ValidationError('A taxa deve ser em alguma das moedas envolvidas na operação')
        
        # Testa se a moeda utilizada para operação e a moeda adquirida/vendida na operação são diferentes
        if data.get('moeda_utilizada').isdigit() and data.get('criptomoeda').id == int(data.get('moeda_utilizada')):
            raise forms.ValidationError('A moeda utilizada deve ser diferente da moeda comprada/vendida')
        
        # Verifica se é possível vender a criptomoeda apontada
        if data.get('tipo_operacao') == 'V' and calcular_qtd_moedas_ate_dia_por_criptomoeda(self.investidor, data.get('criptomoeda').id, data.get('data')) < data.get('quantidade'):
            raise forms.ValidationError('Não é possível vender a quantidade informada para %s' % (data.get('criptomoeda')))
            
class TransferenciaCriptomoedaForm(LocalizedModelForm):
    class Meta:
        model = TransferenciaCriptomoeda
        fields = ('moeda', 'data', 'quantidade', 'origem', 'destino', 'taxa',)
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
    class Media:
        js = ('js/bagogold/form_transferencia_criptomoeda.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(TransferenciaCriptomoedaForm, self).__init__(*args, **kwargs)
        escolhas_moeda = (('', 'R$ (Reais)'),)
        for criptomoeda in Criptomoeda.objects.all():
            escolhas_moeda += ((criptomoeda.id, '%s (%s)' % (criptomoeda.ticker, criptomoeda.nome)),)
        self.fields['moeda'].choices = escolhas_moeda
        
    def clean(self):
        data = super(TransferenciaCriptomoedaForm, self).clean()
        if data.get('origem') == data.get('destino'):
            raise forms.ValidationError('Origem deve ser diferente de destino')
        
        if data.get('taxa') > data.get('quantidade'):
            raise forms.ValidationError('Taxa não pode ser maior que a quantidade transferida')
        
        # Testar se o campo criptomoeda foi preenchido, se não, transferência de reais
        if data.get('criptomoeda') and data.get('quantidade') > calcular_qtd_moedas_ate_dia_por_criptomoeda(self.investidor, data.get('criptomoeda').id, data.get('data')):
            raise forms.ValidationError('Não é possível transferir quantidade informada. Quantidade em %s: %s %s' % (data.get('data').strftime('%d/%m/%Y'), data.get('quantidade'), data.get('criptomoeda').ticker))
        
class OperacaoCriptomoedaLoteForm(forms.Form):
    divisao = forms.ModelChoiceField(queryset=None, label=u'Divisão')
    operacoes_lote = forms.CharField(label=u'Operações', widget=forms.Textarea)
    
    class Media:
        js = ('js/bagogold/form_operacao_criptomoeda_lote.min.js',)
    
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoCriptomoedaLoteForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)

    def clean(self):
        data = super(OperacaoCriptomoedaLoteForm, self).clean()
        
class TransferenciaCriptomoedaLoteForm(forms.Form):
    divisao = forms.ModelChoiceField(queryset=None, label=u'Divisão')
    transferencias_lote = forms.CharField(label=u'Transferências', widget=forms.Textarea)
    
    class Media:
        js = ('js/bagogold/form_transferencia_criptomoeda_lote.min.js',)
    
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(TransferenciaCriptomoedaLoteForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['divisao'].queryset = Divisao.objects.filter(investidor=self.investidor)

    def clean(self):
        data = super(TransferenciaCriptomoedaLoteForm, self).clean()        
