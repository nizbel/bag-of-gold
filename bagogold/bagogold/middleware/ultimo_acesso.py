# -*- coding: utf-8 -*-
from django.template.exceptions import TemplateDoesNotExist
import datetime


class UltimoAcessoMiddleWare(object): 
     
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_anonymous():
            if (not request.user.investidor.data_ultimo_acesso) or request.user.investidor.data_ultimo_acesso.day != datetime.date.today().day:
                request.user.investidor.data_ultimo_acesso = datetime.date.today()
                request.user.investidor.save()
        return None
        