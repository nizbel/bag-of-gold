# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.investidores import LoginIncorreto
from bagogold.bagogold.utils.investidores import user_blocked
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from registration.forms import RegistrationFormUniqueEmail


class DadosCadastraisForm(LocalizedModelForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username')
        super(DadosCadastraisForm, self).__init__(*args, **kwargs)
        if self.initial['email'] and self.initial['email'] != '':
            self.fields['email'].disabled = True

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email=email).exclude(username=self.username):
            raise forms.ValidationError('Este e-mail já está em uso, por favor insira outro email')
        return email

# Extende a classe de email único do django-registration
class ExtendedUserCreationForm(RegistrationFormUniqueEmail):
    def __init__(self, *args, **kwargs):
        super(ExtendedUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].label = 'E-mail'
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise forms.ValidationError('A senha deve ter no mínimo 8 caracteres')
        return password1

class ExtendedAuthForm(AuthenticationForm):
    error_messages = {
        'invalid_login': (u"Senha inválida para o usuário."),
        'inactive': (u"Esta conta está inativa."),
        'blocked': (u"Esta conta está bloqueada por 10 minutos devido a quantidade de tentativas de "
                     u"login sem sucesso em um curto período de tempo."),
        'user_not_found': (u"Usuário não encontrado.")
    }
    mensagem_bloqueio = ''
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            if User.objects.filter(username=username).exists():
                self.user_cache = authenticate(username=username,
                                               password=password)
                if self.user_cache is None:
                    if user_blocked(User.objects.get(username=username)):
                        raise forms.ValidationError(
                            self.error_messages['blocked'],
                            code='blocked',
                            )
                    else:
                        horario = timezone.now()
                        print 'login failed for: %s at %s' % (username, horario)
                        # Já foram feitos logins anteriores
                        if LoginIncorreto.objects.filter(user__username=username).exists():
                            ultima_tentativa = LoginIncorreto.objects.filter(user__username=username).order_by('-horario')[0]
                            # Verifica se última tentativa foi feita a menos de 10 minutos
                            if (horario - ultima_tentativa.horario).total_seconds() < 10 * 60:
                                LoginIncorreto.objects.create(user=User.objects.get(username=username), horario=horario)
                                qtd_tentativas = LoginIncorreto.objects.filter(user__username=username).count()
                                if qtd_tentativas >= 6:
                                    send_mail(
                                        'Conta bloqueada no Bag of Gold',
                                        'Devido a quantidade de tentativas de login sem sucesso em um curto espaço de tempo, sua conta no Bag of Gold acaba de ser bloqueada pelo período de 10 minutos.',
                                        'do-not-reṕly@bagofgold.com.br',
                                        [User.objects.get(username=username).email],
                                        fail_silently=False,
                                    )
                                    raise forms.ValidationError(
                                        self.error_messages['blocked'],
                                        code='blocked',
                                        )
                                elif qtd_tentativas > 2:
                                    self.mensagem_bloqueio = u' Você possui mais %s tentativa(s) de login antes da conta ser bloqueada por 10 minutos.' % (6 - qtd_tentativas)
                            else:
                                LoginIncorreto.objects.filter(user__username=username).delete()
                                LoginIncorreto.objects.create(user=User.objects.get(username=username), horario=horario)
                        else:
                            LoginIncorreto.objects.create(user=User.objects.get(username=username), horario=horario)
                        raise forms.ValidationError(
                            self.error_messages['invalid_login'] + (self.mensagem_bloqueio or ''),
                            code='invalid_login',
                            )
                else:
                    self.confirm_login_allowed(self.user_cache)
                    self.confirm_user_not_blocked(self.user_cache)
            else:
                raise forms.ValidationError(
                    self.error_messages['user_not_found'],
                    code='user_not_found'
                )

        return self.cleaned_data
    
    def confirm_user_not_blocked(self, user):
        """ Verifica se usuário não está bloqueado """
        if user_blocked(user):
            raise forms.ValidationError(
                self.error_messages['blocked'],
                code='blocked',
            )
        LoginIncorreto.objects.filter(user=user).delete()
