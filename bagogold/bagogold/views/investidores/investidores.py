# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import views, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext


def cadastrar(request):
    if request.method == 'POST':
        form_usuario = UserCreationForm(request.POST)
        if form_usuario.is_valid():
            form_usuario.save()
            messages.success(request, 'Conta criada com sucesso')
            novo_usuario = authenticate(username=form_usuario.cleaned_data['username'], \
                                    password=form_usuario.cleaned_data['password1'],)
            login(request, novo_usuario)
            return redirect('home')
    else:
        form_usuario = UserCreationForm()
            
    return render_to_response('investidores/cadastrar.html', {'form_usuario': form_usuario}, context_instance=RequestContext(request))

def logout(request, *args, **kwargs):
    messages.success(request, 'Logout feito com sucesso')
    return views.logout(request, *args, **kwargs)