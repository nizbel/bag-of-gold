# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
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


@login_required    
def configuracoes_conta_investidor(request, id):
    investidor = request.user.investidor
    if int(id) != int(request.user.id):
        raise PermissionDenied
    
    return render_to_response('investidores/configuracoes_conta.html', {}, context_instance=RequestContext(request))


@login_required
def alterar_dados_cadastrais(request, id):
    investidor = request.user.investidor
    if int(id) != int(request.user.id):
        raise PermissionDenied
    
    