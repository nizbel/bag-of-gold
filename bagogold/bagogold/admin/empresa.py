# -*- coding: utf-8 -*-
from bagogold.bagogold.models.empresa import Empresa
from django.contrib import admin


class EmpresaAdmin(admin.ModelAdmin):
    search_fields = ['nome']
    list_display = ('nome', 'nome_pregao', 'codigo_cvm')
    
admin.site.register(Empresa, EmpresaAdmin)

