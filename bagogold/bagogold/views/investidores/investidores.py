# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.investidor import DadosCadastraisForm
from django.contrib import messages
from django.contrib.auth import login, views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.http.response import HttpResponseRedirect
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
def editar_dados_cadastrais(request, id):
    if int(id) != int(request.user.id):
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.POST.get("save"):
            form_dados_cadastrais = DadosCadastraisForm(request.POST, instance=request.user, username=request.user.username)
            if form_dados_cadastrais.is_valid():
                form_dados_cadastrais.save()
                messages.success(request, 'Dados cadastrais alterados com sucesso')
                return HttpResponseRedirect(reverse('configuracoes_conta_investidor', kwargs={'id': id}))
    
    else:
        form_dados_cadastrais = DadosCadastraisForm(instance=request.user, username=request.user.username)
    
    return render_to_response('investidores/editar_dados_cadastrais.html', {'form_dados_cadastrais': form_dados_cadastrais}, context_instance=RequestContext(request))