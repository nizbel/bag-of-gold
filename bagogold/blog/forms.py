# -*- coding: utf-8 -*-
from bagogold.blog.models import Tag, Post
from django import forms

class PostForm(forms.ModelForm):
    tags = forms.MultipleChoiceField(required=False, choices=[(tag.id, tag.nome) for tag in Tag.objects.all().order_by('nome')])
    
    class Meta:
        model = Post
        fields = ('titulo', 'conteudo', 'chamada_facebook', 'tags')
        
    class Media:
        js = ('js/bagogold/form_post_blog.min.js',)
        
    def clean_tags(self):
        tags = self.cleaned_data['tags']
        print tags
        
        return tags
    
