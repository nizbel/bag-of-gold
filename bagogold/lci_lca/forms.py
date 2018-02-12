# -*- coding: utf-8 -*-
from bagogold.blog.models import Tag, Post
from django import forms

class PostForm(forms.ModelForm):
    tags = forms.MultipleChoiceField(choices=[(tag.id, tag.nome) for tag in Tag.objects.all().order_by('nome')])
    
    class Meta:
        model = Post
        fields = ('titulo', 'conteudo', 'chamada_facebook', 'tags')
        
    class Media:
        js = ('js/bagogold/form_post_blog.min.js',)
        
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['chamada_facebook'].disabled = True
        
    def clean_tags(self):
        tags = self.cleaned_data['tags']
        
        if len(tags) != Tag.objects.filter(id__in=tags).count():
            raise ValueError('Tag inválida selecionada')
        
        return list(Tag.objects.filter(id__in=tags))
    
