# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.acoes import OperacaoAcao, \
    UsoProventosOperacaoAcao, AtualizacaoSelicProvento
from decimal import Decimal
from django import forms
from django.forms import widgets


ESCOLHAS_CONSOLIDADO=(
        (True, "Sim"),
        (False, "Não"),
        )

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoAcaoForm(LocalizedModelForm):


    class Meta:
        model = OperacaoAcao
        fields = ('preco_unitario', 'quantidade', 'data', 'corretagem', 'emolumentos', 'tipo_operacao',
                  'acao', 'consolidada')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),
                 'consolidada': widgets.Select(choices=ESCOLHAS_CONSOLIDADO),}
        
    class Media:
        js = ('js/bagogold/calculo_emolumentos.js', 
              'js/bagogold/form_operacao_acao.js',)
    
    def clean_preco_unitario(self):
        preco_unitario = Decimal(self.cleaned_data['preco_unitario'])
        if preco_unitario < Decimal(0):
            raise forms.ValidationError('Preço unitário deve ser maior ou igual a 0')
        return preco_unitario
    
    def clean(self):
        data = super(OperacaoAcaoForm, self).clean()
        if data.get('consolidada') and data.get('data') is None:
            raise forms.ValidationError('Data é obrigatória para operações consolidadas')
    
class UsoProventosOperacaoAcaoForm(LocalizedModelForm):
    class Meta:
        model = UsoProventosOperacaoAcao
        fields = ('qtd_utilizada', )
        
    def __init__(self, *args, **kwargs):
        super(UsoProventosOperacaoAcaoForm, self).__init__(*args, **kwargs)
        self.fields['qtd_utilizada'].required = False
            
    def clean(self):
        data = super(UsoProventosOperacaoAcaoForm, self).clean()
        if data.get('qtd_utilizada') is not None:
            if data.get('qtd_utilizada') < 0:
                raise forms.ValidationError('Quantidade de proventos utilizada não pode ser negativa')
            qtd_utilizada = str(data.get('qtd_utilizada'))
            qtd_utilizada = qtd_utilizada.replace(",", ".")
            qtd_utilizada = Decimal(qtd_utilizada)
            data['qtd_utilizada'] = qtd_utilizada
        else:
            data['qtd_utilizada'] = 0

class AtualizacaoSelicProventoForm(LocalizedModelForm):
    class Meta:
        model = AtualizacaoSelicProvento
        fields = ('data_inicio', 'data_fim',)
        
    def clean(self):
        data = super(AtualizacaoSelicProventoForm, self).clean()
        if data.get('data_inicio') is not None and data.get('data_fim') is not None:
            if data.get('data_inicio') > data.get('data_fim'):
                raise forms.ValidationError('Data de início da atualização pela Selic deve ser anterior à data final')
