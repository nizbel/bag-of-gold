# -*- coding: utf-8 -*-
import datetime

from bagogold.bagogold.utils.investidores import atualizar_checkpoints


class UltimoAcessoMiddleWare(object): 
    """Middleware para guardar último acesso a uma página do site"""
     
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_anonymous():
            if (not request.user.investidor.data_ultimo_acesso) or request.user.investidor.data_ultimo_acesso != datetime.date.today():
                # Se último acesso foi em ano anterior ou estamos nos primeiros 5 dias do ano, atualizar checkpoints
                if (request.user.investidor.data_ultimo_acesso and request.user.investidor.data_ultimo_acesso.year < datetime.date.today().year):
                    atualizar_checkpoints(request.user.investidor, request.user.investidor.data_ultimo_acesso.year)
                  
                request.user.investidor.data_ultimo_acesso = datetime.date.today()
                request.user.investidor.save()
                
        return None
    