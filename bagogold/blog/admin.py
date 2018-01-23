# -*- coding: utf-8 -*-
from bagogold.blog.models import Postagem, Categoria, CategoriaPostagem
from django.contrib import admin

class PostagemAdmin(admin.ModelAdmin):
    search_fields = ['titulo', 'data']
    # TODO adicionar categorias
    list_display = ('titulo', 'slug', 'data')
    
admin.site.register(Postagem, PostagemAdmin)
    
admin.site.register(Categoria)

admin.site.register(CategoriaPostagem)

