# -*- coding: utf-8 -*-
from bagogold.models.divisoes import Divisao
from django import forms

class DivisaoForm(forms.ModelForm):

    class Meta:
        model = Divisao
        fields = ('nome', 'valor_objetivo')