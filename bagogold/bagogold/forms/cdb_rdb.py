# -*- coding: utf-8 -*-
from bagogold.bagogold.models.cdb import HistoricoPorcentagemCDB, OperacaoCDB
from bagogold.bagogold.models.rdb import HistoricoCarenciaRDB, OperacaoRDB
from django import forms
from django.forms import widgets


ESCOLHAS_CDB_RDB=((1, 'CDB'), 
                  (2, 'RDB'))

ESCOLHAS_TIPO_RENDIMENTO=((1, 'Pré-fixado'), 
                            (2, 'Pós-fixado'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class CDBRDBForm(forms.Form):
    tipo = forms.ChoiceField(label='Tipo', choices=ESCOLHAS_CDB_RDB)
    nome = forms.CharField(label='Nome', max_length=50)
    tipo_rendimento = forms.ChoiceField(label='Tipo de rendimento', choices=ESCOLHAS_TIPO_RENDIMENTO)

class OperacaoCDBForm(forms.ModelForm):
    # Campo verificado apenas no caso de venda de operação de cdb/rdb
    operacao_compra = forms.ModelChoiceField(label='Operação de compra',queryset=OperacaoCDB.objects.filter(tipo_operacao='C'), required=False)
    
    class Meta:
        model = OperacaoCDB
        fields = ('tipo_operacao', 'quantidade', 'data', 'operacao_compra',
                  'cdb')
        labels = {'cdb': 'CDB'}
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/cdb.js',)
        
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(OperacaoCDBForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['cdb'].required = False
        self.fields['tipo_operacao'].widget.attrs.update({'id' : 'id_tipo_operacao_cdb'})
        self.fields['operacao_compra'].widget.attrs.update({'id' : 'id_operacao_compra_cdb'})
        self.fields['data'].widget.attrs.update({'id' : 'id_data_cdb'})
        self.fields['quantidade'].widget.attrs.update({'id' : 'id_quantidade_cdb'})
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
    
class OperacaoRDBForm(forms.ModelForm):
    # Campo verificado apenas no caso de venda de operação de cdb/rdb
    operacao_compra = forms.ModelChoiceField(label='Operação de compra',queryset=OperacaoRDB.objects.filter(tipo_operacao='C'), required=False)
    
    class Meta:
        model = OperacaoRDB
        fields = ('tipo_operacao', 'quantidade', 'data', 'operacao_compra',
                  'rdb')
        labels = {'rdb': 'RDB'}
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        
    class Media:
        js = ('js/bagogold/rdb.js',)
        
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(OperacaoRDBForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields['rdb'].required = False
        self.fields['tipo_operacao'].widget.attrs.update({'id' : 'id_tipo_operacao_rdb'})
        self.fields['operacao_compra'].widget.attrs.update({'id' : 'id_operacao_compra_rdb'})
        self.fields['data'].widget.attrs.update({'id' : 'id_data_rdb'})
        self.fields['quantidade'].widget.attrs.update({'id' : 'id_quantidade_rdb'})
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

    def clean_rdb(self):
        tipo_operacao = self.cleaned_data['tipo_operacao']
        if tipo_operacao == 'V':
            rdb = self.cleaned_data.get('operacao_compra').rdb
        else:
            rdb = self.cleaned_data.get('rdb')
        if rdb is None:
            raise forms.ValidationError('Insira RDB válido')
              
        return rdb

class HistoricoPorcentagemForm(forms.Form):
    porcentagem = forms.DecimalField(label='Porcentagem de rendimento', max_digits=5, decimal_places=2)
    
class HistoricoCarenciaForm(forms.Form):
    carencia = forms.IntegerField(label='Período de carência (em dias)')
