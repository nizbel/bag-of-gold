# # -*- coding: utf-8 -*-
# from bagogold.bagogold.forms.utils import LocalizedModelForm
# from bagogold.fii.models import OperacaoFII, ProventoFII, \
#     UsoProventosOperacaoFII
# from decimal import Decimal
# from django import forms
# from django.forms import widgets
# 
# 
# ESCOLHAS_CONSOLIDADO=(
#         (True, "Sim"),
#         (False, "Não"),
#         )
# 
# ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
#                         ('V', "Venda"))
# 
# class ProventoFIIForm(LocalizedModelForm):
# 
# 
#     class Meta:
#         model = ProventoFII
#         fields = ('valor_unitario', 'tipo_provento', 'data_ex', 'data_pagamento', 'fii', )
#         widgets={'data_ex': widgets.DateInput(attrs={'class':'datepicker', 
#                                             'placeholder':'Selecione uma data'}),
#                  'data_pagamento': widgets.DateInput(attrs={'class':'datepicker', 
#                                             'placeholder':'Selecione uma data'}),
#                  'tipo_provento': widgets.Select(choices=ProventoFII.ESCOLHAS_TIPO_PROVENTO_FII),}
#         
#     
#     
# class OperacaoFIIForm(LocalizedModelForm):
#     
#     class Meta:
#         model = OperacaoFII
#         fields = ('preco_unitario', 'quantidade', 'data', 'corretagem', 'emolumentos', 'tipo_operacao',
#                   'fii', 'consolidada')
#         widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
#                                             'placeholder':'Selecione uma data'}),
#                  'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),
#                  'consolidada': widgets.Select(choices=ESCOLHAS_CONSOLIDADO),}
#         
#     class Media:
#         js = ('js/bagogold/calculo_emolumentos.min.js', 
#               'js/bagogold/form_operacao_fii.min.js',)
#         
#     def clean(self):
#         data = super(OperacaoFIIForm, self).clean()
#         if data.get('consolidada') is True:
#             if data.get('data') is None:
#                 raise forms.ValidationError('Operações consolidadas precisam de uma data definida')
# 
#         return data
#     
#     
# class UsoProventosOperacaoFIIForm(LocalizedModelForm):
# 
# 
#     class Meta:
#         model = UsoProventosOperacaoFII
#         fields = ('qtd_utilizada', )
#     
#     def __init__(self, *args, **kwargs):
#         super(UsoProventosOperacaoFIIForm, self).__init__(*args, **kwargs)
#         self.fields['qtd_utilizada'].required = False
#         
#     def clean(self):
#         data = super(UsoProventosOperacaoFIIForm, self).clean()
#         if data.get('qtd_utilizada') is not None:
#             if data.get('qtd_utilizada') < 0:
#                 raise forms.ValidationError('Quantidade de proventos utilizada não pode ser negativa')
#             qtd_utilizada = str(data.get('qtd_utilizada'))
#             qtd_utilizada = qtd_utilizada.replace(",", ".")
#             qtd_utilizada = Decimal(qtd_utilizada)
#             data['qtd_utilizada'] = qtd_utilizada
#         else:
#             data['qtd_utilizada'] = 0
# 
#         return data
#     
# class CalculoResultadoCorretagemForm(forms.Form):
#     def __new__(cls, *args, **kwargs):
#         new_class = super(CalculoResultadoCorretagemForm, cls).__new__(cls, *args, **kwargs)
#         for field in new_class.base_fields.values():
#             if isinstance(field, forms.DecimalField):
#                 field.localize = True
#                 field.widget.is_localized = True
#         return new_class
# #     NUM_MESES = 500
# #     PRECO_COTA = 97
# #     CORRETAGEM = 9.8
# #     RENDIMENTO = 0.78
# #     QTD_COTAS = 4
#     num_meses = forms.IntegerField(label='Quantidade de meses', min_value=1, max_value=1000)
#     preco_cota = forms.DecimalField(label='Preço da cota', max_digits=11, decimal_places=2, min_value=0)
#     corretagem = forms.DecimalField(label='Corretagem (em R$)', max_digits=9, decimal_places=2, min_value=0)
#     rendimento = forms.DecimalField(label='Rendimento (em R$)', max_digits=9, decimal_places=2, min_value=0)
#     quantidade_cotas = forms.IntegerField(label='Quantidade inicial de cotas', min_value=0, max_value=1000)
#     