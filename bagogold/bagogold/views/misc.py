# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseRedirect
import subprocess32 as subprocess
import sys
import time


@login_required
def ver_nova_aparencia(request, url):
    # Apenas eu e Camila podemos acessar
    if request.user.id not in [1,31]:
        raise PermissionDenied
    
    if 'testando_aparencia' in request.session:
        request.session['testando_aparencia'] = not request.session['testando_aparencia']
    else:
        request.session['testando_aparencia'] = True
    return HttpResponseRedirect('/' + url + '/')
    
@login_required
def carregar_nova_aparencia(request, url):
    # Apenas eu e Camila podemos acessar
    if request.user.id not in [1,31]:
        raise PermissionDenied

    subprocess.call('cp -ar /home/bagofgold/Dropbox/HTML\ Bag\ of\ Gold/Teste\ in\ Progress/pages/* /home/bagofgold/bagogold/bagogold/templates/teste', shell=True)
    subprocess.call('cp -ar /home/bagofgold/Dropbox/HTML\ Bag\ of\ Gold/Teste\ in\ Progress/assets /home/bagofgold/bagogold/bagogold/static/', shell=True)
    subprocess.call(['/home/bagofgold/.virtualenvs/bagogold/bin/python', '/home/bagofgold/bagogold/manage.py', 'collectstatic', '--noinput'])

    messages.success(request, 'Arquivos carregados com sucesso')
    return HttpResponseRedirect('/' + url + '/')