# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.fundo_investimento.models import FundoInvestimento, \
    OperacaoFundoInvestimento, HistoricoValorCotas
from bagogold.fundo_investimento.utils import \
    calcular_qtd_cotas_ate_dia_por_fundo
from django import forms
from django.forms import widgets
import datetime

ESCOLHAS_TIPO_PRAZO=(('L', 'Longo prazo'), 
                            ('C', 'Curto prazo'))

ESCOLHAS_TIPO_OPERACAO=(('C', "Compra"),
                        ('V', "Venda"))

class OperacaoFundoInvestimentoForm(LocalizedModelForm):
    
    class Meta:
        model = OperacaoFundoInvestimento
        fields = ('tipo_operacao', 'quantidade', 'valor', 'data', 'fundo_investimento')
        widgets={'data': widgets.DateInput(attrs={'class':'datepicker', 
                                            'placeholder':'Selecione uma data'}),
                 'tipo_operacao': widgets.Select(choices=ESCOLHAS_TIPO_OPERACAO),}
        labels = {'fundo_investimento': 'Fundo de investimento',}
    
    class Media:
        js = ('js/bagogold/form_operacao_fundo_investimento.min.js',)
        
    def __init__(self, *args, **kwargs):
        self.investidor = kwargs.pop('investidor')
        # first call parent's constructor
        super(OperacaoFundoInvestimentoForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
#         self.fields['fundo_investimento'].queryset = FundoInvestimento.objects.filter(investidor=self.investidor)
        
    def clean(self):
        dados = super(OperacaoFundoInvestimentoForm, self).clean()
        data = dados.get('data')
        # Testa se não se trata de uma edição de compra para venda
        if dados.get('tipo_operacao') == 'V':
            if self.instance.tipo_operacao == 'C':
                # Verificar se já há vendas registradas para essa compra, se sim, lançar erro
                if calcular_qtd_cotas_ate_dia_por_fundo(self.investidor, self.instance.fundo_investimento.id, datetime.date.today()) - self.instance.quantidade < 0:
                    raise forms.ValidationError('Não é possível alterar tipo de operação pois a quantidade atual para o fundo %s seria negativa' % (self.instance.fundo_investimento))
            # Verifica se é possível vender o fundo apontado
            if calcular_qtd_cotas_ate_dia_por_fundo(self.investidor, dados.get('fundo_investimento').id, data) < dados.get('quantidade'):
                raise forms.ValidationError('Não é possível vender a quantidade informada para o fundo %s' % (dados.get('fundo_investimento')))
