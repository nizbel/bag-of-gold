# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.gerador_proventos import \
    ProventoAcaoDescritoDocumentoBovespa, AcaoProventoAcaoDescritoDocumentoBovespa, \
    ProventoFIIDescritoDocumentoBovespa
from django import forms
from django.forms import widgets


ESCOLHAS_TIPO_PROVENTO_ACAO=(('A', "Ações"),
                        ('D', "Dividendos"),
                        ('J', "Juros sobre capital próprio"),)

ESCOLHAS_TIPO_PROVENTO_FII=(('R', "Rendimento"),
                        ('A', "Amortização"),)

class ProventoAcaoDescritoDocumentoBovespaForm(LocalizedModelForm):

    class Meta:
        model = ProventoAcaoDescritoDocumentoBovespa
        fields = ('valor_unitario', 'data_ex', 'data_pagamento', 'tipo_provento',
                  'acao',)
        widgets={'data_ex': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'data_pagamento': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_provento': widgets.Select(choices=ESCOLHAS_TIPO_PROVENTO_ACAO),}
        
    def clean(self):
        dados = super(ProventoAcaoDescritoDocumentoBovespaForm, self).clean()
        data_ex = dados.get('data_ex')
        data_pagamento = dados.get('data_pagamento')
        if (data_ex > data_pagamento):
            raise forms.ValidationError("Data EX deve ser anterior a data de pagamento")
        return dados

class AcaoProventoAcaoDescritoDocumentoBovespaForm(LocalizedModelForm):
    
    class Meta:
        model = AcaoProventoAcaoDescritoDocumentoBovespa
        fields = ('acao_recebida', 'data_pagamento_frac', 'valor_calculo_frac')
        widgets={'data_pagamento_frac': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'})}

class ProventoFIIDescritoDocumentoBovespaForm(LocalizedModelForm):

    class Meta:
        model = ProventoFIIDescritoDocumentoBovespa
        fields = ('valor_unitario', 'data_ex', 'data_pagamento',
                  'fii',)
        widgets={'data_ex': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'data_pagamento': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_provento': widgets.Select(choices=ESCOLHAS_TIPO_PROVENTO_FII),}
        
    def clean(self):
        dados = super(ProventoFIIDescritoDocumentoBovespaForm, self).clean()
        data_ex = dados.get('data_ex')
        data_pagamento = dados.get('data_pagamento')
        if (data_ex > data_pagamento):
            raise forms.ValidationError("Data EX deve ser anterior a data de pagamento")
        return dados