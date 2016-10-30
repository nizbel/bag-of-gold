# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseRedirect
from fabric.context_managers import settings
from fabfile import metronic_test_update

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

    with settings(host_string='bagofgold@bagofgold.com.br'):
        metronic_test_update()
        
    return HttpResponseRedirect('/' + url + '/')