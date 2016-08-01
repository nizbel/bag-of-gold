# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User



class DadosCadastraisForm(forms.ModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username')
        super(DadosCadastraisForm, self).__init__(*args, **kwargs)
        if self.initial['email'] and self.initial['email'] != '':
            self.fields['email'].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email=email).exclude(username=self.username):
            raise forms.ValidationError('Este email já está em uso, por favor insira outro email')
        return email
