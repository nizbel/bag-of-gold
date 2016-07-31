# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import views, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from registration.backends.hmac import urls
from django.dispatch import receiver
from registration.signals import user_activated


def logout(request, *args, **kwargs):
    messages.success(request, 'Logout feito com sucesso')
    return views.logout(request, *args, **kwargs)


# Sinal para logar após ativação
@receiver(user_activated)
def login_on_activation(sender, user, request, **kwargs):
    """Loga o usuário após ativação"""
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)