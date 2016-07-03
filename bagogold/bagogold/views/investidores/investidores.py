# -*- coding: utf-8 -*-
from django.contrib.auth import views
from django.contrib import messages


def logout(request, *args, **kwargs):
    messages.success(request, 'Logout feito com sucesso')
    return views.logout(request, *args, **kwargs)