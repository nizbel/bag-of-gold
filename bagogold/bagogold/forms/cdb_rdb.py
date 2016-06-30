# -*- coding: utf-8 -*-
from bagogold.bagogold.models.cdb_rdb import CDB_RDB, OperacaoCDB_RDB, \
    HistoricoPorcentagemCDB_RDB, HistoricoCarenciaCDB_RDB
from django import forms
from django.forms import widgets


ESCOLHAS_CDB_RDB=(('C', 'CDB'), 
                  ('R', 'RDB'))

ESCOLHAS_TIPO_RENDIMENTO=((1, 'Pré-fixado'), 
                            (2, 'Pós-fixado'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class CDB_RDBForm(forms.ModelForm):
    class Meta:
        model = CDB_RDB
        fields = ('nome', 'tipo', 'tipo_rendimento')
        widgets={'tipo': widgets.Select(choices=ESCOLHAS_CDB_RDB),
                 'tipo_rendimento': widgets.Select(choices=ESCOLHAS_TIPO_RENDIMENTO),}

class OperacaoCDB_RDBForm(forms.ModelForm):
    # Campo verificado apenas no caso de venda de operação de cdb/rdb
    operacao_compra = forms.ModelChoiceField(label='Operação de compra',queryset=OperacaoCDB_RDB.objects.filter(tipo_operacao='C'), required=False)
    
    class Meta:
        model = OperacaoCDB_RDB
        fields = ('tipo_operacao', 'quantidade', 'data', 'operacao_compra',
                  'investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/cdb_rdb.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoCDB_RDBForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['investimento'].required = False
        self.fields['investimento'].queryset = CDB_RDB.objects.filter(investidor=self.investidor)
#         if self.instance.pk is not None:
#             # Verificar se é uma compra
#             if self.instance.tipo_operacao == 'V':
#                 self.operacao_compra.v
    
    def clean_operacao_compra(self):
        print 'test'
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            operacao_compra = self.cleaned_data.get('operacao_compra')
            # Testar se operacao_compra é válido
            if operacao_compra is None:
                raise forms.ValidationError('Selecione operação de compra válida')
            quantidade = self.cleaned_data['quantidade']
            if quantidade > operacao_compra.qtd_disponivel_venda():
                raise forms.ValidationError('Não é possível vender mais do que o disponível na operação de compra')
            return operacao_compra
        return None

    def clean_cdb(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            cdb = self.cleaned_data.get('operacao_compra').cdb
        else:
            cdb = self.cleaned_data.get('cdb')
        if cdb is None:
            raise forms.ValidationError('Insira CDB válido')
              
        return cdb
    

class HistoricoPorcentagemCDB_RDBForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoPorcentagemCDB_RDB
        fields = ('porcentagem', 'data',
                  'cdb_rdb')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}
        
class HistoricoCarenciaCDB_RDBForm(forms.ModelForm):
    
    class Meta:
        model = HistoricoCarenciaCDB_RDB
        fields = ('carencia', 'data',
                  'cdb_rdb')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),}