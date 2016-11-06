# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import \
    ProventoAcaoDescritoDocumentoBovespa, AcaoProventoAcaoDescritoDocumentoBovespa
from django import forms
from django.forms import widgets



ESCOLHAS_TIPO_PROVENTO=(('A', "Ações"),
                        ('D', "Dividendos"),
                        ('J', "Juros sobre capital próprio"),)

class ProventoAcaoDescritoDocumentoBovespaForm(forms.ModelForm):


    class Meta:
        model = ProventoAcaoDescritoDocumentoBovespa
        fields = ('valor_unitario', 'data_ex', 'data_pagamento', 'tipo_provento',
                  'acao',)
        widgets={'data_ex': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'data_pagamento': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_provento': widgets.Select(choices=ESCOLHAS_TIPO_PROVENTO),}
        
    def clean(self):
        dados = super(ProventoAcaoDescritoDocumentoBovespaForm, self).clean()
        data_ex = dados.get('data_ex')
        data_pagamento = dados.get('data_pagamento')
        if (data_ex > data_pagamento):
            raise forms.ValidationError("Data EX deve ser anterior a data de pagamento")
        return dados

class AcaoProventoAcaoDescritoDocumentoBovespaForm(forms.ModelForm):
    
    class Meta:
        model = AcaoProventoAcaoDescritoDocumentoBovespa
        fields = ('acao_recebida', 'data_pagamento_frac', 'valor_calculo_frac')
        widgets={'data_pagamento_frac': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'})}

#     def clean_acao_recebida(self):
#         print 'ENtrou no clean'
#         acao_recebida = self.cleaned_data['acao_recebida']
#         print acao_recebida
#         if not acao_recebida:
#             raise forms.ValidationError('Ação recebida não pode ser nula')
#         return acao_recebida
#     
#     def clean(self):
#         print 'Entrou no clean'
#         dados = super(AcaoProventoAcaoDescritoDocumentoBovespaForm, self).clean()
#         return dados