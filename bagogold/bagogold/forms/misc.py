# -*- coding: utf-8 -*-
from django import forms

class ContatoForm(forms.Form):
    nome = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    conteudo = forms.CharField(
        required=True,
        widget=forms.Textarea
    )