# -*- coding: utf-8 -*-
from bagogold.blog.models import Post, Tag, TagPost
from django.contrib import admin

class PostAdmin(admin.ModelAdmin):
    search_fields = ['titulo', 'data']
    # TODO adicionar Tags
    list_display = ('titulo', 'slug', 'data', 'chamada_facebook')
    
admin.site.register(Post, PostAdmin)
    
admin.site.register(Tag)

admin.site.register(TagPost)

