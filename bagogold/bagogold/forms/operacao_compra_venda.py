# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.acoes import OperacaoCompraVenda, OperacaoAcao
from django import forms
from django.db.models import Sum
from django.forms import widgets


ESCOLHAS_DAYTRADE=(
        (False, 'Não'),
        (True, 'Sim'),
        )

class OperacaoCompraVendaForm(LocalizedModelForm):

    class Meta:
        model = OperacaoCompraVenda
        fields = ('compra', 'venda', 'day_trade', 'quantidade')
        widgets={'day_trade': widgets.Select(choices=ESCOLHAS_DAYTRADE),}
    
    def __init__(self, *args, **kwargs):
        # Pegar investidor atual
        self.investidor = kwargs.pop('investidor')
        
        super(OperacaoCompraVendaForm, self).__init__(*args, **kwargs)
        
        # lista de compras
        operacoes_compra = OperacaoAcao.objects.filter(investidor=self.investidor, tipo_operacao='C', destinacao='T')
        self.fields['compra'].choices = [] if not self.instance.id else [[self.instance.compra.id, self.instance.compra]]
        for operacao in operacoes_compra:
            adicionar = True
            if operacao.compra.get_queryset():
                if operacao.compra.get_queryset().aggregate(total_venda=Sum('quantidade'))['total_venda'] == operacao.quantidade:
                    adicionar = False
            if adicionar:
                self.fields['compra'].choices += [[operacao.id, operacao]]
        
        # lista de vendas
        operacoes_venda = OperacaoAcao.objects.filter(investidor=self.investidor, tipo_operacao='V', destinacao='T')
        self.fields['venda'].choices = [] if not self.instance.id else [[self.instance.venda.id, self.instance.venda]]
        for operacao in operacoes_venda:
            adicionar = True
            if operacao.venda.get_queryset():
                if operacao.venda.get_queryset().aggregate(total_compra=Sum('quantidade'))['total_compra'] == operacao.quantidade:
                    adicionar = False
            if adicionar:
                self.fields['venda'].choices += [[operacao.id, operacao]]
    
    def clean(self):
        data = super(OperacaoCompraVendaForm, self).clean()
        compra = data['compra']
        venda = data['venda']
        day_trade = data['day_trade']
        quantidade = data['quantidade']
        
        if compra.acao != venda.acao:
            raise forms.ValidationError('Compra e venda devem ser da mesma ação')
        elif compra.data != venda.data and day_trade:
            raise forms.ValidationError('Operações de day trade devem ser feitas no mesmo dia')
        elif compra.data == venda.data and not day_trade:
            raise forms.ValidationError('Operações feitas no mesmo dia configuram day trade')
        elif quantidade > compra.quantidade - (compra.compra.get_queryset().aggregate(total_venda=Sum('quantidade'))['total_venda'] or 0):
            raise forms.ValidationError('Quantidade negociada entre compra/venda maior que a quantidade da compra')
        elif quantidade > venda.quantidade - (venda.venda.get_queryset().aggregate(total_compra=Sum('quantidade'))['total_compra'] or 0):
            raise forms.ValidationError('Quantidade negociada entre compra/venda maior que a quantidade da venda')

        #always return the cleaned data
        return data
