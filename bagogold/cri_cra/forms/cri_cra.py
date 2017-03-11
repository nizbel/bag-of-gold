# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.cri_cra.models.cri_cra import CRI_CRA, DataRemuneracaoCRI_CRA, \
    DataAmortizacaoCRI_CRA, OperacaoCRI_CRA
from bagogold.cri_cra.utils.utils import \
    quantidade_cri_cra_na_data_por_certificado
from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.forms import widgets

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class CRI_CRAForm(LocalizedModelForm):
    class Meta:
        model = CRI_CRA
        fields = ('nome', 'codigo_isin', 'tipo', 'tipo_indexacao', 'porcentagem', 'juros_adicional', 'data_emissao',
                  'valor_emissao', 'data_vencimento')
        widgets={'tipo': widgets.Select(choices=CRI_CRA.ESCOLHAS_TIPO_CRI_CRA),
                 'tipo_indexacao': widgets.Select(choices=CRI_CRA.ESCOLHAS_TIPO_INDEXACAO),}
        
    class Media:
        js = ('js/bagogold/form_cri_cra.js',)

class OperacaoCRI_CRAForm(LocalizedModelForm):
    class Meta:
        model = OperacaoCRI_CRA
        fields = ('tipo_operacao', 'quantidade', 'preco_unitario', 'data', 'cri_cra')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoCRI_CRAForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['cri_cra'].required = False
        self.fields['cri_cra'].queryset = CRI_CRA.objects.filter(investidor=self.investidor)
    
    def clean(self):
        data = super(OperacaoCRI_CRAForm, self).clean()
        if data.get('tipo_operacao') == 'V':
            # Testa se quantidade da venda condiz com a quantidade que o investidor possui
            quantidade_atual = quantidade_cri_cra_na_data_por_certificado(data.get('data'), data.get('cri_cra'))
            # Se for uma operação de compra sendo convertida em venda, remover sua quantidade da quantidade atual
            if self.instance.tipo_operacao == 'C':
                quantidade_atual -= self.instance.quantidade
            if data.get('quantidade') > quantidade_atual:
                raise forms.ValidationError('Quantidade da venda é maior do que %s, quantidade possuída na data %s' % (quantidade_atual, data.get('data')))
            
class DataRemuneracaoCRI_CRAForm(LocalizedModelForm):
    
    class Meta:
        model = DataRemuneracaoCRI_CRA
        fields = ('data', 'cri_cra')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.cri_cra = kwargs.pop('cri_cra')
        except:
            self.cri_cra = None
        super(DataRemuneracaoCRI_CRAForm, self).__init__(*args, **kwargs)
        if self.cri_cra:
            self.fields['cri_cra'].disabled = True
    
    def clean_cri_cra(self):
        if self.cleaned_data['cri_cra'].investidor != self.investidor:
            raise forms.ValidationError('CRI/CRA inválido')
        return self.cleaned_data['cri_cra']
    
    def clean(self):
        cleaned_data = super(DataRemuneracaoCRI_CRAForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if DataRemuneracaoCRI_CRA.objects.filter(cri_cra=cleaned_data.get('cri_cra'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Data de rendimento selecionada já foi cadastrada')
        return cleaned_data
    
# Inline FormSet para datas de remuneração
class DataRemuneracaoCRI_CRAFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        datas_remuneracao = list()
        for form_remuneracao in self.forms:
            if form_remuneracao.is_valid():
                # Verifica se pode passar pelo form
                if not (form_remuneracao.instance.id == None and not form_remuneracao.has_changed()):
                    data = form_remuneracao.cleaned_data.get('data')
                    cri_cra = form_remuneracao.cleaned_data.get('cri_cra')
                    if data <= cri_cra.data_emissao or data > cri_cra.data_vencimento:
                        raise ValidationError('Data de remuneração %s está fora do período de duração do %s' % (data.strftime('%d/%m/%Y'), cri_cra.descricao_tipo()))
                    if data in datas_remuneracao:
                        raise ValidationError('%s já possui remuneração cadastrada para a data %s' % (cri_cra.descricao_tipo(), data.strftime('%d/%m/%Y')))
                    datas_remuneracao.append(data)
           
            
        
class DataAmortizacaoCRI_CRAForm(LocalizedModelForm):
    
    class Meta:
        model = DataAmortizacaoCRI_CRA
        fields = ('data', 'cri_cra', 'percentual')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        try:
            self.inicial = kwargs.pop('inicial')
        except:
            self.inicial = False
        try:
            self.cri_cra = kwargs.pop('cri_cra')
        except:
            self.cri_cra = None
        super(DataAmortizacaoCRI_CRAForm, self).__init__(*args, **kwargs)
        if self.cri_cra:
            self.fields['cri_cra'].disabled = True
    
    def clean_cri_cra(self):
        if self.cleaned_data['cri_cra'].investidor != self.investidor:
            raise forms.ValidationError('CRI/CRA inválido')
        return self.cleaned_data['cri_cra']
    
    def clean(self):
        cleaned_data = super(DataAmortizacaoCRI_CRAForm, self).clean()
        # Testar se já existe algum histórico para o investimento na data
        if DataAmortizacaoCRI_CRA.objects.filter(cri_cra=cleaned_data.get('cri_cra'), data=cleaned_data.get('data')).exists():
            raise forms.ValidationError('Data de rendimento selecionada já foi cadastrada')
        return cleaned_data
    
# Inline FormSet para datas de amortização
class DataAmortizacaoCRI_CRAFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        datas_amortizacao = list()
        total_amortizacao = Decimal(0)
        for form_amortizacao in self.forms:
            if form_amortizacao.is_valid():
                # Verifica se pode passar pelo form
                if not (form_amortizacao.instance.id == None and not form_amortizacao.has_changed()):
#                     print form_divisao.cleaned_data.get('quantidade')
                    data = form_amortizacao.cleaned_data.get('data')
                    cri_cra = form_amortizacao.cleaned_data.get('cri_cra')
                    percentual = form_amortizacao.cleaned_data.get('percentual')
                    if percentual <= 0:
                        raise ValidationError('Percentual de amortização deve ser maior que 0')
                    if data <= cri_cra.data_emissao or data >= cri_cra.data_vencimento:
                        raise ValidationError('Data de remuneração %s está fora do período de duração do %s' % (data, cri_cra.descricao_tipo()))
                    if data in datas_amortizacao:
                        raise ValidationError('%s já possui amortização cadastrada para a data %s' % (cri_cra.descricao_tipo(), data.strftime('%d/%m/%Y')))
                    datas_amortizacao.append(data)
                    total_amortizacao += percentual
                    # Não se pode amortizar mais de 100%
                    if total_amortizacao > 100:
                        raise ValidationError('Total amortizado não pode superar 100%')