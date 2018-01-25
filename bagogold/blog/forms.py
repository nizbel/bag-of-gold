# -*- coding: utf-8 -*-
from bagogold.blog.models import Tag, Post
from django import forms
from django.forms import widgets

class PostForm(forms.ModelForm):
    tags = forms.MultipleChoiceField(required=False, choices=Tag.objects.all())
    
    class Meta:
        model = Post
        fields = ('titulo', 'conteudo',)
        
