# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.investidor import DadosCadastraisForm
from django.contrib import messages
from django.contrib.auth import login, views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
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
@adiciona_titulo_descricao('Minha conta', 'Dados da conta do investidor')
def minha_conta(request, user_id):
    investidor = request.user.investidor
    if int(user_id) != int(request.user.id):
        raise PermissionDenied
    
    return TemplateResponse(request, 'investidores/minha_conta.html', {})


# @login_required
# def editar_dados_cadastrais(request, id):
#     if int(id) != int(request.user.id):
#         raise PermissionDenied
#     
#     if request.method == 'POST':
#         if request.POST.get("save"):
#             form_dados_cadastrais = DadosCadastraisForm(request.POST, instance=request.user, username=request.user.username)
#             if form_dados_cadastrais.is_valid():
#                 form_dados_cadastrais.save()
#                 messages.success(request, 'Dados cadastrais alterados com sucesso')
#                 return HttpResponseRedirect(reverse('configuracoes_conta_investidor', kwargs={'id': id}))
#     
#     else:
#         form_dados_cadastrais = DadosCadastraisForm(instance=request.user, username=request.user.username)
#     
#     return TemplateResponse(request, 'investidores/editar_dados_cadastrais.html', {'form_dados_cadastrais': form_dados_cadastrais})