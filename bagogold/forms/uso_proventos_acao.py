# -*- coding: utf-8 -*-
from bagogold.models.acoes import UsoProventosOperacaoAcao
from django import forms
from django.forms import widgets


class UsoProventosOperacaoAcaoForm(forms.ModelForm):


    class Meta:
        model = UsoProventosOperacaoAcao
        fields = ('qtd_utilizada', )
            
    def clean(self):
        data = super(UsoProventosOperacaoAcaoForm, self).clean()
        if data.get('qtd_utilizada') is not None:
            qtd_utilizada = str(data.get('qtd_utilizada'))
            qtd_utilizada = qtd_utilizada.replace(",", ".")
            qtd_utilizada = float(qtd_utilizada)
            data['qtd_utilizada'] = qtd_utilizada

        return data
