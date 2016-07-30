# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import views, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from registration.backends.hmac import urls


def logout(request, *args, **kwargs):
    messages.success(request, 'Logout feito com sucesso')
    return views.logout(request, *args, **kwargs)