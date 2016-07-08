# -*- coding: utf-8 -*-
from bagogold.bagogold.models.investidores import Investidor
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
   
admin.site.register(Investidor)

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class UserInvestidorInline(admin.StackedInline):
    model = Investidor
    can_delete = False
    verbose_name_plural = 'investidores'
  
# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserInvestidorInline, )
  
# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
