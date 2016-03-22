# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoCompraVenda, OperacaoAcao
from django import forms
from django.db.models import Sum
from django.forms import widgets


ESCOLHAS_DAYTRADE=(
        (False, "Não"),
        (True, "Sim"),
        )

class OperacaoCompraVendaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OperacaoCompraVendaForm, self).__init__(*args, **kwargs)

        # lista de compras
        operacoes_compra = OperacaoAcao.objects.filter(tipo_operacao='C', destinacao='T')
        self.fields["compra"].choices = []
        for operacao in operacoes_compra:
            adicionar = True
            if operacao.compra.get_queryset():
                if operacao.compra.get_queryset().aggregate(total_venda=Sum('venda__quantidade'))['total_venda'] == operacao.quantidade:
                    adicionar = False
            if adicionar:
                self.fields["compra"].choices += [[operacao.id, operacao]]
        
        # lista de vendas
        operacoes_venda = OperacaoAcao.objects.filter(tipo_operacao='V', destinacao='T')
        self.fields["venda"].choices = []
        for operacao in operacoes_venda:
            adicionar = True
            if operacao.venda.get_queryset():
                if operacao.venda.get_queryset().aggregate(total_compra=Sum('venda__quantidade'))['total_compra'] == operacao.quantidade:
                    adicionar = False
            if adicionar:
                self.fields["venda"].choices += [[operacao.id, operacao]]

    class Meta:
        model = OperacaoCompraVenda
        fields = ('compra', 'venda', 'day_trade', )
        widgets={'day_trade': widgets.Select(choices=ESCOLHAS_DAYTRADE),}
        
    def clean(self):
        data = super(OperacaoCompraVendaForm, self).clean()
        compra = data["compra"]
        venda = data["venda"]
        day_trade = data["day_trade"]
        
        if compra.acao != venda.acao:
            raise forms.ValidationError("Compra e venda devem ser da mesma ação")
        elif compra.data != venda.data and day_trade:
            raise forms.ValidationError("Operações de day trade devem ser feitas no mesmo dia")
        elif compra.data == venda.data and not day_trade:
            raise forms.ValidationError("Operações feitas no mesmo dia configuram day trade")

        #always return the cleaned data
        return data
