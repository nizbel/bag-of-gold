# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.acoes import Provento
from bagogold.bagogold.models.fii import ProventoFII
from bagogold.bagogold.models.gerador_proventos import \
    ProventoAcaoDescritoDocumentoBovespa, AcaoProventoAcaoDescritoDocumentoBovespa, \
    ProventoFIIDescritoDocumentoBovespa, SelicProventoAcaoDescritoDocBovespa
from django import forms
from django.forms import widgets


class ProventoAcaoDescritoDocumentoBovespaForm(LocalizedModelForm):
    class Meta:
        model = ProventoAcaoDescritoDocumentoBovespa
        fields = ('valor_unitario', 'data_ex', 'data_pagamento', 'tipo_provento',
                  'acao',)
        widgets={'data_ex': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'data_pagamento': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_provento': widgets.Select(choices=Provento.ESCOLHAS_TIPO_PROVENTO_ACAO),}
        
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

class SelicProventoAcaoDescritoDocBovespaForm(LocalizedModelForm):
    class Meta:
        model = SelicProventoAcaoDescritoDocBovespa
        fields = ('data_inicio', 'data_fim',)
        
    def clean(self):
        data = super(SelicProventoAcaoDescritoDocBovespaForm, self).clean()
        if data.get('data_inicio') is not None and data.get('data_fim') is not None:
            if data.get('data_inicio') > data.get('data_fim'):
                raise forms.ValidationError('Data de início da atualização pela Selic deve ser anterior à data final')
            
        print 'tipo de provento', self.instance.provento.tipo_provento
        if self.instance.provento.tipo_provento == 'A':
            raise forms.ValidationError('Proventos em ações não podem ser atualizados pela Selic')

class ProventoFIIDescritoDocumentoBovespaForm(LocalizedModelForm):
    class Meta:
        model = ProventoFIIDescritoDocumentoBovespa
        fields = ('valor_unitario', 'data_ex', 'data_pagamento', 'tipo_provento',
                  'fii',)
        widgets={'data_ex': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'data_pagamento': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_provento': widgets.Select(choices=ProventoFII.ESCOLHAS_TIPO_PROVENTO_FII),}
        
    def clean(self):
        dados = super(ProventoFIIDescritoDocumentoBovespaForm, self).clean()
        data_ex = dados.get('data_ex')
        data_pagamento = dados.get('data_pagamento')
        if (data_ex > data_pagamento):
            raise forms.ValidationError("Data EX deve ser anterior a data de pagamento")
        return dados