# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.acoes import Provento
from django import forms
from django.forms import widgets


class ProventoAcaoForm(LocalizedModelForm):
    class Meta:
        model = Provento
        fields = ('valor_unitario', 'data_ex', 'data_pagamento', 'tipo_provento',
                  'acao',)
        widgets={'data_ex': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'data_pagamento': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_provento': widgets.Select(choices=Provento.ESCOLHAS_TIPO_PROVENTO_ACAO),}
        
    def clean(self):
        dados = super(ProventoAcaoForm, self).clean()
        data_ex = dados.get('data_ex')
        data_pagamento = dados.get('data_pagamento')
#         print '%s %s %s' % (data_ex, data_pagamento, data_ex < data_pagamento)
        if (data_ex > data_pagamento):
            raise forms.ValidationError("Data EX deve ser anterior a data de pagamento")
        return dados
