# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.bagogold.utils.td import quantidade_titulos_ate_dia_por_titulo
from django import forms
from django.forms import widgets
import datetime


ESCOLHAS_CONSOLIDADO=(
        (True, "Sim"),
        (False, "Não"),
        )

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))
            
    
class OperacaoTituloForm(forms.ModelForm):
    
    class Meta:
        model = OperacaoTitulo
        fields = ('preco_unitario', 'quantidade', 'data', 'taxa_bvmf', 'taxa_custodia', 'tipo_operacao',
                  'titulo', 'consolidada',)
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),
                 'consolidada': widgets.Select(choices=ESCOLHAS_CONSOLIDADO),}

    class Media:
        js = ('js/bagogold/td.js',)

    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoTituloForm, self).__init__(*args, **kwargs)
        self.fields['titulo'].queryset = self.fields['titulo'].queryset.order_by('data_vencimento')

    def clean(self):
        dados = super(OperacaoTituloForm, self).clean()
        data = dados.get('data')
        data_vencimento = dados.get('titulo').data_vencimento
#         print '%s %s %s' % (data_ex, data_pagamento, data_ex < data_pagamento)
        if (data > data_vencimento):
            raise forms.ValidationError("Título não pode ter sido comprado após sua data de vencimento (%s)" % (dados.get('titulo').data_vencimento))
        # Testa se não se trata de uma edição de compra para venda
        if dados.get('tipo_operacao') == 'V':
            if self.instance.tipo_operacao == 'C':
                # Verificar se já há vendas registradas para essa compra, se sim, lançar erro
                if quantidade_titulos_ate_dia_por_titulo(self.investidor, self.instance.titulo.id, datetime.date.today()) - self.instance.quantidade < 0:
                    raise forms.ValidationError('Não é possível alterar tipo de operação pois a quantidade atual para o título %s seria negativa' % (self.instance.titulo))
            # Verifica se é possível vender o título apontado
            if quantidade_titulos_ate_dia_por_titulo(self.investidor, dados.get('titulo').id, data) < dados.get('quantidade'):
                raise forms.ValidationError('Não é possível vender a quantidade informada para o título %s' % (dados.get('titulo')))
