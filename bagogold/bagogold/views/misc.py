# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect

@login_required
def teste_nova_aparencia(request, url):
    if 'testando_aparencia' in request.session:
        request.session['testando_aparencia'] = not request.session['testando_aparencia']
    else:
        request.session['testando_aparencia'] = True
    return HttpResponseRedirect('/' + url + '/')
    