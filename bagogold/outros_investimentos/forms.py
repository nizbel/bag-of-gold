# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.outros_investimentos.models import Investimento, Rendimento, \
    Amortizacao, ImpostoRendaRendimento
from decimal import Decimal
from django import forms
from django.forms import widgets
import datetime

class InvestimentoForm(LocalizedModelForm):
    taxa = forms.DecimalField(min_value=0,  max_digits=9, decimal_places=2)
    
    class Meta:
        model = Investimento
        fields = ('nome', 'descricao', 'quantidade', 'data')
    
    class Media:
        js = ('js/bagogold/form_investimento.min.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(InvestimentoForm, self).__init__(*args, **kwargs)

class AmortizacaoForm(LocalizedModelForm):
    class Meta:
        model = Amortizacao
        fields = ('investimento', 'valor', 'data')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'})}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        self.investimento = kwargs.pop('investimento')
        # first call parent's constructor
        super(AmortizacaoForm, self).__init__(*args, **kwargs)
        self.fields['investimento'].disabled = True
        
        
    def clean_investimento(self):
        investimento = self.cleaned_data['investimento']
        if investimento.investidor != self.investidor:
            raise forms.ValidationError('Investimento inválido')
        if hasattr(self.instance, 'investimento') and investimento != self.instance.investimento:
            raise forms.ValidationError('Investimento não deve ser alterado')
        return investimento
        
    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor <= 0:
            raise forms.ValidationError('Valor da amortização deve ser maior que zero')
        return valor
    
    def clean(self):
        cleaned_data = super(AmortizacaoForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if Amortizacao.objects.filter(investimento=cleaned_data.get('investimento'), data=cleaned_data.get('data')).exists() \
            and Amortizacao.objects.get(investimento=cleaned_data.get('investimento'), data=cleaned_data.get('data')).investimento.id != self.investimento.id:
            raise forms.ValidationError('Já existe uma amortização para essa data')

class RendimentoForm(LocalizedModelForm):
    ESCOLHAS_IMPOSTO_RENDA = ((ImpostoRendaRendimento.TIPO_SEM_IMPOSTO, 'Sem imposto'),
                              (ImpostoRendaRendimento.TIPO_LONGO_PRAZO, 'Longo prazo'),
                              (ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO, 'Percentual específico'))
    
    imposto_renda = forms.ChoiceField(choices=ESCOLHAS_IMPOSTO_RENDA)
    percentual_imposto = forms.DecimalField(min_value=Decimal('0.001'), max_digits=5, decimal_places=3, required=False)
    
    class Meta:
        model = Rendimento
        fields = ('investimento', 'valor', 'data', 'imposto_renda')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'})}
        labels={'imposto_renda': u'Imposto de Renda', 'percentual_imposto': u'Percentual do IR'}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        self.investimento = kwargs.pop('investimento')
        # first call parent's constructor
        super(RendimentoForm, self).__init__(*args, **kwargs)
        self.fields['investimento'].disabled = True
        
    def clean_investimento(self):
        investimento = self.cleaned_data['investimento']
        if investimento.investidor != self.investidor:
            raise forms.ValidationError('Investimento inválido')
        if hasattr(self.instance, 'investimento') and investimento != self.instance.investimento:
            raise forms.ValidationError('Investimento não deve ser alterado')
        return investimento
        
    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor <= 0:
            raise forms.ValidationError('Valor do rendimento deve ser maior que zero')
        return valor
    
    def clean(self):
        cleaned_data = super(RendimentoForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if Rendimento.objects.filter(investimento=cleaned_data.get('investimento'), data=cleaned_data.get('data')).exists() \
            and Rendimento.objects.get(investimento=cleaned_data.get('investimento'), data=cleaned_data.get('data')).investimento.id != self.investimento.id:
            raise forms.ValidationError('Já existe um rendimento para essa data')
        
        # Garantir que percentual foi definido caso tenha sido escolhido IR com percentual específico
        imposto_renda = cleaned_data.get('imposto_renda')
        # Garantir que o percentual de imposto 
        if imposto_renda == ImpostoRendaRendimento.TIPO_PERC_ESPECIFICO:
            percentual_imposto = cleaned_data.get('percentual_imposto')
            if percentual_imposto == None or 0:
                raise forms.ValidationError('É necessário definir o percentual de imposto para o tipo de imposto de renda selecionado')
        
        
class EncerramentoForm(LocalizedModelForm):
    amortizacao = forms.DecimalField(min_value=0,  max_digits=9, decimal_places=2)

    class Meta:
        model = Investimento
        fields = ('data_encerramento',)
        widgets={'data_encerramento': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'})}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(EncerramentoForm, self).__init__(*args, **kwargs)
        self.fields['data_encerramento'].required = True
        self.fields['amortizacao'].required = False
        self.fields['amortizacao'].label = u'Amortização'
        
    def clean_amortizacao(self):
        valor = self.cleaned_data['amortizacao']
        if valor < 0:
            raise forms.ValidationError('Valor da amortização deve ser pelo menos igual a zero')
        return valor
    
    def clean(self):
        cleaned_data = super(EncerramentoForm, self).clean()
        if cleaned_data.get('data_encerramento'):
#             data_encerramento = datetime.datetime.strptime(cleaned_data.get('data_encerramento'), '%d/%m/%Y')
            if self.instance.data >= cleaned_data.get('data_encerramento'):
                raise forms.ValidationError('Data de encerramento deve ser posterior à data de início do investimento, %s' % (self.instance.data.strftime('%d/%m/%Y')))
            # Verificar se não há amortização posterior ao fim do rendimento
            if self.instance.amortizacao_set.filter(data__gt=cleaned_data.get('data_encerramento')).exists():
                raise forms.ValidationError('Há uma data de amortização cadastrada em data posterior a data de encerramento informada')
        